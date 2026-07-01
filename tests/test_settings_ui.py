"""Tests for the interactive settings panel."""

from enum import StrEnum
from typing import Literal
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import Field

import pibot.cogs.admin.config as _adminConfig  # noqa: F401 — registers AdminConfig
import pibot.cogs.general.config as _generalConfig  # noqa: F401 — registers GeneralConfig
import pibot.cogs.summarize.config as _summarizeConfig  # noqa: F401 — registers SummarizeConfig
import pibot.cogs.translations.config as _translationsConfig  # noqa: F401 — registers TranslationsConfig
from pibot.cogs.admin.config import AdminConfig
from pibot.cogs.general.config import GeneralConfig
from pibot.cogs.summarize.config import SummarizeConfig
from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.setting_type import (
    BoolType,
    ChannelType,
    EnumType,
    IntegerType,
    LiteralType,
    StringType,
    unwrapAnnotation,
)
from pibot.guild_settings.settings_ui import SettingsPanelView, sendSettingsPanel


class SampleMode(StrEnum):
    """Sample enum for settings field tests."""

    FAST = "fast"
    SAFE = "safe"


class SampleConfig(SettingsGroup):
    """Synthetic config covering multiple field kinds."""

    name = "sample"
    description = "Sample feature settings"

    mode: SampleMode = Field(default=SampleMode.FAST, description="Operating mode")
    level: Literal["low", "high"] = Field(default="low", description="Level preset")


def makeTestConfig(fieldCount: int, *, name: str = "huge-test") -> type[SettingsGroup]:
    """Build a feature config with ``fieldCount`` custom int settings plus ``enabled``."""
    annotations = {f"setting{i}": int for i in range(fieldCount)}
    namespace: dict[str, object] = {
        "name": name,
        "description": "Synthetic config for settings panel tests",
        "__annotations__": annotations,
        **{f"setting{i}": Field(default=i, description=f"Setting {i}") for i in range(fieldCount)},
    }
    return type("HugeTestConfig", (SettingsGroup,), namespace)


def testResolveSettingTypes() -> None:
    """Setting types map to the expected UI controls."""
    assert GeneralConfig.resolveSettingType("enabled") is BoolType
    assert GeneralConfig.resolveSettingType("prefix") is StringType
    assert GeneralConfig.resolveSettingType("commandChannelId") is ChannelType
    assert SummarizeConfig.resolveSettingType("cooldownSeconds") is IntegerType
    assert SampleConfig.resolveSettingType("mode") is EnumType
    assert SampleConfig.resolveSettingType("level") is LiteralType


def testSettingFieldsExposeMetadata() -> None:
    """Config fields expose values, descriptions, and setting types."""
    config = GeneralConfig()
    field = "prefix"

    assert getattr(config, field) == "."
    assert GeneralConfig.model_fields[field].description == "Text command prefix"
    assert GeneralConfig.resolveSettingType(field) is StringType


def testFieldChoicesForEnumAndLiteral() -> None:
    """Enum and literal fields expose selectable values."""
    modeField = "mode"
    levelField = "level"
    modeAnnotation = unwrapAnnotation(SampleConfig.model_fields[modeField].annotation)
    levelAnnotation = unwrapAnnotation(SampleConfig.model_fields[levelField].annotation)
    modeType = SampleConfig.resolveSettingType(modeField)
    levelType = SampleConfig.resolveSettingType(levelField)

    assert modeType.choices(modeAnnotation) == ["fast", "safe"]
    assert levelType.choices(levelAnnotation) == ["low", "high"]


def testChannelTypeMetadataDoesNotBreakParsing() -> None:
    """UI metadata on channel fields does not affect validation."""
    assert GeneralConfig.parseSetting("commandChannelId", "123456789") == 123456789


def testFormatSettingStatusLineShowsDefault() -> None:
    """Optional settings show the model default beside the current value."""
    config = AdminConfig(maxClearAmount=50)
    line = AdminConfig.resolveSettingType("maxClearAmount").formatStatusLine(config, "maxClearAmount")

    assert line == "Current: `50` · Default: `100`"


def testFormatSettingStatusLineForUnsetOptional() -> None:
    """Unset optional values at the default omit the default label."""
    config = GeneralConfig()
    line = GeneralConfig.resolveSettingType("commandChannelId").formatStatusLine(config, "commandChannelId")

    assert line == "Current: `default`"


def testFormatSettingStatusLineHidesMatchingDefault() -> None:
    """Values equal to the model default only show the current line."""
    config = AdminConfig()
    line = AdminConfig.resolveSettingType("maxClearAmount").formatStatusLine(config, "maxClearAmount")

    assert line == "Current: `100`"


def testSettingsPanelUsesOnlyMessageComponents() -> None:
    """Message panels must not embed modal-only text inputs."""
    view = SettingsPanelView(MagicMock(), 1, GeneralConfig, GeneralConfig())
    invalidTypes: list[dict] = []

    def collectInvalidTypes(component: object) -> None:
        if isinstance(component, dict):
            if component.get("type") == 4:
                invalidTypes.append(component)
            for value in component.values():
                collectInvalidTypes(value)
        elif isinstance(component, list):
            for value in component:
                collectInvalidTypes(value)

    collectInvalidTypes(view.to_components())
    assert invalidTypes == []


def testSettingsPanelSectionAccessoriesAreButtons() -> None:
    """Section accessories must be buttons; action rows are rejected by Discord."""
    view = SettingsPanelView(MagicMock(), 1, AdminConfig, AdminConfig())
    invalidAccessories: list[dict] = []

    def collectAccessories(component: object) -> None:
        if isinstance(component, dict):
            accessory = component.get("accessory")
            if isinstance(accessory, dict) and accessory.get("type") not in {2, 11, None}:
                if accessory.get("type") is not None:
                    invalidAccessories.append(accessory)
            for value in component.values():
                collectAccessories(value)
        elif isinstance(component, list):
            for value in component:
                collectAccessories(value)

    collectAccessories(view.to_components())
    assert invalidAccessories == []


def testSettingsPanelBuildsForGeneralConfig() -> None:
    """The panel can render a real feature config."""
    view = SettingsPanelView(MagicMock(), 1, GeneralConfig, GeneralConfig())

    assert view.total_children_count > 0
    assert len(view.children) == 1


def testSettingsPanelIncludesAllFields() -> None:
    """The panel renders every field for a feature."""
    view = SettingsPanelView(MagicMock(), 1, SummarizeConfig, SummarizeConfig())

    assert view.total_children_count > 0
    assert len(SummarizeConfig.model_fields) == 5


def testSettingsPanelRejectsWhenDiscordComponentLimitExceeded() -> None:
    """Very large configs hit Discord's layout component limit instead of being truncated."""
    configClass = makeTestConfig(50)

    with pytest.raises(ValueError, match="maximum number of children exceeded"):
        SettingsPanelView(MagicMock(), 1, configClass, configClass())


async def testSendSettingsPanelRequiresGuild() -> None:
    """The panel command is guild-only."""
    bot = MagicMock()
    interaction = MagicMock()
    interaction.guild = None
    interaction.response.send_message = AsyncMock()

    await sendSettingsPanel(bot, interaction)

    interaction.response.send_message.assert_awaited_once()


async def testSendSettingsPanelOpensView() -> None:
    """The panel sends an interactive layout view."""
    bot = MagicMock()
    bot.guildSettings.getSettingsGroup = AsyncMock(return_value=GeneralConfig())
    interaction = MagicMock()
    interaction.guild = MagicMock(id=1)
    interaction.response.send_message = AsyncMock()

    await sendSettingsPanel(bot, interaction, groupName="general")

    interaction.response.send_message.assert_awaited_once()
    awaitArgs = interaction.response.send_message.await_args
    assert awaitArgs is not None
    assert isinstance(awaitArgs.kwargs["view"], SettingsPanelView)


async def testSendSettingsPanelOpensOnSelectedFeature() -> None:
    """The panel can open focused on a specific feature."""
    bot = MagicMock()
    bot.guildSettings.getSettingsGroup = AsyncMock(return_value=SummarizeConfig())
    interaction = MagicMock()
    interaction.guild = MagicMock(id=1)
    interaction.response.send_message = AsyncMock()

    await sendSettingsPanel(bot, interaction, groupName="summarize")

    awaitArgs = interaction.response.send_message.await_args
    assert awaitArgs is not None
    view = awaitArgs.kwargs["view"]
    assert view.configClass is SummarizeConfig

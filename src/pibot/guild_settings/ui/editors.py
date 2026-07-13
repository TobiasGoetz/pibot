"""Discord UI editors for guild settings fields."""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from enum import Enum
from typing import Any, ClassVar, Literal, Union, cast, get_args, get_origin

import discord
from discord import ui
from pydantic.fields import FieldInfo

from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.serializer import fieldDefault, parseSetting


def unwrapAnnotation(annotation: object) -> object:
    """Return the inner type when the annotation is an optional union."""
    origin = get_origin(annotation)
    if origin is Union:
        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return annotation


def partitionFieldMetadata(fieldInfo: FieldInfo) -> tuple[list[type[SettingEditor]], list[object]]:
    """Split field metadata into UI editors and Pydantic validators."""
    uiTypes = [meta for meta in fieldInfo.metadata if isinstance(meta, type) and issubclass(meta, SettingEditor)]
    uiMetadata = set(uiTypes)
    return uiTypes, [meta for meta in fieldInfo.metadata if meta not in uiMetadata]


class SettingEditor(ABC):
    """Base class for per-field Discord settings controls."""

    _editors: ClassVar[list[type[SettingEditor]]] = []

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register concrete editor subclasses."""
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            cls._editors.append(cls)

    @classmethod
    @abstractmethod
    def matches(cls, annotation: object, fieldInfo: FieldInfo) -> bool:
        """Return whether this editor applies to the given annotation."""

    @classmethod
    def formatDisplay(cls, value: object) -> str:
        """Format a stored value for panel display."""
        if value is None:
            return "default"
        return str(value)

    @classmethod
    def formatInput(cls, value: object) -> str:
        """Format a stored value for a modal text input."""
        if value is None:
            return ""
        return str(value)

    @classmethod
    def formatStatusLine(cls, config: SettingsGroup, field: str) -> str:
        """Format current and, when overridden, model-default values for panel display."""
        value = getattr(config, field)
        fieldInfo = type(config).model_fields[field]
        line = f"Current: `{cls.formatDisplay(value)}`"
        if fieldInfo.is_required():
            return line
        defaultValue = fieldDefault(fieldInfo)
        if value != defaultValue:
            line += f" · Default: `{cls.formatDisplay(defaultValue)}`"
        return line

    @classmethod
    def choices(cls, annotation: object) -> list[str]:
        """Return selectable values for choice-based fields."""
        return []

    @classmethod
    @abstractmethod
    def buildControls(
        cls, configClass: type[SettingsGroup], config: SettingsGroup, field: str, header: ui.TextDisplay
    ) -> list[ui.Item]:
        """Build Discord layout components for one setting field."""

    @classmethod
    def parseInteractionValue(
        cls, interaction: discord.Interaction, configClass: type[SettingsGroup], config: SettingsGroup, field: str
    ) -> object:
        """Parse interaction payload into a persisted value."""
        msg = f"{cls.__name__} does not support value parsing."
        raise NotImplementedError(msg)


class BoolEditor(SettingEditor):
    """Boolean toggle setting."""

    @classmethod
    def matches(cls, annotation: object, fieldInfo: FieldInfo) -> bool:
        return annotation is bool

    @classmethod
    def formatDisplay(cls, value: object) -> str:
        if value is None:
            return "default"
        return "on" if value else "off"

    @classmethod
    def buildControls(
        cls, configClass: type[SettingsGroup], config: SettingsGroup, field: str, header: ui.TextDisplay
    ) -> list[ui.Item]:
        value = getattr(config, field)
        button = ui.Button(
            label="Turn off" if value else "Turn on",
            style=discord.ButtonStyle.success if value else discord.ButtonStyle.danger,
            custom_id=f"settings:toggle:{field}",
        )
        return [ui.Section(header, accessory=button)]

    @classmethod
    def parseInteractionValue(
        cls, interaction: discord.Interaction, configClass: type[SettingsGroup], config: SettingsGroup, field: str
    ) -> object:
        return not getattr(config, field)


def bindUiCallback(
    item: ui.Button | ui.Select | ui.ChannelSelect,
    callback: Callable[[discord.Interaction], Coroutine[Any, Any, None]],
) -> None:
    """Assign a callback to a Discord UI item (discord.py stubs expect a bound method)."""
    item.callback = cast(Any, callback)


def defaultResetButton(field: str) -> ui.Button:
    """Build a button that resets one optional field to its model default."""
    button = ui.Button(
        label="Use default",
        style=discord.ButtonStyle.secondary,
        custom_id=f"settings:reset:{field}",
    )

    return button


class ChoiceEditor(SettingEditor):
    """Shared select control for literal and enum settings."""

    @classmethod
    def buildControls(
        cls, configClass: type[SettingsGroup], config: SettingsGroup, field: str, header: ui.TextDisplay
    ) -> list[ui.Item]:
        fieldInfo = configClass.model_fields[field]
        value = getattr(config, field)
        annotation = unwrapAnnotation(fieldInfo.annotation)
        choices = cls.choices(annotation)
        select = ui.Select(
            placeholder=f"Select {field}",
            options=[
                discord.SelectOption(label=choice, value=choice, default=choice == str(value)) for choice in choices
            ],
            custom_id=f"settings:choice:{field}",
        )
        return [header, ui.ActionRow(select)]

    @classmethod
    def parseInteractionValue(
        cls, interaction: discord.Interaction, configClass: type[SettingsGroup], config: SettingsGroup, field: str
    ) -> object:
        rawValue = interaction.data.get("values", [None])[0] if interaction.data else None
        if rawValue is None:
            msg = "No value selected."
            raise ValueError(msg)
        return parseSetting(configClass, field, rawValue)


class LiteralEditor(ChoiceEditor):
    """Literal union setting."""

    @classmethod
    def matches(cls, annotation: object, fieldInfo: FieldInfo) -> bool:
        return get_origin(annotation) is Literal

    @classmethod
    def choices(cls, annotation: object) -> list[str]:
        if get_origin(annotation) is Literal:
            return [str(choice) for choice in get_args(annotation)]
        return []


class EnumEditor(ChoiceEditor):
    """Enum setting."""

    @classmethod
    def matches(cls, annotation: object, fieldInfo: FieldInfo) -> bool:
        return isinstance(annotation, type) and issubclass(annotation, Enum)

    @classmethod
    def choices(cls, annotation: object) -> list[str]:
        if isinstance(annotation, type) and issubclass(annotation, Enum):
            return [member.value for member in annotation]
        return []


class ChannelEditor(SettingEditor):
    """Discord channel picker for channel ID settings."""

    @classmethod
    def matches(cls, annotation: object, fieldInfo: FieldInfo) -> bool:
        return False

    @classmethod
    def formatDisplay(cls, value: object) -> str:
        if value is None:
            return "default"
        return f"<#{value}>"

    @classmethod
    def buildControls(
        cls, configClass: type[SettingsGroup], config: SettingsGroup, field: str, header: ui.TextDisplay
    ) -> list[ui.Item]:
        channelSelect = ui.ChannelSelect(
            placeholder="Select a channel",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
            custom_id=f"settings:channel:{field}",
        )
        return [header, ui.ActionRow(channelSelect), ui.ActionRow(defaultResetButton(field))]

    @classmethod
    def parseInteractionValue(
        cls, interaction: discord.Interaction, configClass: type[SettingsGroup], config: SettingsGroup, field: str
    ) -> object:
        values = interaction.data.get("values", []) if interaction.data else []
        if not values:
            msg = "No channel selected."
            raise ValueError(msg)
        return int(values[0])


class TextInputEditor(SettingEditor):
    """Shared modal editor for string and integer settings."""

    @classmethod
    def buildControls(
        cls, configClass: type[SettingsGroup], config: SettingsGroup, field: str, header: ui.TextDisplay
    ) -> list[ui.Item]:
        fieldInfo = configClass.model_fields[field]
        editButton = ui.Button(
            label="Edit",
            style=discord.ButtonStyle.primary,
            custom_id=f"settings:edit:{field}",
        )

        if fieldInfo.is_required():
            return [header, ui.ActionRow(editButton)]

        return [header, ui.ActionRow(editButton, defaultResetButton(field))]


class StringEditor(TextInputEditor):
    """String setting."""

    @classmethod
    def matches(cls, annotation: object, fieldInfo: FieldInfo) -> bool:
        return annotation is str


class IntegerEditor(TextInputEditor):
    """Integer setting."""

    @classmethod
    def matches(cls, annotation: object, fieldInfo: FieldInfo) -> bool:
        return annotation is int


def resolveSettingEditor(configClass: type[SettingsGroup], field: str) -> type[SettingEditor]:
    """Resolve the UI editor for one model field."""
    fieldInfo = configClass.model_fields[field]
    uiTypes, _validation = partitionFieldMetadata(fieldInfo)
    if uiTypes:
        return uiTypes[0]

    annotation = unwrapAnnotation(fieldInfo.annotation)
    for editor in SettingEditor._editors:
        if editor.matches(annotation, fieldInfo):
            return editor

    msg = f"Unsupported settings field type for {configClass.__name__}.{field}: {fieldInfo.annotation!r}"
    raise TypeError(msg)

"""Interactive guild settings panel."""

import logging

import discord
from discord import ui

from pibot.bot import Bot
from pibot.guild_settings.errors import InvalidSettingValue
from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.registry import getSettingsGroups
from pibot.guild_settings.serializer import fieldDefault, parseModalSetting
from pibot.guild_settings.ui.editors import SettingEditor, bindUiCallback, resolveSettingEditor

logger = logging.getLogger("guild_settings.settings_ui")


class SettingValueModal(ui.Modal):
    """Modal editor for one string or integer setting."""

    def __init__(
        self,
        bot: Bot,
        guildId: int,
        configClass: type[SettingsGroup],
        config: SettingsGroup,
        field: str,
        panelMessage: discord.Message,
    ) -> None:
        """Build a single-field modal."""
        fieldInfo = configClass.model_fields[field]
        description = (fieldInfo.description or field)[:100]
        editor = resolveSettingEditor(configClass, field)
        value = getattr(config, field)
        placeholder = None
        if not fieldInfo.is_required():
            placeholder = f"Leave empty for default ({fieldDefault(fieldInfo)})"[:100]

        super().__init__(title=field[:45])
        self.bot = bot
        self.guildId = guildId
        self.configClass = configClass
        self.field = field
        self.panelMessage = panelMessage

        self.textInput = ui.TextInput(
            custom_id=f"settings:modal:{field}",
            default=editor.formatInput(value),
            required=False,
            placeholder=placeholder,
            min_length=0,
        )
        self.add_item(
            ui.Label(
                text=field[:45],
                description=description or None,
                component=self.textInput,
            )
        )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        """Parse, persist, and refresh the settings panel."""
        raw = self.textInput.value.strip()
        try:
            parsed = parseModalSetting(self.configClass, self.field, raw)
        except InvalidSettingValue as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return

        config = await self.bot.guildSettings.update(
            self.guildId,
            self.configClass,
            self.field,
            parsed,
        )
        logger.info(
            "%s set %s.%s for guild %s via modal.",
            interaction.user,
            self.configClass.name,
            self.field,
            interaction.guild.name if interaction.guild else self.guildId,
        )
        view = SettingsPanelView(self.bot, self.guildId, self.configClass, config)
        await interaction.response.defer(ephemeral=True)
        await self.panelMessage.edit(view=view)


class SettingsPanelView(ui.LayoutView):
    """In-chat settings editor for one feature page."""

    def __init__(
        self,
        bot: Bot,
        guildId: int,
        configClass: type[SettingsGroup],
        config: SettingsGroup,
    ) -> None:
        """Build the panel for the given feature."""
        super().__init__(timeout=600)
        self.bot = bot
        self.guildId = guildId
        self.configClass = configClass
        self.config = config
        self.settingsGroups = getSettingsGroups()
        self._build()

    def _build(self) -> None:
        """Add layout components for the current feature."""
        containerItems: list[ui.Item] = [
            ui.TextDisplay(
                f"## {self.configClass.name}\n{self.configClass.description}\nChanges save immediately.",
            ),
            self._featureSelectRow(),
        ]

        for field in self.configClass.model_fields:
            containerItems.extend(self._settingControls(field))

        self.add_item(ui.Container(*containerItems, accent_color=discord.Color.blurple()))

    def _featureSelectRow(self) -> ui.ActionRow:
        """Feature picker across registered cogs."""
        options = [
            discord.SelectOption(
                label=groupName,
                value=groupName,
                description=groupClass.description[:100],
                default=groupName == self.configClass.name,
            )
            for groupName, groupClass in sorted(self.settingsGroups.items())
        ]
        select = ui.Select(
            placeholder="Choose feature",
            options=options,
            custom_id="settings:feature",
        )

        async def callback(interaction: discord.Interaction) -> None:
            groupName = interaction.data.get("values", [None])[0] if interaction.data else None
            if groupName is None or groupName not in self.settingsGroups:
                await interaction.response.send_message("Unknown settings group.", ephemeral=True)
                return
            await self._refreshPanel(interaction, groupName=groupName)

        bindUiCallback(select, callback)
        return ui.ActionRow(select)

    def _settingControls(self, field: str) -> list[ui.Item]:
        """Return layout items for one setting field."""
        fieldInfo = self.configClass.model_fields[field]
        description = fieldInfo.description or field
        editor = resolveSettingEditor(self.configClass, field)
        header = ui.TextDisplay(f"**{field}**\n{description}\n{editor.formatStatusLine(self.config, field)}")
        controls = editor.buildControls(self.configClass, self.config, field, header)
        self._bindSettingCallbacks(field, editor, controls)
        return controls

    def _bindSettingCallbacks(self, field: str, editor: type[SettingEditor], items: list[ui.Item]) -> None:
        """Attach per-field component callbacks owned by this view."""
        for item in items:
            for interactive in self._iterInteractiveItems(item):

                async def callback(
                    interaction: discord.Interaction, fieldName: str = field, editorCls: type[SettingEditor] = editor
                ) -> None:
                    await self._handleEditorInteraction(interaction, fieldName, editorCls)

                bindUiCallback(interactive, callback)

    def _iterInteractiveItems(self, item: ui.Item) -> list[ui.Button | ui.Select | ui.ChannelSelect]:
        """Return interactive controls inside a layout item."""
        controls: list[ui.Button | ui.Select | ui.ChannelSelect] = []
        if isinstance(item, (ui.Button, ui.Select, ui.ChannelSelect)):
            controls.append(item)
            return controls
        if isinstance(item, ui.ActionRow):
            for child in item.children:
                controls.extend(self._iterInteractiveItems(child))
            return controls
        if isinstance(item, ui.Section) and item.accessory is not None:
            controls.extend(self._iterInteractiveItems(item.accessory))
        return controls

    async def _handleEditorInteraction(
        self, interaction: discord.Interaction, field: str, editor: type[SettingEditor]
    ) -> None:
        """Route one component interaction to editor logic and apply the result."""
        customId = interaction.data.get("custom_id") if interaction.data else None
        if customId == f"settings:edit:{field}":
            if interaction.message is None:
                await interaction.response.send_message("Could not open the editor.", ephemeral=True)
                return
            await self.openSettingModal(interaction, field, interaction.message)
            return
        if customId == f"settings:reset:{field}":
            await self.resetSetting(interaction, field)
            return
        try:
            value = editor.parseInteractionValue(interaction, self.configClass, self.config, field)
        except NotImplementedError:
            await interaction.response.send_message("Unsupported interaction.", ephemeral=True)
            return
        except InvalidSettingValue as exc:
            await interaction.response.send_message(str(exc), ephemeral=True)
            return
        await self.persistSetting(interaction, field, value)

    async def persistSetting(self, interaction: discord.Interaction, field: str, value: object) -> None:
        """Persist one setting and refresh the panel."""
        config = await self.bot.guildSettings.update(self.guildId, self.configClass, field, value)
        logger.info(
            "%s set %s.%s for guild %s.",
            interaction.user,
            self.configClass.name,
            field,
            interaction.guild.name if interaction.guild else self.guildId,
        )
        await self._refreshPanel(interaction, config=config)

    async def resetSetting(self, interaction: discord.Interaction, field: str) -> None:
        """Reset one optional setting to its model default."""
        fieldInfo = self.configClass.model_fields[field]
        if fieldInfo.is_required():
            await interaction.response.send_message(f"**{field}** cannot be reset.", ephemeral=True)
            return
        config = await self.bot.guildSettings.reset(self.guildId, self.configClass, field)
        await self._refreshPanel(interaction, config=config)

    async def openSettingModal(
        self,
        interaction: discord.Interaction,
        field: str,
        panelMessage: discord.Message,
    ) -> None:
        """Open the text modal editor for one field."""
        await interaction.response.send_modal(
            SettingValueModal(
                self.bot,
                self.guildId,
                self.configClass,
                self.config,
                field,
                panelMessage,
            ),
        )

    async def _refreshPanel(
        self,
        interaction: discord.Interaction,
        *,
        groupName: str | None = None,
        config: SettingsGroup | None = None,
    ) -> None:
        groupName = groupName or self.configClass.name
        configClass = self.settingsGroups[groupName]
        if config is None or type(config) is not configClass:
            config = await self.bot.guildSettings.load(self.guildId, configClass)
        view = SettingsPanelView(self.bot, self.guildId, configClass, config)

        if interaction.response.is_done():
            await interaction.edit_original_response(view=view)
        else:
            await interaction.response.edit_message(view=view)


async def sendSettingsPanel(
    bot: Bot,
    interaction: discord.Interaction,
    *,
    groupName: str | None = None,
) -> None:
    """Send the interactive settings panel."""
    if interaction.guild is None:
        await interaction.response.send_message(
            "This command can only be used in a server.",
            ephemeral=True,
        )
        return

    settingsGroups = getSettingsGroups()
    if not settingsGroups:
        msg = "No settings groups are registered."
        raise RuntimeError(msg)

    resolvedGroup = groupName or sorted(settingsGroups)[0]
    configClass = settingsGroups[resolvedGroup]
    config = await bot.guildSettings.load(interaction.guild.id, configClass)
    view = SettingsPanelView(bot, interaction.guild.id, configClass, config)
    await interaction.response.send_message(view=view, ephemeral=True)

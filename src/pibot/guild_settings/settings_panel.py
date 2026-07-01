"""Panel protocol for guild settings UI controls."""

from __future__ import annotations

from typing import Protocol

import discord

from pibot.guild_settings.model import SettingsGroup


class SettingsPanel(Protocol):
    """Panel view API used when building per-field Discord controls."""

    configClass: type[SettingsGroup]
    config: SettingsGroup

    async def persistSetting(self, interaction: discord.Interaction, field: str, value: object) -> None:
        """Persist one setting and refresh the panel."""

    async def resetSetting(self, interaction: discord.Interaction, field: str) -> None:
        """Reset one optional setting to its model default."""

    async def openSettingModal(
        self,
        interaction: discord.Interaction,
        field: str,
        panelMessage: discord.Message,
    ) -> None:
        """Open the text modal editor for one field."""

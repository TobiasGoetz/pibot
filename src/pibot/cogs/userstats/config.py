"""Userstats feature settings."""

from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.registry import registerSettingsGroup


@registerSettingsGroup
class UserstatsConfig(SettingsGroup):
    """Userstats feature settings."""

    name = "userstats"
    description = "Track member message activity and stats"

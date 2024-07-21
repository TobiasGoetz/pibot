"""
Custom errors for the bot.
"""

import discord


class UserNotConnectedToVoice(discord.app_commands.AppCommandError):
    """Raised when a user is not connected to a voice channel."""


class BotNotConnectedToVoice(discord.app_commands.AppCommandError):
    """Raised when the bot is not connected to a voice channel."""


class BotNotPlayingAudio(discord.app_commands.AppCommandError):
    """Raised when the bot is not playing anything."""

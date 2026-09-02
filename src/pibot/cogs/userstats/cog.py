"""Userstats cog for PiBot."""

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.cogs.userstats.config import UserstatsConfig
from pibot.cogs.userstats.model import UserStatsRecord
from pibot.cogs.userstats.store import UserstatsStore
from pibot.guild_settings.feature_mixin import FeatureSettingsMixin


class Userstats(
    FeatureSettingsMixin,
    commands.GroupCog,
    group_name="userstats",
    group_description="Member activity stats",
):
    """Member activity stats commands."""

    settingsGroup = UserstatsConfig

    def __init__(self, bot: Bot) -> None:
        """Initialize the cog."""
        self.bot = bot
        self.store = UserstatsStore(bot._mongoClient)

    @staticmethod
    def _buildStatsEmbed(member: discord.Member, record: UserStatsRecord) -> discord.Embed:
        """Build an embed for one member's activity stats."""
        embed = discord.Embed(
            title="Activity stats",
            description=member.mention,
            color=discord.Color.blurple(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Messages", value=f"{record.messageCount:,}", inline=False)
        if member.joined_at is not None:
            timestamp = int(member.joined_at.timestamp())
            embed.add_field(name="Joined server", value=f"<t:{timestamp}:D>", inline=False)
        if record.lastMessageAt is not None:
            timestamp = int(record.lastMessageAt.timestamp())
            embed.add_field(name="Last message", value=f"<t:{timestamp}:R>", inline=False)
        return embed

    async def _showStats(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """Send activity stats for one member."""
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return

        record = await self.store.getStats(interaction.guild.id, member.id)
        if record is None:
            await interaction.response.send_message("No activity tracked yet.", ephemeral=True)
            return

        embed = self._buildStatsEmbed(member, record)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="me", description="View your activity stats")
    async def me(self, interaction: discord.Interaction) -> None:
        """
        View your activity stats.

        :param interaction: The interaction of the slash command.
        """
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True,
            )
            return
        await self._showStats(interaction, interaction.user)

    @app_commands.default_permissions(administrator=True)
    @app_commands.command(name="user", description="View a member's activity stats")
    async def user(self, interaction: discord.Interaction, member: discord.Member) -> None:
        """
        View a member's activity stats.

        :param interaction: The interaction of the slash command.
        :param member: The member whose stats to view.
        """
        await self._showStats(interaction, member)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        """
        Record member message activity.

        :param message: The message that was sent.
        """
        if message.guild is None or message.author.bot:
            return

        config = await self.bot.guildSettings.load(message.guild.id, UserstatsConfig)
        if config.enabled:
            await self.store.recordMessage(message)

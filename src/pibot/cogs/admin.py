"""Admin cog."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot

logger = logging.getLogger("cog.admin")


@app_commands.default_permissions(administrator=True)
class Admin(commands.GroupCog):
    """Admin commands."""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot

    @app_commands.command(name="clear", description="Clear a specified amount of messages.")
    async def clear(self, interaction: discord.Interaction, amount: int = 1) -> None:
        """
        Clear a specified amount of messages.

        :param interaction: The interaction of the slash command.
        :param amount: The amount of messages to clear.
        """
        await interaction.response.defer()
        if isinstance(interaction.channel, discord.TextChannel):
            await interaction.channel.purge(limit=amount + 1)
        logging.info(
            "User %s cleared %s messages in %s.",
            interaction.user,
            amount,
            interaction.channel,
        )

    @app_commands.command(name="mute", description="Mute a member.")
    async def mute(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        *,
        reason: str | None = None,
    ) -> None:
        """
        Mute a member.

        :param interaction: The interaction of the slash command.
        :param member: The member to mute.
        :param reason: The reason for the mute.
        """
        if interaction.guild is None:
            return
        guild = interaction.guild
        await interaction.response.defer()
        role = discord.utils.get(guild.roles, name="Muted")

        if role is None:
            logger.info("Muted role not found, creating one.")
            await guild.create_role(name="Muted")
            role = discord.utils.get(guild.roles, name="Muted")

        if role is not None:
            for channel in guild.channels:
                await channel.set_permissions(role, speak=False, send_messages=False)
            logger.info("Muted role created.")
            await member.add_roles(role)

        if role is None:
            await interaction.followup.send("Could not find or create the Muted role.")
        elif reason is None:
            await interaction.followup.send(f"{member.mention} has been muted.")
        else:
            await interaction.followup.send(f"{member.mention} has been muted for {reason}")
        logging.info("User %s muted %s for %s.", interaction.user, member, reason)

    @app_commands.command(name="unmute", description="Unmute a member.")
    async def unmute(self, interaction: discord.Interaction, member: discord.Member):
        """
        Unmute a member.

        :param interaction: The interaction of the slash command.
        :param member: The member to unmute.
        """
        if interaction.guild is None:
            return
        guild = interaction.guild
        await interaction.response.defer()
        role = discord.utils.get(guild.roles, name="Muted")
        if role is not None:
            await member.remove_roles(role)
        await interaction.followup.send(f"{member.mention} has been unmuted.")
        logging.info("User %s unmuted %s.", interaction.user, member)


async def setup(bot: Bot) -> None:
    """Set up the cog."""
    await bot.add_cog(Admin(bot))

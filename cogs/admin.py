"""
Admin cog
"""
import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot import db_check_if_guild_exists_else_initialize, set_setting

logger = logging.getLogger('discord.admin')


class Admin(commands.Cog):
    """
    Admin commands
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, arg):
        """
        Set the prefix for the guild.
        :param ctx: The context of the command.
        :param arg: The prefix to set.
        """
        await db_check_if_guild_exists_else_initialize(ctx.guild)
        await set_setting(ctx.guild, "prefix", arg)
        logger.info("Changed prefix for %s to %s.", ctx.guild.name, arg)
        await ctx.send(f"Prefix set to {arg}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def command_channel(self, ctx, arg):
        """
        Set the command channel for the guild.
        :param ctx: The context of the command.
        :param arg: The channel to set.
        """
        await db_check_if_guild_exists_else_initialize(ctx.guild)

        # Get the channel id by the name provided as arg
        channel = discord.utils.get(ctx.guild.channels, name=arg, type=discord.ChannelType.text)
        if channel is None:
            return await ctx.send(f"Channel {arg} not found.")

        await set_setting(ctx.guild, "command_channel", channel.id)
        await ctx.send(f"Command channel set to {channel.mention}")

    @app_commands.command(name="clear", description="Clear a specified amount of messages.")
    @commands.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, amount: int = 1) -> None:
        """
        Clear a specified amount of messages.
        :param interaction: The interaction of the slash command.
        :param amount: The amount of messages to clear.
        """
        await interaction.response.defer()
        await interaction.channel.purge(limit=amount + 1)
        logging.info('User %s cleared %s messages in %s.', interaction.user, amount, interaction.channel)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def mute(self, ctx, member: discord.Member, *, reason=None):
        """
        Mute a member.
        :param ctx: The context of the command.
        :param member: The member to mute.
        :param reason: The reason for the mute.
        """
        role = discord.utils.get(ctx.guild.roles, name='Muted')

        if role is None:
            logger.info('Muted role not found, creating one.')
            await ctx.guild.create_role(name='Muted')
            role = discord.utils.get(ctx.guild.roles, name='Muted')

        for channel in ctx.guild.channels:
            await channel.set_permissions(
                role,
                speak=False,
                send_messages=False
            )
        logger.info('Muted role created.')

        await member.add_roles(role)

        if reason is None:
            await ctx.send(f'{member.mention} has been muted.')
        else:
            await ctx.send(f'{member.mention} has been muted for {reason}')
        logging.info('User %s muted %s for %s.', ctx.author, member, reason)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unmute(self, ctx, member: discord.Member):
        """
        Unmute a member.
        :param ctx: The context of the command.
        :param member: The member to unmute.
        """
        role = discord.utils.get(ctx.guild.roles, name='Muted')
        await member.remove_roles(role)
        await ctx.send(f'{member.mention} has been unmuted.')
        logging.info('User %s unmuted %s.', ctx.author, member)


async def setup(bot):
    """ Setup the cog. """
    await bot.add_cog(Admin(bot))

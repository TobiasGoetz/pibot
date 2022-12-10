"""
Admin cog
"""
import logging

import discord
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
    async def clear(self, ctx, amount=1):
        """
        Clear a specified amount of messages.
        :param ctx: The context of the command.
        :param amount: The amount of messages to clear.
        """
        await ctx.message.delete()
        await ctx.channel.purge(limit=amount)
        logging.info('User %s cleared %s messages in %s.', ctx.author, amount, ctx.channel)

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

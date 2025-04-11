"""Development tools cog."""

import os
import discord
from discord.ext import commands

from pibot.pibot import PiBot


class DevTools(commands.Cog):
    """Development tools only available in non-production environments."""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot

    @commands.command(name="getcommands")
    @commands.is_owner()
    async def get_commands(self, ctx):
        """Get all application commands."""
        await ctx.defer()

        embed = discord.Embed(
            title="Commands",
            description="",
        )

        embed.add_field(
            name="Get Global Commands",
            value=f"{self.bot.tree.get_commands()}",
            inline=False,
        )
        embed.add_field(
            name="Get Guild Commands",
            value=f"{self.bot.tree.get_commands(guild=ctx.guild)}",
            inline=False,
        )
        embed.add_field(
            name="Fetch Global Commands",
            value=f"{await self.bot.tree.fetch_commands()}",
            inline=False,
        )
        embed.add_field(
            name="Fetch Guild Commands",
            value=f"{await self.bot.tree.fetch_commands(guild=ctx.guild)}",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """Sync all application commands for the guild."""
        await ctx.defer()

        self.bot.tree.copy_global_to(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)

        await ctx.send(
            embed=discord.Embed(
                title="Sync Complete",
                description="Synced commands.",
            )
        )

    @commands.command(name="clear")
    @commands.is_owner()
    async def clear_commands(self, ctx):
        """Remove all application commands for the guild."""
        await ctx.defer()

        self.bot.tree.clear_commands(guild=ctx.guild)
        await self.bot.tree.sync(guild=ctx.guild)

        await ctx.send(
            embed=discord.Embed(
                title="Clear Complete",
                description="Cleared commands.",
            )
        )

    @commands.command(name="clearglobal")
    @commands.is_owner()
    async def clear_global_commands(self, ctx):
        """Remove all application commands."""
        await ctx.defer()

        # Save the global commands to a variable
        global_commands = self.bot.tree.get_commands(guild=None)

        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()

        # Restore the global commands
        for command in global_commands:
            self.bot.tree.add_command(command)

        await ctx.send(
            embed=discord.Embed(
                title="Clear Complete",
                description="Cleared commands.",
            )
        )


async def setup(bot: PiBot) -> None:
    """Set up the cog only in non-production environments."""
    if os.getenv("ENVIRONMENT") != "production" and os.getenv("ENVIRONMENT") != "testing":
        await bot.add_cog(DevTools(bot))

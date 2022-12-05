import asyncio
import logging
from datetime import datetime, timezone, timedelta

import discord
import pytimeparse as pytimeparse
from discord.ext import commands

logger = logging.getLogger('discord.general')


class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def countdown(self, ctx, time_str: str):
        seconds = pytimeparse.parse(time_str)

        # Input validation
        if seconds is None:
            raise commands.BadArgument(f"Could not parse {time_str} as a time.")
        if seconds < 0:
            raise commands.BadArgument("Time cannot be negative.")
        if seconds > 86400:
            raise commands.BadArgument("Countdowns cannot be longer than 24 hours.")

        start_time = ctx.message.created_at
        end_time = (start_time + timedelta(seconds=seconds)).strftime("%H:%M:%S")
        logger.info(f"{ctx.author} started a countdown for {seconds} seconds.")
        message = await ctx.send(embed=discord.Embed(
            title=f'Countdown - {seconds}s',
            description=(
                f'{seconds} seconds remaining.\n'
                f'Ends at {end_time} UTC.'
            )
        ))

        while (datetime.now(timezone.utc) - start_time).total_seconds() < seconds:
            await message.edit(embed=discord.Embed(
                title=f'Countdown - {seconds}s',
                description=(
                    f'{seconds - round((datetime.now(timezone.utc) - start_time).total_seconds())} seconds remaining.\n'
                    f'Ends at {end_time} UTC.'
                )
            ))
            await asyncio.sleep(1)

        await message.edit(embed=discord.Embed(
            title=f'Countdown - {seconds}s',
            description=f'Countdown finished at {end_time} UTC.'
        ))
        logger.info(f"Finished {ctx.author}'s countdown for {seconds} seconds.")


async def setup(bot):
    await bot.add_cog(General(bot))

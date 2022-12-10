"""
AI cog
"""

import logging
import os

import openai
from discord.ext import commands

logger = logging.getLogger('discord.ai')

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class AI(commands.Cog):
    """
    AI commands
    """

    def __init__(self, bot):
        self.bot = bot

    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.command()
    async def image(self, ctx, *, query: str):
        """
        Generate an image from a query.
        :param ctx: The context of the command.
        :param query: The query to search for.
        """
        logger.info('User %s searched for %s.', ctx.author, query)
        response = openai.Image.create(
            prompt=query,
            n=1,
            size="256x256",
        )
        image_url = response['data'][0]['url']
        await ctx.send(image_url)


async def setup(bot):
    """ Setup the cog. """
    await bot.add_cog(AI(bot))

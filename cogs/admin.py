import logging

from discord.ext import commands

logger = logging.getLogger('discord.admin')


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def clear(self, ctx, amount=1):
        await ctx.message.delete()
        await ctx.channel.purge(limit=amount)
        logging.info(f'User {ctx.author} cleared {amount} messages in {ctx.channel}')


async def setup(bot):
    await bot.add_cog(Admin(bot))

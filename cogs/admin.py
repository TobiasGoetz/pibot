from discord.ext import commands


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def clear(self, ctx, amount=1):
        await ctx.message.delete()
        await ctx.channel.purge(limit=amount)


async def setup(bot):
    await bot.add_cog(Admin(bot))

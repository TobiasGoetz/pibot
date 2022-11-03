import discord
import wavelink
from discord.ext import commands

from CustomPlayer import CustomPlayer
from StringProgressBar import progressBar


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host='127.0.0.1',
            port=2333,
            password='youshallnotpass',
            identifier='MAIN',
            region='europe',
        )

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f'Node: <{node.identifier}> is ready!')

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: CustomPlayer, track: wavelink.Track, reason):
        if not player.queue.is_empty and reason == 'FINISHED':
            next_track = player.queue.get()
            await player.play(next_track)

    @commands.command(name='connect')
    async def connect_(self, ctx):
        vc = ctx.voice_client
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send('You are not connected to a voice channel.')

        if not vc:
            await ctx.author.voice.channel.connect(cls=CustomPlayer)
        else:
            await ctx.send('I am already connected to a voice channel.')

    @commands.command()
    async def stop(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.disconnect()
        else:
            await ctx.send('I am not connected to a voice channel.')

    @commands.command()
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        vc = ctx.voice_client
        if not vc:
            custom_player = CustomPlayer()
            vc: CustomPlayer = await ctx.author.voice.channel.connect(cls=custom_player)

        await vc.play(search)

        await ctx.send(embed=discord.Embed(
            title=vc.source.title,
            url=vc.source.uri,
            description=f"Playing {vc.source.title} in {vc.channel}"
        ))

    @commands.command()
    async def add(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        vc = ctx.voice_client
        if not vc:
            return await self.play(ctx, search=search)

        vc.queue.put(item=search)

        await ctx.send(embed=discord.Embed(
            title=search.title,
            url=search.uri,
            description=f"Queued {search.title} in {vc.channel}"
        ))

    @commands.command()
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc:
            if not vc.is_playing():
                return await ctx.send("Nothing is playing.")
            if vc.queue.is_empty:
                return await vc.stop()

            await vc.seek(vc.track.length * 1000)
            if vc.is_paused():
                await vc.resume()
        else:
            await ctx.send("The bot is not connected to a voice channel.")

    @commands.command()
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc:
            if vc.is_playing() and not vc.is_paused():
                await vc.pause()
            elif vc.is_paused():
                await vc.resume()
            else:
                await ctx.send("Nothing is playing.")
        else:
            await ctx.send("The bot is not connected to a voice channel")

    @commands.command()
    async def queue(self, ctx):
        vc = ctx.voice_client
        if vc:
            if not vc.queue.is_empty:
                await ctx.send(embed=discord.Embed(
                    title='Queue',
                    description='\n'.join([track.title for track in vc.queue])
                ))
            else:
                await ctx.send('The queue is empty.')
        else:
            await ctx.send("The bot is not connected to a voice channel")

    @commands.command()
    async def now(self, ctx):
        vc = ctx.voice_client
        if vc:
            if vc.is_playing():
                await ctx.send(embed=discord.Embed(
                    title='Now Playing',
                    description=f'{vc.source.title}\n{progressBar.splitBar(total=round(vc.source.length), current=round(vc.position), size=20)[0]} [{round(vc.position / vc.source.length * 100)}%]\n'
                ))
            else:
                await ctx.send('Nothing is playing.')
        else:
            await ctx.send("The bot is not connected to a voice channel")



    @play.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Could not find a track.")
        else:
            await ctx.send("Please join a voice channel.")


async def setup(bot):
    await bot.add_cog(Music(bot))

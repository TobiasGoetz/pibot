import logging
import os

import discord
import wavelink
from StringProgressBar import progressBar
from discord.ext import commands

from CustomPlayer import CustomPlayer
from bot import set_setting, get_setting

logger = logging.getLogger('discord.music')

ERROR_MESSAGE_BOT_NOT_CONNECTED = "I'm not connected to a voice channel."
ERROR_MESSAGE_USER_NOT_CONNECTED = "You're not connected to a voice channel."
ERROR_MESSAGE_BOT_ALREADY_CONNECTED = "I'm already connected to a voice channel."
ERROR_MESSAGE_NOTHING_PLAYING = "I'm not playing anything."
ERROR_MESSAGE_VOLUME_OUT_OF_RANGE = "Volume must be between 0 and 100."

DEFAULT_VOLUME = 25


class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.connect_nodes())

    async def connect_nodes(self):
        await self.bot.wait_until_ready()
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=os.getenv("LAVALINK_HOST"),
            port=int(os.getenv("LAVALINK_PORT")),
            password=os.getenv("LAVALINK_PASS"),
            identifier='MAIN',
            region='europe',
        )

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        logger.info(f"Node {node.identifier} is ready.")

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: CustomPlayer, track: wavelink.Track, reason):
        logger.info(f"Track {track.title} ended for player {player.guild} with reason {reason}.")
        if not player.queue.is_empty and reason == 'FINISHED':
            next_track = player.queue.get()
            return await player.play(next_track)
        await player.disconnect()
        logger.info(f"Queue is empty, disconnected from {player.guild}.")

    @commands.command(name='connect', help='Connects the bot to your voice channel.')
    @commands.has_role('DJ')
    async def connect_(self, ctx):
        vc = ctx.voice_client
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            return await ctx.send(ERROR_MESSAGE_USER_NOT_CONNECTED)

        if not vc:
            await ctx.author.voice.channel.connect(cls=CustomPlayer)
            logger.info(f'User {ctx.author} connected the bot to {channel}')
        else:
            await ctx.send(ERROR_MESSAGE_BOT_ALREADY_CONNECTED)

    @commands.command(help='Disconnects the bot from your voice channel.')
    @commands.has_role('DJ')
    async def stop(self, ctx):
        vc = ctx.voice_client
        if vc:
            await vc.disconnect()
            logger.info(f'User {ctx.author} disconnected the bot from {vc.channel}')
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Plays a song.')
    @commands.has_role('DJ')
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        logger.info(f'User: {ctx.author} requested: {search}')
        vc = ctx.voice_client
        if not vc:
            custom_player = CustomPlayer()
            vc: CustomPlayer = await ctx.author.voice.channel.connect(cls=custom_player)
            await vc.set_volume(int(await get_setting(ctx.guild, "volume") or DEFAULT_VOLUME))

        await vc.play(search)
        logger.info(f'User: {ctx.author} is now playing: {search}')

        await ctx.send(embed=discord.Embed(
            title=vc.source.title,
            url=vc.source.uri,
            description=f"Playing {vc.source.title} in {vc.channel}"
        ))

    @commands.command(help='Adds a song to the queue.')
    @commands.has_role('DJ')
    async def add(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        vc = ctx.voice_client
        if not vc:
            return await self.play(ctx, search=search)

        vc.queue.put(item=search)
        logger.info(f'User: {ctx.author} added: {search} to the queue.')

        await ctx.send(embed=discord.Embed(
            title=search.title,
            url=search.uri,
            description=f"Queued {search.title} in {vc.channel}"
        ))

    @commands.command(help='Skips the current song.')
    @commands.has_role('DJ')
    async def skip(self, ctx):
        vc = ctx.voice_client
        if vc:
            if not vc.is_playing():
                return await ctx.send(ERROR_MESSAGE_NOTHING_PLAYING)
            if vc.queue.is_empty:
                return await vc.stop()

            await vc.seek(vc.track.length * 1000)
            logger.info(f"User: {ctx.author} skipped: {vc.source.title}")
            if vc.is_paused():
                await vc.resume()
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Pauses the current song.')
    @commands.has_role('DJ')
    async def pause(self, ctx):
        vc = ctx.voice_client
        if vc:
            if vc.is_playing() and not vc.is_paused():
                await vc.pause()
                logger.info(f'User: {ctx.author} paused the song.')
            elif vc.is_paused():
                await vc.resume()
                logger.info(f'User: {ctx.author} resumed the song.')
            else:
                await ctx.send(ERROR_MESSAGE_NOTHING_PLAYING)
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Shows the song queue.')
    async def queue(self, ctx):
        vc = ctx.voice_client
        if vc:
            if vc.queue.is_empty and not vc.is_playing():
                return await ctx.send("The queue is empty.")
            description = f'Currently playing: {vc.source.title} [{round(vc.position)}/{round(vc.source.length)}sec]\n'
            for i, track in enumerate(vc.queue):
                description += f'[{i}] {track.title} [{round(track.length)}sec]\n'

            await ctx.send(embed=discord.Embed(
                title='Queue',
                description='`' + description + '`',
            ))
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Shows the current song.')
    async def now(self, ctx):
        vc = ctx.voice_client
        if vc:
            if vc.is_playing():
                await ctx.send(embed=discord.Embed(
                    title='Now Playing',
                    description=f'{vc.source.title}\n{progressBar.splitBar(total=round(vc.source.length), current=round(vc.position), size=20)[0]} [{round(vc.position)} / {round(vc.source.length)}sec]\n'
                ))
            else:
                await ctx.send(ERROR_MESSAGE_NOTHING_PLAYING)
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Seek to a specific time in the current song.')
    @commands.has_role('DJ')
    async def seek(self, ctx, time: int):
        vc = ctx.voice_client
        if vc:
            if vc.is_playing():
                await vc.seek(time * 1000)
                logger.info(f'User: {ctx.author} seeked to {time} seconds.')
            else:
                await ctx.send(ERROR_MESSAGE_NOTHING_PLAYING)
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Sets the volume.')
    @commands.has_role('DJ')
    async def volume(self, ctx, volume: int):
        vc = ctx.voice_client
        if vc:
            await vc.set_volume(volume)
        await set_setting(ctx.guild, 'volume', volume)
        await ctx.send(embed=discord.Embed(
            title='Volume',
            description=f'Volume set to {volume}.'
        ))
        logger.info(f'User: {ctx.author} set the volume to {volume}.')

    @play.error
    async def play_error(self, ctx, error):
        if isinstance(error, commands.BadArgument):
            await ctx.send("Could not find a track.")
        else:
            await ctx.send("Please join a voice channel.")


async def setup(bot):
    await bot.add_cog(Music(bot))

"""
Music cog
"""
import logging
import os

import discord
import wavelink
from StringProgressBar import progressBar
from discord import app_commands
from discord.ext import commands

from player import Player
from bot import set_setting, get_setting

logger = logging.getLogger('discord.music')

ERROR_MESSAGE_BOT_NOT_CONNECTED = "I'm not connected to a voice channel."
ERROR_MESSAGE_USER_NOT_CONNECTED = "You're not connected to a voice channel."
ERROR_MESSAGE_BOT_ALREADY_CONNECTED = "I'm already connected to a voice channel."
ERROR_MESSAGE_NOTHING_PLAYING = "I'm not playing anything."
ERROR_MESSAGE_VOLUME_OUT_OF_RANGE = "Volume must be between 0 and 100."

DEFAULT_VOLUME = 25


class Music(commands.Cog):
    """
    Music commands for the bot.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        """ Start the nodes for the bot. """
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
        """ Node ready event. """
        logger.info("Node %s is ready.", node.identifier)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, player: Player, track: wavelink.Track, reason):
        """ Track end event. """
        logger.info("Track %s ended for player %s with reason %s.", track.title, player.guild, reason)
        if not player.queue.is_empty and reason == 'FINISHED':
            next_track = player.queue.get()
            return await player.play(next_track)
        await player.disconnect()
        logger.info("Queue is empty, disconnected from %s.", player.guild)

    @staticmethod
    async def connect(interaction: discord.Interaction) -> None:
        """
        Connects the bot to your voice channel.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        try:
            channel = interaction.user.voice.channel
        except AttributeError:
            return await interaction.followup.send(ERROR_MESSAGE_USER_NOT_CONNECTED)

        if not vc:
            await interaction.user.voice.channel.connect(cls=Player)
            logger.info('User %s connected the bot to %s', interaction.user, channel)
        else:
            await interaction.followup.send(ERROR_MESSAGE_BOT_ALREADY_CONNECTED)

    @app_commands.command(name="stop", description='Stops the bot and disconnects it from your voice channel.')
    @app_commands.checks.has_role('DJ')
    async def stop(self, interaction: discord.Interaction):
        """
        Disconnects the bot from your voice channel.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            logger.info('User %s disconnected the bot from %s', interaction.user, vc.channel)
        else:
            await interaction.followup.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)
        # end defer without sending a message
        await interaction.followup.send("Disconnected from voice channel.")

    @commands.command(help='Plays a song.')
    @commands.has_role('DJ')
    async def play(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        """
        Plays a song and connects to the voice channel of the user.
        :param ctx: The context of the command.
        :param search: The search query.
        """
        logger.info('User: %s requested: %s', ctx.author, search)
        vc = ctx.voice_client
        if not vc:
            custom_player = Player()
            vc: Player = await ctx.author.voice.channel.connect(cls=custom_player)
            await vc.set_volume(int(await get_setting(ctx.guild, "volume") or DEFAULT_VOLUME))
            await vc.play(search)

        vc.queue.put_at_front(search)
        await self.skip(ctx)

        logger.info('User: %s is now playing: %s', ctx.author, search)

        await ctx.send(embed=discord.Embed(
            title=vc.source.title,
            url=vc.source.uri,
            description=f"Playing {vc.source.title} in {vc.channel}"
        ))

    @commands.command(help='Adds a song to the queue.')
    @commands.has_role('DJ')
    async def add(self, ctx: commands.Context, *, search: wavelink.YouTubeTrack):
        """
        Adds a song to the queue.
        :param ctx: The context of the command.
        :param search: The search query.
        """
        vc = ctx.voice_client
        if not vc:
            return await self.play(ctx, search=search)

        vc.queue.put(item=search)
        logger.info('User: %s added: %s to the queue.', ctx.author, search)

        await ctx.send(embed=discord.Embed(
            title=search.title,
            url=search.uri,
            description=f"Queued {search.title} in {vc.channel}"
        ))

    @commands.command(help='Skips the current song.')
    @commands.has_role('DJ')
    async def skip(self, ctx):
        """
        Skips the current song.
        :param ctx: The context of the command.
        """
        vc = ctx.voice_client
        if vc:
            if not vc.is_playing():
                return await ctx.send(ERROR_MESSAGE_NOTHING_PLAYING)
            if vc.queue.is_empty:
                return await vc.stop()

            await vc.seek(vc.track.length * 1000)
            logger.info("User: %s skipped: %s", ctx.author, vc.source.title)
            if vc.is_paused():
                await vc.resume()
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Pauses the current song.')
    @commands.has_role('DJ')
    async def pause(self, ctx):
        """
        Pauses the current song.
        :param ctx: The context of the command.
        """
        vc = ctx.voice_client
        if vc:
            if vc.is_playing() and not vc.is_paused():
                await vc.pause()
                logger.info('User: %s paused the song.', ctx.author)
            elif vc.is_paused():
                await vc.resume()
                logger.info('User: %s resumed the song.', ctx.author)
            else:
                await ctx.send(ERROR_MESSAGE_NOTHING_PLAYING)
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Shows the song queue.')
    async def queue(self, ctx):
        """
        Shows the song queue.
        :param ctx: The context of the command.
        """
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
        """
        Shows the current song.
        :param ctx: The context of the command.
        """
        vc = ctx.voice_client
        if vc:
            if vc.is_playing():
                await ctx.send(embed=discord.Embed(
                    title='Now Playing',
                    description=
                    f'{vc.source.title}\n'
                    f'{progressBar.splitBar(total=round(vc.source.length), current=round(vc.position), size=20)[0]}'
                    f'[{round(vc.position)} / {round(vc.source.length)}sec]\n'
                ))
            else:
                await ctx.send(ERROR_MESSAGE_NOTHING_PLAYING)
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Seek to a specific time in the current song.')
    @commands.has_role('DJ')
    async def seek(self, ctx, time: int):
        """
        Seek to a specific time in the current song.
        :param ctx: The context of the command.
        :param time: The time to seek to.
        """
        vc = ctx.voice_client
        if vc:
            if vc.is_playing():
                await vc.seek(time * 1000)
                logger.info('User: %s seeked to %s seconds.', ctx.author, time)
            else:
                await ctx.send(ERROR_MESSAGE_NOTHING_PLAYING)
        else:
            await ctx.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @commands.command(help='Sets the volume.')
    @commands.has_role('DJ')
    async def volume(self, ctx, volume: int):
        """
        Sets the volume.
        :param ctx: The context of the command.
        :param volume: The volume to set.
        """
        vc = ctx.voice_client
        if vc:
            await vc.set_volume(volume)
        await set_setting(ctx.guild, 'volume', volume)
        await ctx.send(embed=discord.Embed(
            title='Volume',
            description=f'Volume set to {volume}.'
        ))
        logger.info('User: %s set the volume to %s.', ctx.author, volume)

    @play.error
    async def play_error(self, ctx, error):
        """ Handles errors for the play command. """
        if isinstance(error, commands.BadArgument):
            await ctx.send("Could not find a track.")
        else:
            await ctx.send("Please join a voice channel.")


async def setup(bot):
    """ Adds the cog to the bot. """
    await bot.add_cog(Music(bot))

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

from bot import get_setting, set_setting
from player import Player

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

    group = app_commands.Group(name="music", description="Music commands for the bot.")

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

    @group.command(name="stop", description='Stops the bot and disconnects it from your voice channel.')
    @app_commands.checks.has_role('DJ')
    async def stop(self, interaction: discord.Interaction):
        """
        Disconnects the bot from your voice channel.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild)
        if player:
            await player.disconnect()
            await interaction.followup.send("Disconnected from voice channel.")
            logger.info('User %s disconnected the bot from %s', interaction.user, player.channel)
        else:
            await interaction.followup.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)

    @group.command(name="play", description='Plays a song and connects to your voice channel.')
    @app_commands.checks.has_role('DJ')
    async def play(self, interaction: discord.Interaction, *, search: str):
        """
        Plays a song and connects to the voice channel of the user.
        :param interaction: The interaction of the slash command.
        :param search: The search query.
        """
        await interaction.response.defer()
        track: wavelink.YouTubeTrack = await wavelink.YouTubeTrack.search(search, return_first=True)

        logger.info('User: %s requested: %s', interaction.user, track)

        await self.play_song(interaction, track)
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild)

        logger.info('User: %s is now playing: %s', interaction.user, track)
        await interaction.followup.send(embed=discord.Embed(
            title=track.title,
            url=track.uri,
            description=f"Playing {track.title} in {player.channel}"
        ))

    async def play_song(self, interaction: discord.Interaction, track: wavelink.YouTubeTrack):
        """
        Plays a song.
        :param interaction: The interaction of the slash command.
        :param track: The track to play.
        """
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild)

        if player is None or not player.is_connected:
            player: Player = await interaction.user.voice.channel.connect(cls=Player)
            await player.set_volume(int(await get_setting(interaction.guild, "volume") or DEFAULT_VOLUME))
            await player.play(track)
            return

        player.queue.put_at_front(track)
        await self.skip_song(player)
        return

    @group.command(name="add", description='Adds a song to the queue.')
    @app_commands.checks.has_role('DJ')
    async def add(self, interaction: discord.Interaction, *, search: str):
        """
        Adds a song to the queue.
        :param interaction: The interaction of the slash command.
        :param search: The search query.
        """
        await interaction.response.defer()
        track: wavelink.YouTubeTrack = await wavelink.YouTubeTrack.search(search, return_first=True)
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild)

        if not player:
            await self.play_song(interaction, track)
        else:
            player.queue.put(item=track)
        logger.info('User: %s added: %s to the queue.', interaction.user, track.title)

        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild)

        await interaction.followup.send(embed=discord.Embed(
            title=track.title,
            url=track.uri,
            description=f"Queued {track.title} in {player.channel}"
        ))

    @group.command(name="skip", description='Skips the current song.')
    @app_commands.checks.has_role('DJ')
    async def skip(self, interaction: discord.Interaction):
        """
        Skips the current song.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()

        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild)
        song = player.source.title

        status: bool = await self.skip_song(player)
        if status is False:
            await interaction.followup.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)
            return
        logger.info("User: %s skipped: %s", interaction.user, song)
        await interaction.followup.send("Skipped song.")

    @staticmethod
    async def skip_song(player: Player) -> bool:
        """
        Skips the current song.
        :param player: The player.
        """
        if player is None:
            return False
        if not player.is_playing():
            return False
        if player.queue.is_empty:
            await player.stop()
            return True

        await player.seek(player.track.length * 1000)
        logger.info("Skipped: %s", player.source.title)
        if player.is_paused():
            await player.resume()
        return True

    @group.command(name="pause", description='Pauses the current song.')
    @app_commands.checks.has_role('DJ')
    async def pause(self, interaction: discord.Interaction):
        """
        Pauses the current song.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild)

        if player is None:
            await interaction.followup.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)
            return

        if player.is_playing() and not player.is_paused():
            await player.pause()
            logger.info('User: %s paused the song.', interaction.user)
            await interaction.followup.send("Paused song.")
        elif player.is_paused():
            await player.resume()
            logger.info('User: %s resumed the song.', interaction.user)
            await interaction.followup.send("Resumed song.")
        else:
            await interaction.followup.send(ERROR_MESSAGE_NOTHING_PLAYING)

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

    @group.command(name="now", description='Shows the current song.')
    async def now(self, interaction: discord.Interaction):
        """
        Shows the current song.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild)

        if player is None:
            await interaction.followup.send(ERROR_MESSAGE_BOT_NOT_CONNECTED)
            return

        if not player.is_playing():
            await interaction.followup.send(ERROR_MESSAGE_NOTHING_PLAYING)
            return

        await interaction.followup.send(embed=discord.Embed(
            title='Now Playing',
            description=
            f'{player.source.title}\n'
            f'{progressBar.splitBar(total=round(player.source.length), current=round(player.position), size=20)[0]}'
            f'[{round(player.position)} / {round(player.source.length)}sec]\n'
        ))

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
    async def play_error(self, interaction: discord.Interaction, error):
        """ Handles errors for the play command. """
        if isinstance(error, commands.BadArgument):
            await interaction.followup.send("Could not find a track.")
        else:
            logger.error(error)
            await interaction.followup.send("Please join a voice channel.")


async def setup(bot):
    """ Adds the cog to the bot. """
    await bot.add_cog(Music(bot))

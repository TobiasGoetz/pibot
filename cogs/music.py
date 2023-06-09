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

import errors
from bot import get_setting, set_setting
from player import Player

logger = logging.getLogger('discord.music')

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
        node: wavelink.Node = wavelink.Node(
            uri=os.getenv("LAVALINK_HOST") + ":" + os.getenv("LAVALINK_PORT"),
            password=os.getenv("LAVALINK_PASS"))
        await wavelink.NodePool.connect(client=self.bot, nodes=[node])

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """ Node ready event. """
        logger.info("Node %s is ready.", node.id)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEventPayload):
        """ Track end event. """
        logger.info("Track %s ended for player %s with reason %s.",
                    payload.track.title, payload.player.guild, payload.reason)
        if not payload.player.queue.is_empty and payload.reason == 'FINISHED':
            next_track = payload.player.queue.get()
            return await payload.player.play(next_track)
        await payload.player.disconnect()
        logger.info("Queue is empty, disconnected from %s.", payload.player.guild)

    @group.command(name="stop", description='Stops the bot and disconnects it from your voice channel.')
    @app_commands.checks.has_role('DJ')
    async def stop(self, interaction: discord.Interaction):
        """
        Disconnects the bot from your voice channel.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if player is None:
            raise errors.BotNotConnectedToVoice

        await player.disconnect()
        logger.info('User %s disconnected the bot from %s', interaction.user, player.channel)
        await interaction.followup.send("Disconnected from voice channel.")

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
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

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
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if interaction.user.voice is None:
            raise errors.UserNotConnectedToVoice

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
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if not player:
            await self.play_song(interaction, track)
        else:
            player.queue.put(item=track)
        logger.info('User: %s added: %s to the queue.', interaction.user, track.title)

        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        await interaction.followup.send(embed=discord.Embed(
            title=track.title,
            url=track.uri,
            description=f"Queued {track.title} in {player.channel}"
        ))

    @group.command(name="add_playlist", description='Adds a playlist to the queue.')
    @app_commands.checks.has_role('DJ')
    async def add_playlist(self, interaction: discord.Interaction, *, search: str):
        """
        Adds a playlist to the queue.
        :param interaction: The interaction of the slash command.
        :param search: The search query, must be a YouTube playlist.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        playlist: wavelink.YouTubePlaylist = await wavelink.YouTubePlaylist.search(search)

        if not player:
            await self.play_song(interaction, playlist.tracks.pop(0))
            player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        for track in playlist.tracks:
            player.queue.put(item=track)

        # log all the songs added and form which playlist
        logger.info('User: %s added: %s from playlist: %s to the queue.', interaction.user, str(playlist.tracks),
                    playlist.name)

        embed: discord.Embed = discord.Embed(
            title=f"Queued playlist: {playlist.name}",
            url=search,
            description="```" +
                        "\n".join(f'[{index}] {track.title}' for index, track in enumerate(playlist.tracks)) +
                        "```"
        )

        await interaction.followup.send(embed=embed)

    @group.command(name="skip", description='Skips the current song.')
    @app_commands.checks.has_role('DJ')
    async def skip(self, interaction: discord.Interaction):
        """
        Skips the current song.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()

        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if player is None:
            raise errors.BotNotConnectedToVoice

        song = player.current

        status: bool = await self.skip_song(player)
        if status is False:
            raise errors.BotNotConnectedToVoice
        logger.info("User: %s skipped: %s", interaction.user, song.title)
        await interaction.followup.send("Skipped song.")

    @staticmethod
    async def skip_song(player: Player) -> bool:
        """
        Skips the current song.
        :param player: The player.
        """
        if player is None:
            raise errors.BotNotConnectedToVoice
        if not player.is_playing():
            raise errors.BotNotPlayingAudio
        if player.queue.is_empty:
            await player.stop()
            return True

        await player.seek(player.current.length * 1000)
        logger.info("Skipped: %s", player.current.title)
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
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if player is None:
            raise errors.BotNotConnectedToVoice

        if player.is_playing() and not player.is_paused():
            await player.pause()
            logger.info('User: %s paused the song.', interaction.user)
            await interaction.followup.send("Paused song.")
        elif player.is_paused():
            await player.resume()
            logger.info('User: %s resumed the song.', interaction.user)
            await interaction.followup.send("Resumed song.")
        else:
            raise errors.BotNotPlayingAudio

    @group.command(name="queue", description='Shows the song queue.')
    async def queue(self, interaction: discord.Interaction):
        """
        Shows the song queue.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if player is None:
            raise errors.BotNotConnectedToVoice

        if player.queue.is_empty and not player.is_playing():
            await interaction.followup.send("The queue is empty.")
            return

        description = (
            f'Currently playing: {player.source.title}'
            f'[{round(player.position)}/{round(player.source.length)}sec]\n'
        )
        for i, track in enumerate(player.queue):
            description += f'[{i}] {track.title} [{round(track.length)}sec]\n'

        await interaction.followup.send(embed=discord.Embed(
            title='Queue',
            description='`' + description + '`',
        ))

    @group.command(name="now", description='Shows the current song.')
    async def now(self, interaction: discord.Interaction):
        """
        Shows the current song.
        :param interaction: The interaction of the slash command.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if player is None:
            raise errors.BotNotConnectedToVoice

        if not player.is_playing():
            raise errors.BotNotPlayingAudio

        await interaction.followup.send(embed=discord.Embed(
            title='Now Playing',
            description=
            f'{player.source.title}\n'
            f'{progressBar.splitBar(total=round(player.source.length), current=round(player.position), size=20)[0]}'
            f'[{round(player.position)} / {round(player.source.length)}sec]\n'
        ))

    @group.command(name="seek", description='Seeks to a specific time in the current song.')
    @app_commands.checks.has_role('DJ')
    async def seek(self, interaction: discord.Interaction, time: int):
        """
        Seek to a specific time in the current song.
        :param interaction: The interaction of the slash command.
        :param time: The time to seek to.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if player is None:
            raise errors.BotNotConnectedToVoice

        if not player.is_playing():
            raise errors.BotNotPlayingAudio

        await player.seek(time * 1000)
        logger.info('User: %s seeked to %s seconds.', interaction.user, time)
        await interaction.followup.send("Seeked to " + str(time) + " seconds.")

    @group.command(name="volume", description='Sets the volume.')
    @app_commands.checks.has_role('DJ')
    async def volume(self, interaction: discord.Interaction, volume: int):
        """
        Sets the volume.
        :param interaction: The interaction of the slash command.
        :param volume: The volume to set.
        """
        await interaction.response.defer()
        player: Player = wavelink.NodePool.get_node().get_player(interaction.guild.id)

        if player:
            await player.set_volume(volume)
        await set_setting(interaction.guild, 'volume', volume)
        logger.info('User: %s set the volume to %s.', interaction.user, volume)
        await interaction.followup.send(embed=discord.Embed(
            title='Volume',
            description=f'Volume set to {volume}.'
        ))

    @play.error
    async def on_error(self, interaction: discord.Interaction, error):
        """ Handles errors for the play command. """
        if isinstance(error, commands.BadArgument):
            await interaction.followup.send("Could not find a track.")


async def setup(bot):
    """ Adds the cog to the bot. """
    await bot.add_cog(Music(bot))

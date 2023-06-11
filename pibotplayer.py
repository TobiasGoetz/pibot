"""
Custom Wavelink Player
"""
import logging

import discord
import wavelink
from StringProgressBar import progressBar

LOGGER: logging.Logger = logging.getLogger('music-player')


class PibotPlayer(wavelink.Player):
    """
    Custom Wavelink Player
    """

    def __int__(self):
        super().__init__()
        self.queue = wavelink.Queue()

    async def get_now_playing_string(self) -> str:
        """
        Gets the currently playing track
        """
        description: str = (
            f'{self.current.title}\n'
            f'{progressBar.splitBar(total=round(self.current.length), current=round(self.position), size=20)[0]}'
            f'[{round(self.position / 1000)} / {round(self.current.length / 1000)}sec]\n')
        return description

    async def get_queue_string(self) -> str:
        """
        Gets the queue
        """
        description: str = (
            f'Currently playing: {self.current.title}'
            f'[{round(self.position / 1000)}/{round(self.current.length / 1000)}sec]\n'
        )
        for i, track in enumerate(self.queue):
            description += f'[{i}] {track.title} [{round(track.length / 1000)}sec]\n'
        return description

    async def get_embed(self) -> discord.Embed:
        """
        Gets the embed
        """
        embed = discord.Embed(
            title='Music Player',
            description='`' + await self.get_queue_string() + '`',
            color=discord.Color.blurple()
        )

        return embed

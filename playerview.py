"""
View for the Player
"""
import asyncio
import logging

import discord

import errors
from pibotplayer import PibotPlayer

LOGGER: logging.Logger = logging.getLogger('music-player-view')


class PlayerView(discord.ui.View):
    """
    Custom View for the Player
    """

    def __init__(self, player: PibotPlayer, interaction: discord.Interaction):
        super().__init__()
        self.player: PibotPlayer = player
        self.interaction: discord.Interaction = interaction

        self.add_item(self.RefreshButton(player=player))
        self.add_item(self.PauseButton(player=player))
        self.add_item(self.SkipButton(player=player))
        self.add_item(self.StopButton(player=player))

    class PauseButton(discord.ui.Button):
        """
        Pause button
        """

        def __init__(self, player: PibotPlayer):
            if player.is_playing and not player.is_paused():
                super().__init__(
                    emoji='⏸️',
                    style=discord.ButtonStyle.blurple)
            else:
                super().__init__(
                    emoji='▶️',
                    style=discord.ButtonStyle.green)
            self.player: PibotPlayer = player

        async def callback(self, interaction: discord.Interaction):
            assert self.view is not None
            if self.player.is_playing and not self.player.is_paused():
                await self.player.pause()
                self.emoji = '▶️'
                self.style = discord.ButtonStyle.green
            elif self.player.is_paused():
                await self.player.resume()
                self.emoji = '⏸️'
                self.style = discord.ButtonStyle.blurple
            await interaction.response.edit_message(view=self.view)

    class SkipButton(discord.ui.Button):
        """
        Skip button
        """

        def __init__(self, player: PibotPlayer):
            super().__init__(
                emoji='⏭️',
                style=discord.ButtonStyle.blurple)
            self.player: PibotPlayer = player

        async def callback(self, interaction: discord.Interaction):
            if self.player is None:
                raise errors.BotNotConnectedToVoice
            if not self.player.is_playing():
                raise errors.BotNotPlayingAudio
            if self.player.queue.is_empty:
                await self.player.stop()
                return True

            await self.player.seek(self.player.current.length * 1000)
            LOGGER.info("Skipped: %s", self.player.current.title)
            if self.player.is_paused():
                await self.player.resume()
            await asyncio.sleep(1)
            await interaction.response.edit_message(embed=await self.player.get_embed(), view=self.view)

    class StopButton(discord.ui.Button):
        """
        Stop button
        """

        def __init__(self, player: PibotPlayer):
            super().__init__(
                emoji='⏹️',
                style=discord.ButtonStyle.blurple)
            self.player: PibotPlayer = player

        async def callback(self, interaction: discord.Interaction):
            if self.player is None:
                raise errors.BotNotConnectedToVoice

            await self.player.disconnect()
            LOGGER.info('User %s disconnected the bot from %s', interaction.user, self.player.channel)
            await interaction.delete_original_response()
            self.view.stop()

    class RefreshButton(discord.ui.Button):
        """
        Refresh button
        """

        def __init__(self, player: PibotPlayer):
            super().__init__(
                emoji='🔄',
                style=discord.ButtonStyle.blurple)
            self.player: PibotPlayer = player

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.edit_message(embed=await self.player.get_embed(), view=self.view)

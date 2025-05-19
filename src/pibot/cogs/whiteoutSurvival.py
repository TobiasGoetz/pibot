import discord
from discord import app_commands, ui
from discord.ext import commands

from WhiteoutSurvival.allianceRepository import AllianceRepository
from WhiteoutSurvival.models.alliance import Alliance
from WhiteoutSurvival.models.player import Player
from WhiteoutSurvival.playerRepository import PlayerRepository
from pibot.pibot import PiBot


class WhiteoutSurvival(commands.GroupCog, group_name="wos", description="Whiteout Survival commands."):
    """Cog for Whiteout Survival."""

    def __init__(self, bot: PiBot) -> None:
        self.bot = bot
        self.playerRepository = PlayerRepository(guild_id="708452533856894977")
        self.allianceRepository = AllianceRepository(guild_id="708452533856894977")

    @app_commands.command(name="save_player", description="Save a player to the database.")
    async def save_player(self, interaction: discord.Interaction, id: int, name: str):
        """Save the player to the database."""
        await interaction.response.defer(thinking=True)
        player = self.playerRepository.save(Player(id=id, name=name))
        await interaction.followup.send(
            embed=discord.Embed(
                title="Player Saved",
                description=f"Player {player.name} saved with ID {player.id}.",
            )
        )

    @app_commands.command(name="get_player", description="Get a player from the database.")
    async def get_player(self, interaction: discord.Interaction, id: int):
        """Get the player from the database."""
        await interaction.response.defer(thinking=True)
        player = self.playerRepository.get(id)
        if player is None:
            return await interaction.followup.send(
                embed=discord.Embed(
                    title="Player Not Found",
                    description=f"Player with ID {id} not found.",
                )
            )
        await interaction.followup.send(
            embed=discord.Embed(
                title="Player Found",
                description=f"Player {player.name} found with ID {player.id}.",
            )
        )
        return None

    @app_commands.command(name="save_alliance", description="Save an alliance to the database.")
    async def save_alliance(self, interaction: discord.Interaction,
                            state: int,
                            tag: str,
                            r5_ids: str,
                            name: str,
                            r4_ids: str,
                            r3_ids: str,
                            r2_ids: str,
                            r1_ids: str):
        """Save the alliance to the database."""
        await interaction.response.defer(thinking=True)

        r5_ids = [int(x) for x in r5_ids.split(",") if x.isdigit()]
        r4_ids = [int(x) for x in r4_ids.split(",") if x.isdigit()]
        r3_ids = [int(x) for x in r3_ids.split(",") if x.isdigit()]
        r2_ids = [int(x) for x in r2_ids.split(",") if x.isdigit()]
        r1_ids = [int(x) for x in r1_ids.split(",") if x.isdigit()]

        alliance = Alliance(
            state=state,
            tag=tag,
            r5_ids=r5_ids,
            r4_ids=r4_ids,
            r3_ids=r3_ids,
            r2_ids=r2_ids,
            r1_ids=r1_ids,
        )
        alliance = self.allianceRepository.save(alliance)
        await interaction.followup.send(
            embed=discord.Embed(
                title="Alliance Saved",
                description=f"Alliance {alliance.tag} saved.",
            )
        )

class CreateAllianceModal(ui.Modal, title="Create Alliance"):
    """Modal to create an alliance."""

    tag = ui.TextInput(label="Tag", placeholder="Enter the alliance tag")
    name = ui.TextInput(label="Name", placeholder="Enter the alliance name")
    state = ui.TextInput(label="State", placeholder="Enter the alliance state")
    r5_ids = ui.TextInput(label="R5 IDs", placeholder="Enter the R5 IDs (comma separated)")
    r4_ids = ui.TextInput(label="R4 IDs", placeholder="Enter the R4 IDs (comma separated)", required=False)
    r3_ids = ui.TextInput(label="R3 IDs", placeholder="Enter the R3 IDs (comma separated)", required=False)
    r2_ids = ui.TextInput(label="R2 IDs", placeholder="Enter the R2 IDs (comma separated)", required=False)
    r1_ids = ui.TextInput(label="R1 IDs", placeholder="Enter the R1 IDs (comma separated)", required=False)

    async def on_submit(self, interaction: discord.Interaction):
        """Handle the submission of the modal."""
        await interaction.response.send_message(f"Alliance created with tag {self.tag.value} and name {self.name.value}.")
        await self.bot.add_cog(WhiteoutSurvival(self.bot))


async def setup(bot: PiBot) -> None:
    """Set up the cog."""
    await bot.add_cog(WhiteoutSurvival(bot))

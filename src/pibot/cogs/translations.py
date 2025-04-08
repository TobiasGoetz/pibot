import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

from TranslationService.deeplTranslator import DeepLTranslator
from TranslationService.translator import Translator
from pibot.pibot import PiBot

logger = logging.getLogger("cog.translations")


class Translations(commands.Cog):
    """Translation commands."""

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
        self.translator: Translator = DeepLTranslator(api_key=os.getenv("DEEPL_API_KEY"))

    @app_commands.command(name="translate", description="Translate a text to a target language.")
    async def translate(self, interaction: discord.Interaction, text: str, target_lang: str):
        """Translate a text to a target language.

        :param interaction: The interaction of the slash command.
        :param text: The text to translate.
        :param target_lang: The target language to translate to.
        """
        await interaction.response.defer()

        logger.info("Translating %s to %s.", text, target_lang)

        # Create an embed with the translation
        embed = discord.Embed(
            title="Translation",
            description=f"**Original:** {text}\n**Translated:** {self.translator.translate(text, target_lang)}",
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Translated to {target_lang}")

        await interaction.followup.send(embed=embed)


async def setup(bot: PiBot) -> None:
    """Set up the cog."""
    await bot.add_cog(Translations(bot))

"""Translations cog for PiBot."""
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

    language_dict: dict[str, str] = {
        "🇦🇪": "AR",  # Arabic
        "🇧🇬": "BG",  # Bulgarian
        "🇨🇿": "CS",  # Czech
        "🇩🇰": "DA",  # Danish
        "🇩🇪": "DE",  # German
        "🇬🇷": "EL",  # Greek
        "🇬🇧": "EN-GB",  # English (British)
        "🇺🇸": "EN-US",  # English (American)
        "🇪🇸": "ES",  # Spanish
        "🇪🇪": "ET",  # Estonian
        "🇫🇮": "FI",  # Finnish
        "🇫🇷": "FR",  # French
        "🇭🇺": "HU",  # Hungarian
        "🇮🇩": "ID",  # Indonesian
        "🇮🇹": "IT",  # Italian
        "🇯🇵": "JA",  # Japanese
        "🇰🇷": "KO",  # Korean
        "🇱🇹": "LT",  # Lithuanian
        "🇱🇻": "LV",  # Latvian
        "🇳🇴": "NB",  # Norwegian Bokmål
        "🇳🇱": "NL",  # Dutch
        "🇵🇱": "PL",  # Polish
        "🇵🇹": "PT-PT",  # Portuguese (Portugal)
        "🇧🇷": "PT-BR",  # Portuguese (Brazil)
        "🇷🇴": "RO",  # Romanian
        "🇷🇺": "RU",  # Russian
        "🇸🇰": "SK",  # Slovak
        "🇸🇮": "SL",  # Slovenian
        "🇸🇪": "SV",  # Swedish
        "🇹🇷": "TR",  # Turkish
        "🇺🇦": "UK",  # Ukrainian
        "🇨🇳": "ZH-HANS",  # Chinese (Simplified)
        "🇹🇼": "ZH-HANT",  # Chinese (Traditional)
    }

    def __init__(self, bot):
        """Initialize the cog."""
        self.bot = bot
        self.translator: Translator = DeepLTranslator(api_key=os.getenv("DEEPL_API_KEY"))

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """
        Handle reaction add events.

        :param payload: The payload of the reaction.
        """
        if not payload.emoji.is_unicode_emoji():
            logger.debug("Reaction is not a unicode emoji.")
            return

        if payload.emoji.name not in self.language_dict:
            logger.debug(f"Reaction {payload.emoji.name} not in supported languages.")
            return

        logger.debug(f"Detected translation request: {payload.emoji.name} {self.language_dict[payload.emoji.name]}")
        await self.send_translation(
            channel_id=payload.channel_id,
            message_author_id=payload.message_author_id,
            message_id=payload.message_id,
            target_lang=self.language_dict[payload.emoji.name],
        )

    async def send_translation(self, channel_id: int, message_author_id: int, message_id: int, target_lang: str):
        """
        Send the translation to the channel.

        :param channel_id: The ID of the channel.
        :param message_author_id: The ID of the message author.
        :param message_id: The ID of the message.
        :param target_lang: The target language to translate to.
        """
        channel = self.bot.get_channel(channel_id)
        if not channel:
            logger.warning(f"Channel {channel_id} not found.")
            return

        message = await channel.fetch_message(message_id)
        if not message:
            logger.warning(f"Message {message_id} not found.")
            return
        author = await self.bot.fetch_user(message_author_id)
        if not author:
            logger.warning(f"Author {message_author_id} not found.")
            return

        await message.reply(
            content=self.translator.translate(message.content, target_lang),
            mention_author=False,
            silent=True
        )

    @app_commands.command(name="get_languages", description="Get the available languages for translation.")
    async def get_languages(self, interaction: discord.Interaction):
        """
        Get the available languages for translation.

        :param interaction: The interaction of the slash command.
        """
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Available languages",
                description="\n".join([f"{emoji} {lang}" for emoji, lang in self.language_dict.items()]),
            )
        )


async def setup(bot: PiBot) -> None:
    """Set up the cog."""
    await bot.add_cog(Translations(bot))


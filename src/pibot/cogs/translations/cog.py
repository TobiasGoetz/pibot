"""Translations cog for PiBot."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from pibot.bot import Bot
from pibot.cogs.translations.config import TranslationsConfig
from pibot.guild_settings.decorators import requiresFeature
from pibot.translation_service.deepl_translator import DeepLTranslator
from pibot.translation_service.translator import Translator

logger = logging.getLogger("cog.translations")


class Translations(commands.Cog):
    """Translation commands."""

    featureName = TranslationsConfig.name

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

    def __init__(self, bot: Bot) -> None:
        """Initialize the cog."""
        self.bot = bot
        self._translatorCache: dict[tuple[int, str], Translator] = {}

    async def _getTranslator(self, guildId: int) -> Translator | None:
        """Return a cached DeepL translator for the guild, if configured."""
        config = await self.bot.guildSettings.resolve(guildId, TranslationsConfig)
        if not config.deeplApiKey:
            return None
        apiKey = config.deeplApiKey.get_secret_value()
        cacheKey = (guildId, apiKey)
        cached = self._translatorCache.get(cacheKey)
        if cached is not None:
            return cached
        translator = DeepLTranslator(api_key=apiKey)
        self._translatorCache[cacheKey] = translator
        return translator

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        """
        Handle reaction add events.

        :param payload: The payload of the reaction.
        """
        if payload.guild_id is None:
            return

        if not TranslationsConfig.resolve(self.bot.guildSettings.getDocument(payload.guild_id)).enabled:
            return

        if not await self.bot.guildSettings.isFeatureAvailable(payload.guild_id, self.featureName):
            return

        if not payload.emoji.is_unicode_emoji():
            logger.debug("Reaction is not a unicode emoji.")
            return

        if payload.emoji.name not in self.language_dict:
            logger.debug("Reaction %s not in supported languages.", payload.emoji.name)
            return

        if payload.message_author_id is None:
            return

        logger.debug(
            "Detected translation request: %s %s",
            payload.emoji.name,
            self.language_dict[payload.emoji.name],
        )
        await self.sendTranslation(
            guild_id=payload.guild_id,
            channel_id=payload.channel_id,
            message_author_id=payload.message_author_id,
            message_id=payload.message_id,
            target_lang=self.language_dict[payload.emoji.name],
            target_lang_emoji=payload.emoji.name,
        )

    async def sendTranslation(
        self,
        guild_id: int,
        channel_id: int,
        message_author_id: int,
        message_id: int,
        target_lang: str,
        target_lang_emoji: str | None = None,
    ) -> None:
        """
        Send the translation to the channel.

        :param guild_id: The guild ID.
        :param channel_id: The ID of the channel.
        :param message_author_id: The ID of the message author.
        :param message_id: The ID of the message.
        :param target_lang: The target language to translate to.
        :param target_lang_emoji: The emoji of the target language.
        """
        translator = await self._getTranslator(guild_id)
        if translator is None:
            logger.debug("No DeepL translator configured for guild %s.", guild_id)
            return

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            logger.warning("Channel %s not found or not messageable.", channel_id)
            return

        message = await channel.fetch_message(message_id)
        if not message:
            logger.warning("Message %s not found.", message_id)
            return
        author = await self.bot.fetch_user(message_author_id)
        if not author:
            logger.warning("Author %s not found.", message_author_id)
            return

        translation: str = translator.translate(message.content, target_lang)

        await message.reply(content=f"{target_lang_emoji}\n{translation}", mention_author=False, silent=True)

    @app_commands.command(name="get_languages", description="Get the available languages for translation.")
    @requiresFeature(TranslationsConfig.name)
    async def getLanguages(self, interaction: discord.Interaction) -> None:
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

"""Summarize cog for PiBot."""

import logging
from datetime import UTC, datetime, timedelta

import discord
import pytimeparse
from discord import app_commands
from discord.ext import commands

from pibot.ai_service import create_ai_service
from pibot.ai_service.ai_service import AIService, ChatMessage
from pibot.bot import Bot

logger = logging.getLogger("cog.summarize")

MAX_DURATION_SECONDS = 7 * 24 * 60 * 60
MAX_MESSAGES = 1000
CHARS_PER_MESSAGE = 100
MAX_INPUT_CHARS = MAX_MESSAGES * CHARS_PER_MESSAGE
DISCORD_MESSAGE_LIMIT = 2000

SUMMARY_SYSTEM_PROMPT = (
    "You summarize Discord channel conversations. "
    "Provide a concise summary covering key topics, decisions, questions, and notable moments. "
    "Use bullet points when helpful. Keep the tone neutral and factual."
)


class Summarize(commands.Cog):
    """Channel summarization commands."""

    def __init__(self, bot: Bot) -> None:
        """Initialize the cog."""
        self.bot = bot
        self.aiService: AIService = create_ai_service()

    @staticmethod
    def _parse_duration(duration: str) -> int:
        seconds = pytimeparse.parse(duration)
        if seconds is None:
            raise commands.BadArgument(f"Could not parse `{duration}` as a duration (e.g. `1h`, `1d`, `10min`).")
        if seconds <= 0:
            raise commands.BadArgument("Duration must be greater than zero.")
        if seconds > MAX_DURATION_SECONDS:
            raise commands.BadArgument("Duration cannot be longer than 7 days.")
        return seconds

    @staticmethod
    async def _fetch_channel_messages(channel: discord.TextChannel, after: datetime) -> list[discord.Message]:
        messages: list[discord.Message] = []
        async for message in channel.history(after=after, oldest_first=True, limit=None):
            if message.author.bot:
                continue
            if not message.content.strip():
                continue
            messages.append(message)
            if len(messages) >= MAX_MESSAGES:
                logger.debug("Reached message cap (%s) in #%s.", MAX_MESSAGES, channel.name)
                break
        return messages

    @staticmethod
    def _format_messages(messages: list[discord.Message]) -> str:
        lines = [
            f"[{message.created_at.strftime('%Y-%m-%d %H:%M')}] {message.author.display_name}: {message.content}"
            for message in messages
        ]
        text = "\n".join(lines)
        if len(text) > MAX_INPUT_CHARS:
            logger.debug("Truncating input from %s to %s characters.", len(text), MAX_INPUT_CHARS)
            text = text[-MAX_INPUT_CHARS:]
            text = f"(truncated to last {MAX_INPUT_CHARS:,} characters)\n{text}"
        return text

    @staticmethod
    def _chunk_text(text: str, limit: int = DISCORD_MESSAGE_LIMIT) -> list[str]:
        if len(text) <= limit:
            return [text]

        chunks: list[str] = []
        while text:
            chunks.append(text[:limit])
            text = text[limit:]
        return chunks

    @app_commands.command(
        name="summarize",
        description="Summarize recent messages in this channel using AI.",
    )
    @app_commands.describe(duration="How far back to look (e.g. 1h, 1d, 10min).")
    async def summarize(self, interaction: discord.Interaction, duration: str) -> None:
        """
        Summarize channel messages for the given duration.

        :param interaction: The interaction of the slash command.
        :param duration: How far back to look.
        """
        if not isinstance(interaction.channel, discord.TextChannel):
            raise commands.BadArgument("This command can only be used in text channels.")

        seconds = self._parse_duration(duration)
        cutoff = datetime.now(UTC) - timedelta(seconds=seconds)

        await interaction.response.defer(thinking=True)

        channel = interaction.channel
        messages = await self._fetch_channel_messages(channel, cutoff)
        if not messages:
            logger.debug(
                "%s requested a summary of #%s but no messages found in the last %s.",
                interaction.user,
                channel.name,
                duration,
            )
            await interaction.followup.send(f"No messages found in the last `{duration}`.")
            return

        formatted = self._format_messages(messages)
        logger.info(
            "%s requested a summary of #%s (%s discord messages, %s seconds, %s formatted chars).",
            interaction.user,
            channel.name,
            len(messages),
            seconds,
            len(formatted),
        )
        logger.debug("Summary input preview: %r", formatted[:500])

        summary = await self.aiService.chat(
            [
                ChatMessage(role="system", content=SUMMARY_SYSTEM_PROMPT),
                ChatMessage(
                    role="user",
                    content=f"Summarize the following Discord channel messages:\n\n{formatted}",
                ),
            ],
        )
        if not summary:
            logger.warning(
                "No summary generated for %s in #%s (%s messages).",
                interaction.user,
                channel.name,
                len(messages),
            )
            await interaction.followup.send("No summary could be generated.")
            return

        embed = discord.Embed(
            title=f"Summary — #{channel.name}",
            description=self._chunk_text(summary)[0],
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=f"Last {duration} · {len(messages)} messages")

        await interaction.followup.send(embed=embed)
        logger.info(
            "Finished %s's summary of #%s (%s characters).",
            interaction.user,
            channel.name,
            len(summary),
        )

        for chunk in self._chunk_text(summary)[1:]:
            await interaction.followup.send(chunk)


async def setup(bot: Bot) -> None:
    """Set up the cog."""
    await bot.add_cog(Summarize(bot))

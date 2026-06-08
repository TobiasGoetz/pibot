"""Abstract base class for AI services."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

ChatRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    """A single chat message for an AI completion request."""

    role: ChatRole
    content: str


class AIService(ABC):
    """Abstract base class for AI chat completion services."""

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Request a chat completion from the AI service.

        :param messages: Conversation messages (system, user, assistant).
        :param model: Model identifier; uses the service default when omitted.
        :param max_tokens: Maximum tokens in the response.
        :return: The assistant's reply text.
        """
        ...

    async def complete(
        self,
        prompt: str,
        *,
        model: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Request a single-turn completion (like Vercel AI SDK ``generateText``).

        :param prompt: The user prompt.
        :param model: Model identifier; uses the service default when omitted.
        :param max_tokens: Maximum tokens in the response.
        :return: The assistant's reply text.
        """
        return await self.chat(
            [ChatMessage(role="user", content=prompt)],
            model=model,
            max_tokens=max_tokens,
        )

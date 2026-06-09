"""Abstract base class for AI gateways."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

from openai.types.chat import ChatCompletionMessageParam

ChatRole = Literal["system", "user", "assistant"]


@dataclass(frozen=True)
class ChatMessage:
    """A single chat message for an AI completion request."""

    role: ChatRole
    content: str

    def getOpenAiMessage(self) -> ChatCompletionMessageParam:
        """Convert to an OpenAI SDK chat completion message."""
        match self.role:
            case "system":
                return {"role": "system", "content": self.content}
            case "assistant":
                return {"role": "assistant", "content": self.content}
            case "user":
                return {"role": "user", "content": self.content}


class AIGateway(ABC):
    """Abstract base class for AI gateway clients."""

    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """
        Request a chat completion from the AI gateway.

        :param messages: Conversation messages (system, user, assistant).
        :param model: Model identifier; uses the gateway default when omitted.
        :param max_tokens: Maximum tokens in the response.
        :return: The assistant's reply text.
        """
        ...

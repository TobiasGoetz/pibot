"""Cloudflare AI Gateway client (unified provider)."""

import logging
import os

import aiohttp

from pibot.ai_service.ai_service import AIService, ChatMessage

logger = logging.getLogger("ai_service.cloudflare")


def unified_model(model: str) -> str:
    """
    Return a unified-provider model id.

    Mirrors ``createUnified()(model)`` from the ``ai-gateway-provider`` SDK.
    """
    return model


def _output_token_fields(model: str, max_tokens: int) -> dict[str, int]:
    """Return the output token field expected by the upstream provider."""
    if model.startswith("openai/gpt-5") or model.startswith("openai/o"):
        return {"max_completion_tokens": max_tokens}
    return {"max_tokens": max_tokens}


class CloudflareAIGateway(AIService):
    """
    AI chat completions via Cloudflare AI Gateway unified API.

    Python equivalent of::

        createAiGateway({ accountId, gateway, apiKey: process.env.CLOUDFLARE_AI_GATEWAY_TOKEN })
        createUnified()(model)
    """

    def __init__(self, account_id: str, gateway: str, token: str, default_model: str) -> None:
        """
        Initialize the Cloudflare AI Gateway client.

        :param account_id: Cloudflare account ID.
        :param gateway: AI Gateway name (e.g. ``pibot``).
        :param token: AI Gateway token (``CLOUDFLARE_AI_GATEWAY_TOKEN``).
        :param default_model: Default unified model id (e.g. ``openai/gpt-4o-mini``).
        """
        self.accountId = account_id
        self.gateway = gateway
        self.token = token
        self.defaultModel = default_model
        self.chatCompletionsUrl = f"https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway}/compat/chat/completions"

    @classmethod
    def from_env(cls) -> CloudflareAIGateway:
        """Create a client from environment variables."""
        accountId = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if not accountId:
            raise ValueError("Set CLOUDFLARE_ACCOUNT_ID to use AI features.")

        gateway = os.getenv("CLOUDFLARE_AI_GATEWAY")
        if not gateway:
            raise ValueError("Set CLOUDFLARE_AI_GATEWAY to use AI features.")

        token = os.getenv("CLOUDFLARE_AI_GATEWAY_TOKEN")
        if not token:
            raise ValueError("Set CLOUDFLARE_AI_GATEWAY_TOKEN to use AI features.")

        defaultModel = os.getenv("CLOUDFLARE_AI_MODEL")
        if not defaultModel:
            raise ValueError("Set CLOUDFLARE_AI_MODEL to use AI features.")

        return cls(account_id=accountId, gateway=gateway, token=token, default_model=defaultModel)

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """Request a chat completion through the unified ``/compat/chat/completions`` endpoint."""
        resolvedModel = unified_model(model or self.defaultModel)
        payload = {
            "model": resolvedModel,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
            **_output_token_fields(resolvedModel, max_tokens),
        }
        headers = {
            "cf-aig-authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }

        totalChars = sum(len(message.content) for message in messages)
        logger.info(
            "AI Gateway request: model=%s max_tokens=%s message_count=%s total_chars=%s",
            resolvedModel,
            max_tokens,
            len(messages),
            totalChars,
        )
        for index, message in enumerate(messages):
            logger.debug(
                "AI Gateway message[%s]: role=%s chars=%s preview=%r",
                index,
                message.role,
                len(message.content),
                message.content[:200],
            )

        async with (
            aiohttp.ClientSession() as session,
            session.post(self.chatCompletionsUrl, json=payload, headers=headers) as response,
        ):
            if response.status >= 400:
                responseBody = await response.text()
                logger.warning(
                    "AI Gateway request failed with status %s. Response: %s",
                    response.status,
                    responseBody,
                )
            response.raise_for_status()
            data = await response.json()

        choices = data.get("choices", [])
        if not choices:
            return ""
        return choices[0].get("message", {}).get("content", "")

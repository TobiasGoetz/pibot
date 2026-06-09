"""Cloudflare AI Gateway client (unified provider)."""

import logging

import aiohttp

from pibot.ai_gateway.gateway import AIGateway, ChatMessage

logger = logging.getLogger("ai_gateway.cloudflare")


class CloudflareAIGateway(AIGateway):
    """
    AI chat completions via Cloudflare AI Gateway unified API.

    Python equivalent of::

        createAiGateway({ accountId, gateway, apiKey: process.env.CLOUDFLARE_AI_GATEWAY_TOKEN })
        createUnified()(model)
    """

    def __init__(
        self,
        account_id: str,
        gateway: str,
        token: str,
        model: str = "openai/gpt-4o-mini",
    ) -> None:
        """
        Initialize the Cloudflare AI Gateway client.

        :param account_id: Cloudflare account ID.
        :param gateway: AI Gateway name (e.g. ``pibot``).
        :param token: AI Gateway token (``CLOUDFLARE_AI_GATEWAY_TOKEN``).
        :param model: Unified model id (e.g. ``openai/gpt-4o-mini``).
        """
        self.accountId = account_id
        self.gateway = gateway
        self.token = token
        self.model = model
        self.chatCompletionsUrl = f"https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway}/compat/chat/completions"

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """Request a chat completion through the unified ``/compat/chat/completions`` endpoint."""
        resolvedModel = model or self.model
        payload = {
            "model": resolvedModel,
            "max_tokens": max_tokens,
            "messages": [{"role": message.role, "content": message.content} for message in messages],
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

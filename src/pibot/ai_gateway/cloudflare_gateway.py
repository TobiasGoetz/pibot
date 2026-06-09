"""Cloudflare AI Gateway client (OpenAI compat)."""

from openai import AsyncOpenAI

from pibot.ai_gateway.gateway import AIGateway, ChatMessage


class CloudflareAIGateway(AIGateway):
    """Cloudflare AI Gateway via the OpenAI-compatible ``/compat`` endpoint."""

    def __init__(self, account_id: str, gateway: str, token: str, model: str = "openai/gpt-4o-mini") -> None:
        """Initialize the gateway client."""
        self.model = model
        self.client = AsyncOpenAI(
            api_key=token,
            base_url=f"https://gateway.ai.cloudflare.com/v1/{account_id}/{gateway}/compat",
        )

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        max_tokens: int = 1024,
    ) -> str:
        """Request a chat completion."""
        response = await self.client.chat.completions.create(
            model=model or self.model,
            max_tokens=max_tokens,
            messages=[message.getOpenAiMessage() for message in messages],
        )
        if not response.choices:
            return ""
        return response.choices[0].message.content or ""

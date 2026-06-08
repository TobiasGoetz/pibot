"""AI service package."""

from pibot.ai_service.ai_service import AIService, ChatMessage
from pibot.ai_service.cloudflare_gateway import CloudflareAIGateway, unified_model


def create_ai_service() -> AIService:
    """Create the configured AI service (Cloudflare AI Gateway)."""
    return CloudflareAIGateway.from_env()

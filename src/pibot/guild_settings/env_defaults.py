"""Global env fallbacks for guild settings."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CloudflareEnvConfig:
    """Cloudflare AI Gateway credentials from the environment."""

    accountId: str
    gateway: str
    token: str
    model: str | None


def deeplApiKey() -> str | None:
    """Return the global DeepL API key from the environment."""
    value = os.getenv("DEEPL_API_KEY", "").strip()
    return value or None


def cloudflareConfig() -> CloudflareEnvConfig | None:
    """Return global Cloudflare AI Gateway config when fully configured."""
    accountId = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    gateway = os.getenv("CLOUDFLARE_AI_GATEWAY", "").strip()
    token = os.getenv("CLOUDFLARE_AI_GATEWAY_TOKEN", "").strip()
    if not all((accountId, gateway, token)):
        return None
    model = os.getenv("CLOUDFLARE_AI_MODEL", "").strip() or None
    return CloudflareEnvConfig(accountId=accountId, gateway=gateway, token=token, model=model)

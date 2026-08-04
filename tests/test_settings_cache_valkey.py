"""Tests for ValkeySettingsCache against a Valkey testcontainer."""

from pibot.cogs.summarize.config import SummarizeConfig
from pibot.guild_settings.cache import ValkeySettingsCache, cacheKey

GUILD_ID = 999001


async def testValkeyCacheGetSetRoundTrip(valkeyClient) -> None:
  """Valkey cache stores and returns a settings group."""
  cache = ValkeySettingsCache(valkeyClient)
  config = SummarizeConfig(enabled=True, maxMessages=42)

  await cache.set(GUILD_ID, config)
  loaded = await cache.get(GUILD_ID, SummarizeConfig)
  raw = await valkeyClient.get(cacheKey(GUILD_ID, SummarizeConfig.name))

  assert loaded == config
  assert raw is not None


async def testValkeyCacheMissReturnsNone(valkeyClient) -> None:
  """Valkey cache returns None when the key is absent."""
  cache = ValkeySettingsCache(valkeyClient)

  assert await cache.get(GUILD_ID, SummarizeConfig) is None

"""Tests for RedisSettingsCache against a Redis testcontainer."""

from pibot.cogs.summarize.config import SummarizeConfig
from pibot.guild_settings.cache import RedisSettingsCache, cacheKey
from pibot.guild_settings.serializer import fromStored

GUILD_ID = 1


async def testRedisCacheGetSetRoundTrip(redisClient) -> None:
    """Redis cache stores and returns a settings group."""
    cache = RedisSettingsCache(redisClient)
    config = fromStored(SummarizeConfig, {"enabled": False, "maxMessages": 42})

    await cache.set(GUILD_ID, config)
    loaded = await cache.get(GUILD_ID, SummarizeConfig)

    assert loaded == config
    raw = await redisClient.get(cacheKey(GUILD_ID, SummarizeConfig.name))
    assert raw is not None


async def testRedisCacheMissReturnsNone(redisClient) -> None:
    """Redis cache returns None when the key is absent."""
    cache = RedisSettingsCache(redisClient)

    assert await cache.get(GUILD_ID, SummarizeConfig) is None

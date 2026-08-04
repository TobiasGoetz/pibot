"""Shared pytest fixtures."""

import pytest
from pymongo import AsyncMongoClient
from redis.asyncio import Redis
from testcontainers.community.redis import RedisContainer
from testcontainers.mongodb import MongoDbContainer

from pibot.guild_settings.cache import RedisSettingsCache
from pibot.guild_settings.service import SettingsService
from pibot.guild_settings.store import SettingsStore


@pytest.fixture(scope="session")
def mongoContainer():
    """MongoDB testcontainer for the test session."""
    with MongoDbContainer("mongo:7.0") as mongo:
        yield mongo


@pytest.fixture(scope="session")
def redisContainer():
    """Redis testcontainer for the test session."""
    with RedisContainer("redis:7") as redis:
        yield redis


@pytest.fixture
async def mongoClient(mongoContainer):
    """Async MongoDB client connected to the testcontainer."""
    client = AsyncMongoClient(mongoContainer.get_connection_url())
    yield client
    await client["discord"]["settings"].delete_many({})
    await client.close()


@pytest.fixture
async def redisClient(redisContainer):
    """Async Redis client connected to the testcontainer."""
    host = redisContainer.get_container_host_ip()
    port = redisContainer.get_exposed_port(redisContainer.port)
    client = Redis.from_url(f"redis://{host}:{port}/0")
    yield client
    await client.flushdb()
    await client.aclose()


@pytest.fixture
async def settingsStore(mongoClient):
    """Yield a settings store backed by real MongoDB."""
    yield SettingsStore(mongoClient)


@pytest.fixture
async def settingsService(settingsStore, redisClient):
    """Yield a settings service with MongoDB and a Redis testcontainer cache."""
    yield SettingsService(settingsStore, RedisSettingsCache(redisClient))

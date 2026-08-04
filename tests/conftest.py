"""Shared pytest fixtures."""

import pytest
from pymongo import AsyncMongoClient
from testcontainers.community.mongodb import MongoDbContainer
from testcontainers.community.valkey import ValkeyContainer
from valkey.asyncio import Valkey

from pibot.guild_settings.cache import ValkeySettingsCache
from pibot.guild_settings.service import SettingsService
from pibot.guild_settings.store import SettingsStore


@pytest.fixture(scope="session")
def mongoContainer():
  """MongoDB testcontainer for the test session."""
  with MongoDbContainer("mongo:7.0") as mongo:
    yield mongo


@pytest.fixture(scope="session")
def valkeyContainer():
  """Valkey testcontainer for the test session."""
  with ValkeyContainer("valkey/valkey:8") as valkey:
    yield valkey


@pytest.fixture
async def mongoClient(mongoContainer):
  """Async MongoDB client connected to the testcontainer."""
  client = AsyncMongoClient(mongoContainer.get_connection_url())
  yield client
  await client["discord"]["settings"].delete_many({})
  await client.close()


@pytest.fixture
async def valkeyClient(valkeyContainer):
  """Async Valkey client connected to the testcontainer."""
  client = Valkey.from_url(valkeyContainer.get_connection_url())
  yield client
  await client.flushdb()
  await client.aclose()


@pytest.fixture
async def settingsStore(mongoClient):
  """Yield a settings store backed by real MongoDB."""
  yield SettingsStore(mongoClient)


@pytest.fixture
async def settingsService(settingsStore, valkeyClient):
  """Yield a settings service with MongoDB and a Valkey testcontainer cache."""
  yield SettingsService(settingsStore, ValkeySettingsCache(valkeyClient))

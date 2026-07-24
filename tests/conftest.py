"""Shared pytest fixtures."""

import pytest
from pymongo import AsyncMongoClient
from testcontainers.mongodb import MongoDbContainer

from pibot.guild_settings.service import SettingsService
from pibot.guild_settings.store import SettingsStore


@pytest.fixture(scope="session")
def mongoContainer():
    """MongoDB testcontainer for the test session."""
    with MongoDbContainer("mongo:7.0") as mongo:
        yield mongo


@pytest.fixture
async def mongoClient(mongoContainer):
    """Async MongoDB client connected to the testcontainer."""
    client = AsyncMongoClient(mongoContainer.get_connection_url())
    yield client
    await client["discord"]["settings"].delete_many({})
    await client.close()


@pytest.fixture
async def settingsStore(mongoClient):
    """Settings store backed by real MongoDB."""
    yield SettingsStore(mongoClient)


@pytest.fixture
async def settingsService(settingsStore):
    """Settings service backed by real MongoDB."""
    yield SettingsService(settingsStore)

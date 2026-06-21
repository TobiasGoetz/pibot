"""Shared pytest fixtures."""

import pytest
from pymongo import AsyncMongoClient
from testcontainers.mongodb import MongoDbContainer

from pibot.guild_settings.service import GuildSettingsService
from pibot.guild_settings.store import SettingsStore


@pytest.fixture(scope="session")
def mongoContainer():
    """MongoDB testcontainer for the test session."""
    with MongoDbContainer("mongo:7.0") as mongo:
        yield mongo


@pytest.fixture
async def guildSettingsService(mongoContainer):
    """Guild settings service backed by real MongoDB."""
    client = AsyncMongoClient(mongoContainer.get_connection_url())
    store = SettingsStore(client)
    try:
        yield GuildSettingsService(store)
    finally:
        await client["discord"]["settings"].delete_many({})
        await client.close()

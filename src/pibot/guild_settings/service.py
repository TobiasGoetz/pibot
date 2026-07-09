"""Guild settings — shared per-guild settings storage."""

from pibot.guild_settings.model import SettingsGroup
from pibot.guild_settings.serializer import fieldDefault
from pibot.guild_settings.store import SettingsStore


class SettingsService:
    """Shared per-guild settings storage."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store

    async def load[T: SettingsGroup](self, guildId: int, model: type[T]) -> T:
        """Load one settings group for a guild."""
        return await self.store.load(guildId, model.name, model)

    async def update[T: SettingsGroup](
        self,
        guildId: int,
        model: type[T],
        field: str,
        value: object,
    ) -> T:
        """Set one field on a settings group and return the updated config."""
        config = await self.load(guildId, model)
        updated = config.model_copy(update={field: value})
        await self.store.save(guildId, model.name, updated)
        return updated

    async def reset[T: SettingsGroup](
        self,
        guildId: int,
        model: type[T],
        field: str,
    ) -> T:
        """Remove one stored field and return the config with model defaults applied."""
        config = await self.load(guildId, model)
        fieldInfo = model.model_fields[field]
        updated = config.model_copy(update={field: fieldDefault(fieldInfo)})
        await self.store.resetField(guildId, model.name, field)
        return updated

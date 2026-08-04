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
        storedValue = getattr(updated, field)
        fieldInfo = model.model_fields[field]

        if fieldInfo.is_required() or storedValue != fieldDefault(fieldInfo):
            await self.store.setField(guildId, model.name, field, storedValue)
        else:
            await self.store.unsetField(guildId, model.name, field)

        return updated

    async def reset[T: SettingsGroup](
        self,
        guildId: int,
        model: type[T],
        field: str,
    ) -> T:
        """Remove one stored field and return the config with model defaults applied."""
        fieldInfo = model.model_fields[field]
        return await self.update(guildId, model, field, fieldDefault(fieldInfo))

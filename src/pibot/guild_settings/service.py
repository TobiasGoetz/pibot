"""Guild settings — shared per-guild settings storage."""

from pibot.guild_settings.model import SettingsGroup, fieldDefault
from pibot.guild_settings.store import SettingsStore


class GuildSettingsService:
    """Shared per-guild settings storage."""

    def __init__(self, store: SettingsStore) -> None:
        """Initialize the service."""
        self.store = store

    async def getSettingsGroup[T: SettingsGroup](self, guildId: int, model: type[T]) -> T:
        """Return one settings group for a guild."""
        return await self.store.findSettingsGroup(guildId, model.name, model)

    async def setField[T: SettingsGroup](
        self,
        guildId: int,
        model: type[T],
        field: str,
        value: object,
    ) -> T:
        """Set one field on a settings group and return the updated config."""
        config = await self.getSettingsGroup(guildId, model)
        updated = config.model_copy(update={field: value})
        await self.store.saveSettingsGroup(guildId, model.name, updated)
        return updated

    async def unsetField[T: SettingsGroup](
        self,
        guildId: int,
        model: type[T],
        field: str,
    ) -> T:
        """Remove one stored field and return the config with model defaults applied."""
        config = await self.getSettingsGroup(guildId, model)
        fieldInfo = model.model_fields[field]
        updated = config.model_copy(update={field: fieldDefault(fieldInfo)})
        await self.store.unsetField(guildId, model.name, field)
        return updated

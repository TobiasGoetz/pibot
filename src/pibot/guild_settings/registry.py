"""Runtime registry of feature settings groups."""

import logging

from pibot.guild_settings.model import SettingsGroup

LOGGER = logging.getLogger("guild_settings.registry")

_GROUPS: dict[str, type[SettingsGroup]] = {}


def registerSettingsGroup[T: SettingsGroup](group: type[T]) -> type[T]:
    """Register a feature settings group. Called when a cog loads its config."""
    existing = _GROUPS.get(group.name)
    if existing is not None and existing is not group:
        msg = f"Duplicate settings group name: {group.name!r}"
        raise ValueError(msg)
    if existing is not group:
        _GROUPS[group.name] = group
        LOGGER.debug("Registered settings group: %s", group.name)
    return group


def getSettingsGroups() -> dict[str, type[SettingsGroup]]:
    """Return all settings groups registered by loaded cogs."""
    return dict(_GROUPS)

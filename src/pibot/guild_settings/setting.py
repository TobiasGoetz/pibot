"""Declarative per-feature setting definitions."""

from abc import ABC
from enum import StrEnum
from typing import Any, ClassVar, get_args, get_origin

import pytimeparse

from pibot.guild_settings.util import getNested, maskSecret

_SETTINGS_BY_KEY: dict[str, tuple[str, type[Setting[Any]]]] = {}


class SettingValueType(StrEnum):
    """How a setting value is parsed and stored."""

    STRING = "string"
    INT = "int"
    BOOL = "bool"
    DURATION = "duration"


class Setting[T](ABC):
    """Declarative setting. Subclass inside a FeatureConfig; drives set/view/reset."""

    key: ClassVar[str]
    description: ClassVar[str]
    valueType: ClassVar[SettingValueType] = SettingValueType.STRING
    secret: ClassVar[bool] = False
    default: ClassVar[Any] = None

    @classmethod
    def fullKey(cls, featureName: str) -> str:
        """Return the dotted user-facing key (e.g. ``summarize.cooldownSeconds``)."""
        return f"{featureName}.{cls.key}"

    @classmethod
    def mongoPath(cls, featureName: str) -> str:
        """Return the MongoDB dotted path for this setting."""
        return f"features.{featureName}.{cls.key}"

    @classmethod
    def pathParts(cls) -> tuple[str, ...]:
        """Return key segments for nested document access."""
        return tuple(cls.key.split("."))

    @classmethod
    def parse(cls, raw: str) -> Any:
        """Parse a user-provided string into a stored value."""
        if cls.valueType is SettingValueType.STRING:
            return raw
        if cls.valueType is SettingValueType.INT:
            try:
                return int(raw)
            except ValueError as exc:
                raise ValueError(f"`{raw}` is not a valid integer.") from exc
        if cls.valueType is SettingValueType.BOOL:
            lowered = raw.strip().lower()
            if lowered in ("true", "on", "1", "yes"):
                return True
            if lowered in ("false", "off", "0", "no"):
                return False
            raise ValueError(f"`{raw}` is not a valid boolean.")
        if cls.valueType is SettingValueType.DURATION:
            seconds = pytimeparse.parse(raw)
            if seconds is None or seconds <= 0:
                raise ValueError(f"Could not parse `{raw}` as a duration (e.g. `1h`, `30m`).")
            return int(seconds)
        raise ValueError(f"Unsupported value type: {cls.valueType}")

    @classmethod
    def formatDisplay(cls, value: Any) -> str:
        """Format a value for display."""
        if value is None:
            return "(not set)"
        if cls.secret and isinstance(value, str):
            return maskSecret(value)
        return str(value)

    @classmethod
    def getStored(cls, document: dict, featureName: str) -> Any:
        """Read the guild-stored value (not env-resolved)."""
        return getNested(document, ("features", featureName, *cls.pathParts()))

    @classmethod
    def resolveValue(cls, document: dict, featureName: str) -> Any:
        """Resolve stored guild override, otherwise the setting default."""
        stored = cls.getStored(document, featureName)
        value = stored if stored is not None else cls.default

        storageType = cls.storageType()
        if storageType is int and value is not None:
            return int(value)
        if storageType is bool and value is not None:
            return bool(value)
        return value

    @classmethod
    def getResolvedValue(cls, resolved: Any) -> Any:
        """Read a value from a resolved feature config object."""
        current = resolved
        for part in cls.pathParts():
            current = getattr(current, part)
        return current

    @classmethod
    def formatResolved(cls, resolved: Any) -> str:
        """Format the resolved (env-merged) value for display."""
        return cls.formatDisplay(cls.getResolvedValue(resolved))

    @classmethod
    def storageType(cls) -> type:
        """Return the generic type argument if declared (e.g. ``Setting[int]``)."""
        for base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(base)
            if origin is Setting:
                args = get_args(base)
                if args:
                    return args[0]
        return Any


def registerFeatureSettings(featureName: str, settings: tuple[type[Setting[Any]], ...]) -> None:
    """Index settings for autocomplete and lookup."""
    for settingCls in settings:
        _SETTINGS_BY_KEY[settingCls.fullKey(featureName)] = (featureName, settingCls)


def getAllSettings() -> dict[str, tuple[str, type[Setting[Any]]]]:
    """Return all registered settings keyed by ``feature.setting``."""
    return dict(_SETTINGS_BY_KEY)


def getSettingByKey(fullKey: str) -> tuple[str, type[Setting[Any]]] | None:
    """Look up a setting by ``feature.setting`` key."""
    return _SETTINGS_BY_KEY.get(fullKey)


def buildResolvedSlice(document: dict, featureName: str, settings: tuple[type[Setting[Any]], ...]) -> dict:
    """Build a nested resolved values dict from setting definitions."""
    result: dict[str, Any] = {}
    for settingCls in settings:
        value = settingCls.resolveValue(document, featureName)
        parts = settingCls.pathParts()
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result

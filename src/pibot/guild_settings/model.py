"""Pydantic models and field metadata for guild settings."""

import logging
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

from pibot.guild_settings.env import nestedModel

LOGGER = logging.getLogger("guild_settings.model")

_REGISTRY: dict[str, type[FeatureSettings]] = {}


class SettingsGroup(BaseModel):
    """Grouped guild settings fields. Subclass for nested groups or top-level config sections."""

    model_config = ConfigDict(frozen=True)

    @property
    def configured(self) -> bool:
        """Whether required values are present for this group."""
        return True


class FeatureSettings(SettingsGroup):
    """Per-feature guild settings model. Subclass once per feature; fields are the settings."""

    name: ClassVar[str]
    description: ClassVar[str]

    enabled: bool = Field(default=True, description="Whether this feature is active on the server")

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register concrete feature settings subclasses."""
        super().__init_subclass__(**kwargs)
        if "name" not in cls.__dict__:
            return
        _REGISTRY[cls.name] = cls
        LOGGER.debug("Registered feature: %s", cls.name)

    @property
    def available(self) -> bool:
        """Whether the feature is on and ready to run."""
        return self.enabled and self.configured

    @classmethod
    def parseSetting(cls, path: str, raw: str) -> object:
        """Parse a user-provided string into a stored value."""
        try:
            config = cls.model_validate(_nestPath(path, raw))
        except ValidationError as exc:
            raise ValueError(exc.errors()[0]["msg"]) from exc
        return toStoredValue(readPath(config, path))

def getSettings(cls: type[FeatureSettings]) -> tuple[tuple[str, str], ...]:
    """Return configurable fields (path, description) from the model schema."""
    return _collectSettingPaths(cls)


def _collectSettingPaths(model: type[BaseModel], pathPrefix: str = "") -> tuple[tuple[str, str], ...]:
    settings: list[tuple[str, str]] = []
    for name, fieldInfo in model.model_fields.items():
        path = f"{pathPrefix}.{name}" if pathPrefix else name
        nested = nestedModel(fieldInfo.annotation)
        if nested is not None:
            settings.extend(_collectSettingPaths(nested, path))
            continue
        settings.append((path, fieldInfo.description or path))
    return tuple(settings)


def getFeatures() -> dict[str, type[FeatureSettings]]:
    """Return all registered feature settings classes."""
    return dict(_REGISTRY)


def getFeature(name: str) -> type[FeatureSettings] | None:
    """Return a feature settings class by name."""
    return _REGISTRY.get(name)


def resolveSettingKey(fullKey: str) -> tuple[type[FeatureSettings], str] | None:
    """Resolve a ``feature.setting`` key to its settings class and field path."""
    featureName, _, path = fullKey.partition(".")
    if not path:
        return None
    feature = getFeature(featureName)
    if feature is None:
        return None
    if not any(settingPath == path for settingPath, _ in getSettings(feature)):
        return None
    return feature, path


def readPath(model: BaseModel, path: str) -> object:
    """Read a dotted attribute path from a Pydantic model."""
    current: object = model
    for part in path.split("."):
        current = getattr(current, part)
    return current


def setDictPath(document: dict, path: str, value: Any) -> None:
    """Write a nested value into a document using a dotted path."""
    current: dict = document
    parts = path.split(".")
    for key in parts[:-1]:
        nested = current.get(key)
        if not isinstance(nested, dict):
            nested = {}
            current[key] = nested
        current = nested
    current[parts[-1]] = value


def toStoredValue(value: object) -> object:
    """Convert a resolved model value to the form stored in Mongo."""
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    return value


def _nestPath(path: str, value: object) -> dict:
    parts = path.split(".")
    root: dict = {}
    current = root
    for part in parts[:-1]:
        nested: dict = {}
        current[part] = nested
        current = nested
    current[parts[-1]] = value
    return root

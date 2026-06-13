"""Pydantic models and field metadata for guild settings."""

import logging
from typing import Any, ClassVar, Self

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

LOGGER = logging.getLogger("guild_settings.model")

_REGISTRY: dict[str, type[FeatureSettings]] = {}


class SettingsGroup(BaseModel):
    """Grouped guild settings fields. Subclass for nested groups or top-level config sections."""

    model_config = ConfigDict(frozen=True)

    @property
    def configured(self) -> bool:
        """Whether required values are present for this group."""
        return True

    def toDocument(self) -> dict[str, Any]:
        """Serialize to a MongoDB/BSON-compatible document."""
        return self.model_dump(mode="json")

    @classmethod
    def fromDocument(cls, data: dict[str, Any]) -> Self:
        """Deserialize from a MongoDB/BSON document payload."""
        return cls.model_validate(data)


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
    def parseSetting(cls, field: str, raw: str) -> object:
        """Parse a user-provided string into a stored value."""
        if field not in cls.model_fields:
            msg = f"Unknown setting {field!r}"
            raise ValueError(msg)
        try:
            return TypeAdapter(cls.model_fields[field].annotation).validate_python(raw)
        except ValidationError as exc:
            raise ValueError(exc.errors()[0]["msg"]) from exc

def getSettings(cls: type[FeatureSettings]) -> tuple[tuple[str, str], ...]:
    """Return configurable fields (name, description) from the feature model."""
    return tuple((name, fieldInfo.description or name) for name, fieldInfo in cls.model_fields.items())


def getFeatures() -> dict[str, type[FeatureSettings]]:
    """Return all registered feature settings classes."""
    return dict(_REGISTRY)


def getFeature(name: str) -> type[FeatureSettings] | None:
    """Return a feature settings class by name."""
    return _REGISTRY.get(name)

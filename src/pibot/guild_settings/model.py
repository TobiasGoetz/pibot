"""Pydantic models and field metadata for guild settings."""

import logging
from typing import Annotated, ClassVar, TypeVar

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError
from pydantic.fields import FieldInfo

LOGGER = logging.getLogger("guild_settings.model")

_REGISTRY: dict[str, type[FeatureSettings]] = {}

TSettings = TypeVar("TSettings", bound="SettingsGroup")


def fieldDefault(fieldInfo: FieldInfo) -> object:
    """Return the default value for an optional model field."""
    if fieldInfo.is_required():
        msg = "Required settings cannot be reset to a model default."
        raise ValueError(msg)
    return fieldInfo.get_default(call_default_factory=True)


class SettingsGroup(BaseModel):
    """Grouped guild settings fields. Subclass for nested groups or top-level config sections."""

    model_config = ConfigDict(frozen=True)

    @classmethod
    def _fieldTypeAdapter(cls, field: str) -> TypeAdapter[object]:
        """Return a type adapter for one model field."""
        fieldInfo = cls.model_fields[field]
        if fieldInfo.metadata:
            annotated = Annotated[fieldInfo.annotation, *fieldInfo.metadata]
            return TypeAdapter(annotated)
        return TypeAdapter(fieldInfo.annotation)

    @classmethod
    def _coerceStoredValue(cls, field: str, raw: object) -> object:
        """Coerce a MongoDB value into the field's Python type."""
        try:
            return cls._fieldTypeAdapter(field).validate_python(raw)
        except ValidationError as exc:
            msg = f"Invalid stored value for {field!r}: {exc.errors()[0]['msg']}"
            raise ValueError(msg) from exc

    @classmethod
    def fromStored(cls: type[TSettings], data: dict[str, object]) -> TSettings:
        """Build settings from a partial MongoDB feature section."""
        values: dict[str, object] = {}
        for name, fieldInfo in cls.model_fields.items():
            if name in data:
                values[name] = cls._coerceStoredValue(name, data[name])
            elif not fieldInfo.is_required():
                values[name] = fieldDefault(fieldInfo)
        return cls.model_validate(values)

    @classmethod
    def parseSetting(cls, field: str, raw: str) -> object:
        """Parse a user-provided string into a stored value."""
        if field not in cls.model_fields:
            msg = f"Unknown setting {field!r}"
            raise ValueError(msg)
        try:
            return cls._fieldTypeAdapter(field).validate_python(raw)
        except ValidationError as exc:
            raise ValueError(exc.errors()[0]["msg"]) from exc

    def sparseDump(self) -> dict[str, object]:
        """Return only stored fields that should be persisted."""
        stored: dict[str, object] = {}
        for name in self.model_fields_set:
            fieldInfo = type(self).model_fields[name]
            value = getattr(self, name)
            if not fieldInfo.is_required() and value == fieldDefault(fieldInfo):
                continue
            stored[name] = value
        return stored


class FeatureSettings(SettingsGroup):
    """Per-feature guild settings model. Subclass once per feature; fields are the settings."""

    name: ClassVar[str]
    description: ClassVar[str]

    enabled: bool = Field(default=True, description="Whether this feature is active on the server")

    def __init_subclass__(cls) -> None:
        """Register concrete feature settings subclasses."""
        super().__init_subclass__()
        if "name" not in cls.__dict__:
            return
        _REGISTRY[cls.name] = cls
        LOGGER.debug("Registered feature: %s", cls.name)


def getFeatures() -> dict[str, type[FeatureSettings]]:
    """Return all registered feature settings classes."""
    return dict(_REGISTRY)

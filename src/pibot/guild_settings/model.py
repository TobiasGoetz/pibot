"""Pydantic models and field metadata for guild settings."""

import logging
from typing import Annotated, Any, ClassVar, TypeVar, cast

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
    def fromStored(cls: type[TSettings], data: dict[str, Any]) -> TSettings:
        """Build settings from a partial MongoDB feature section."""
        values: dict[str, Any] = {}
        for name, fieldInfo in cls.model_fields.items():
            if name in data:
                values[name] = data[name]
            elif not fieldInfo.is_required():
                values[name] = fieldDefault(fieldInfo)
        return cls.model_construct(**values)  # type: ignore[return-value]

    @property
    def configured(self) -> bool:
        """Whether all required settings are present."""
        for name, fieldInfo in type(self).model_fields.items():
            if fieldInfo.is_required() and name not in self.model_fields_set:
                return False
        return True

    @classmethod
    def parseSetting(cls, field: str, raw: str) -> object:
        """Parse a user-provided string into a stored value."""
        if field not in cls.model_fields:
            msg = f"Unknown setting {field!r}"
            raise ValueError(msg)
        fieldInfo = cls.model_fields[field]
        annotated = (
            Annotated[cast(Any, fieldInfo.annotation), *fieldInfo.metadata]  # ty: ignore[invalid-type-form]
            if fieldInfo.metadata
            else fieldInfo.annotation
        )
        try:
            return TypeAdapter(annotated).validate_python(raw)
        except ValidationError as exc:
            raise ValueError(exc.errors()[0]["msg"]) from exc

    def sparseDump(self) -> dict[str, Any]:
        """Return only stored fields that should be persisted."""
        dumped = self.model_dump(mode="json")
        defaultDump = type(self).fromStored({}).model_dump(mode="json")
        stored: dict[str, Any] = {}
        for name in self.model_fields_set:
            fieldInfo = type(self).model_fields[name]
            value = dumped[name]
            if not fieldInfo.is_required() and value == defaultDump.get(name):
                continue
            stored[name] = value
        return stored


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


def getFeatures() -> dict[str, type[FeatureSettings]]:
    """Return all registered feature settings classes."""
    return dict(_REGISTRY)

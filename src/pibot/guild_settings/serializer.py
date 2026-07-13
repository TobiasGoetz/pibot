"""Load, save, and parse guild settings values."""

from collections.abc import Mapping
from typing import Annotated

from pydantic import TypeAdapter, ValidationError
from pydantic.fields import FieldInfo

from pibot.guild_settings.model import SettingsGroup


def fieldDefault(fieldInfo: FieldInfo) -> object:
    """Return the default value for an optional model field."""
    if fieldInfo.is_required():
        msg = "Required settings cannot be reset to a model default."
        raise ValueError(msg)
    return fieldInfo.get_default(call_default_factory=True)


def _fieldTypeAdapter(model: type[SettingsGroup], field: str) -> TypeAdapter[object]:
    """Return a type adapter for one model field."""
    from pibot.guild_settings.ui.editors import partitionFieldMetadata

    fieldInfo = model.model_fields[field]
    _uiTypes, validation = partitionFieldMetadata(fieldInfo)
    if validation:
        annotated = Annotated[fieldInfo.annotation, *validation]
        return TypeAdapter(annotated)
    return TypeAdapter(fieldInfo.annotation)


def _coerceStoredValue(model: type[SettingsGroup], field: str, raw: object) -> object:
    """Coerce a MongoDB value into the field's Python type."""
    try:
        return _fieldTypeAdapter(model, field).validate_python(raw)
    except ValidationError as exc:
        msg = f"Invalid stored value for {field!r}: {exc.errors()[0]['msg']}"
        raise ValueError(msg) from exc


def fromStored[T: SettingsGroup](model: type[T], data: Mapping[str, object]) -> T:
    """Build settings from partial stored feature settings."""
    values: dict[str, object] = {}
    for name, fieldInfo in model.model_fields.items():
        if name in data:
            values[name] = _coerceStoredValue(model, name, data[name])
        elif not fieldInfo.is_required():
            values[name] = fieldDefault(fieldInfo)
    return model.model_validate(values)


def parseSetting(model: type[SettingsGroup], field: str, raw: str) -> object:
    """Parse a user-provided string into a stored value."""
    if field not in model.model_fields:
        msg = f"Unknown setting {field!r}"
        raise ValueError(msg)
    try:
        return _fieldTypeAdapter(model, field).validate_python(raw)
    except ValidationError as exc:
        raise ValueError(exc.errors()[0]["msg"]) from exc


def parseModalSetting(model: type[SettingsGroup], field: str, raw: str) -> object:
    """Parse modal text input, using the model default when optional and left empty."""
    fieldInfo = model.model_fields[field]
    if not raw:
        if fieldInfo.is_required():
            msg = f"{field} is required."
            raise ValueError(msg)
        return fieldDefault(fieldInfo)
    return parseSetting(model, field, raw)


def toStored(config: SettingsGroup) -> dict[str, object]:
    """Return only fields that should be persisted (non-default optional values included)."""
    stored: dict[str, object] = {}
    model = type(config)
    for name in config.model_fields_set:
        fieldInfo = model.model_fields[name]
        value = getattr(config, name)
        if not fieldInfo.is_required() and value == fieldDefault(fieldInfo):
            continue
        stored[name] = value
    return stored

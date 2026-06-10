"""Pydantic models and field metadata for guild settings."""

import logging
from typing import Annotated, Any, ClassVar, Self, get_args, get_origin

from pydantic import BaseModel, ConfigDict, Field, SecretStr, ValidationError

LOGGER = logging.getLogger("guild_settings.model")

_REGISTRY: dict[str, type[FeatureSettings]] = {}


class FeatureSettings(BaseModel):
    """Per-feature guild settings model. Subclass once per feature; fields are the settings."""

    model_config = ConfigDict(frozen=True)

    name: ClassVar[str]
    description: ClassVar[str]

    enabled: bool = Field(default=True, description="Whether this feature is active on the server")

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register concrete feature settings subclasses."""
        super().__init_subclass__(**kwargs)
        if "name" not in cls.__dict__:
            return
        registerFeature(cls)

    @property
    def isAvailable(self) -> bool:
        """Whether the feature can run for this guild."""
        raise NotImplementedError(f"{type(self).__name__} must implement isAvailable")

    @classmethod
    def settingKey(cls, path: str) -> str:
        """Return the dotted user-facing key (e.g. ``summarize.cooldownSeconds``)."""
        return f"{cls.name}.{path}"

    @classmethod
    def parseSetting(cls, path: str, raw: str) -> object:
        """Parse a user-provided string into a stored value."""
        return parseSettingInput(cls, path, raw)

    @classmethod
    def formatSetting(cls, path: str, config: FeatureSettings) -> str:
        """Format the resolved value from a feature config object."""
        value = readPath(config, path)
        if value is None:
            return ""
        return str(value)

    @classmethod
    def resolve(cls, document: dict) -> Self:
        """Resolve settings from stored guild overrides."""
        from pibot.guild_settings.util import getNested

        stored = getNested(document, ("features", cls.name)) or {}
        return cls.model_validate(stored)

    @classmethod
    def isAvailableFor(cls, document: dict) -> bool:
        """Return whether the feature can run for the guild."""
        return cls.resolve(document).isAvailable


def registerFeature(cls: type[FeatureSettings]) -> None:
    """Register a feature settings class."""
    _REGISTRY[cls.name] = cls
    LOGGER.debug("Registered feature: %s", cls.name)


def getSettings(cls: type[FeatureSettings]) -> tuple[tuple[str, str], ...]:
    """Return configurable fields (path, description) from the model schema."""
    return _collectSettings(cls)


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
    if feature is None or not any(settingPath == path for settingPath, _ in getSettings(feature)):
        return None
    return feature, path


def _collectSettings(model: type[BaseModel], pathPrefix: str = "") -> tuple[tuple[str, str], ...]:
    settings: list[tuple[str, str]] = []
    for name, fieldInfo in model.model_fields.items():
        path = f"{pathPrefix}.{name}" if pathPrefix else name
        nested = nestedModel(fieldInfo.annotation)
        if nested is not None:
            settings.extend(_collectSettings(nested, path))
            continue
        settings.append((path, fieldInfo.description or path))
    return tuple(settings)


def parseSettingInput(configClass: type[FeatureSettings], path: str, raw: str) -> object:
    """Parse user input through the feature model; return a plain value for Mongo."""
    try:
        config = configClass.model_validate(nestPath(path, raw))
    except ValidationError as exc:
        raise ValueError(exc.errors()[0]["msg"]) from exc
    return toStoredValue(readPath(config, path))


def nestPath(path: str, value: object) -> dict:
    """Build a nested dict from a dotted path and leaf value."""
    parts = path.split(".")
    root: dict = {}
    current = root
    for part in parts[:-1]:
        nested: dict = {}
        current[part] = nested
        current = nested
    current[parts[-1]] = value
    return root


def toStoredValue(value: object) -> object:
    """Convert a resolved model value to the form stored in Mongo."""
    if isinstance(value, SecretStr):
        return value.get_secret_value()
    return value


def nestedModel(annotation: object) -> type[BaseModel] | None:
    """Return a nested Pydantic model type from a field annotation, if any."""
    annotation = scalarType(annotation)
    origin = get_origin(annotation)
    if origin is not None:
        for arg in get_args(annotation):
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                return arg
        return None
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


def readPath(model: BaseModel, path: str) -> object:
    """Read a dotted attribute path from a model."""
    current: object = model
    for part in path.split("."):
        current = getattr(current, part)
    return current


def scalarType(annotation: object) -> object:
    """Return the scalar type from a field annotation."""
    inner, _ = _splitAnnotated(annotation)
    while get_origin(inner) is Annotated:
        inner = get_args(inner)[0]
    origin = get_origin(inner)
    if origin is not None:
        for arg in get_args(inner):
            if arg is not type(None):
                return arg
    return inner


def _splitAnnotated(annotation: object) -> tuple[object, list[object]]:
    if get_origin(annotation) is Annotated:
        args = get_args(annotation)
        return args[0], list(args[1:])
    return annotation, []

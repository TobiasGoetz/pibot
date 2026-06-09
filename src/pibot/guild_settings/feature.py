"""Feature config base class and auto-discovery registry."""

import importlib
import logging
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from pibot.guild_settings.setting import Setting, buildResolvedSlice, registerFeatureSettings

LOGGER = logging.getLogger("guild_settings.feature")

_REGISTRY: dict[str, type[FeatureConfig]] = {}
_DISCOVERED = False


@dataclass(frozen=True)
class FeatureMeta:
    """Public metadata for a registered feature."""

    name: str
    description: str
    defaultEnabled: bool


class FeatureConfig(ABC):
    """Base class for per-feature settings. Subclass once; registration is automatic."""

    name: ClassVar[str]
    description: ClassVar[str]
    defaultEnabled: ClassVar[bool] = True
    configClass: ClassVar[type[Any] | None] = None
    nestedConfigs: ClassVar[dict[str, type[Any]]] = {}
    _settings: ClassVar[tuple[type[Setting[Any]], ...]] = ()

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Register concrete feature config subclasses and their settings."""
        super().__init_subclass__(**kwargs)
        if ABC in cls.__bases__:
            return
        featureName = getattr(cls, "name", None)
        if not featureName:
            return

        settings = tuple(
            inner
            for inner in cls.__dict__.values()
            if isinstance(inner, type) and issubclass(inner, Setting) and inner is not Setting
        )
        cls._settings = settings
        registerFeatureSettings(featureName, settings)
        _REGISTRY[featureName] = cls
        LOGGER.debug("Registered feature config: %s (%s setting(s))", featureName, len(settings))

    @classmethod
    def getSettings(cls) -> tuple[type[Setting[Any]], ...]:
        """Return declarative settings defined on this feature."""
        return cls._settings

    @classmethod
    def resolve(cls, document: dict, *, enabled: bool) -> Any:
        """Resolve this feature's settings from a merged guild document."""
        if cls.configClass is None:
            raise TypeError(f"{cls.__name__} must set configClass or override resolve()")

        resolved = buildResolvedSlice(document, cls.name, cls.getSettings())
        kwargs: dict[str, Any] = {}
        for key, value in resolved.items():
            nestedCls = cls.nestedConfigs.get(key)
            kwargs[key] = nestedCls(**value) if nestedCls else value
        return cls.configClass(enabled=enabled, **kwargs)

    @classmethod
    def isAvailable(cls, document: dict, *, enabled: bool) -> bool:
        """Return whether the feature can run for the guild."""
        config = cls.resolve(document, enabled=enabled)
        isAvailable = getattr(config, "isAvailable", None)
        if callable(isAvailable):
            return bool(isAvailable())
        return enabled

    @classmethod
    def meta(cls) -> FeatureMeta:
        """Return feature metadata."""
        return FeatureMeta(name=cls.name, description=cls.description, defaultEnabled=cls.defaultEnabled)


def discoverFeatures() -> None:
    """Import ``cogs/<feature>/config.py`` modules so they self-register."""
    global _DISCOVERED
    if _DISCOVERED:
        return

    cogsRoot = Path(__file__).resolve().parents[1] / "cogs"
    for packageDir in sorted(cogsRoot.iterdir()):
        if not packageDir.is_dir():
            continue
        if packageDir.name.startswith("_"):
            continue
        configModule = packageDir / "config.py"
        if not configModule.is_file():
            continue
        importlib.import_module(f"pibot.cogs.{packageDir.name}.config")

    _DISCOVERED = True
    LOGGER.debug("Discovered %s feature config(s).", len(_REGISTRY))


def getFeatures() -> dict[str, type[FeatureConfig]]:
    """Return all registered feature config classes."""
    discoverFeatures()
    return dict(_REGISTRY)


def getFeature(name: str) -> type[FeatureConfig] | None:
    """Return a feature config class by name."""
    return getFeatures().get(name)

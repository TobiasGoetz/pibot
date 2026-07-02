"""Pydantic schema for per-feature guild settings."""

from typing import ClassVar

from pydantic import BaseModel, ConfigDict, Field


class SettingsGroup(BaseModel):
    """Per-feature guild settings schema. Subclass once per feature; fields are the settings."""

    model_config = ConfigDict(frozen=True)

    name: ClassVar[str]
    description: ClassVar[str]

    enabled: bool = Field(default=True, description="Whether this feature is active on the server")

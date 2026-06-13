"""Environment variable metadata for guild settings."""

import os
from typing import Annotated, get_args, get_origin

from pydantic import BaseModel
from pydantic.fields import FieldInfo


class EnvVar:
    """Bind a settings field to an environment variable."""

    def __init__(self, name: str) -> None:
        """Initialize with the environment variable name."""
        self.name = name


def collectEnvDefaults(model: type[BaseModel]) -> dict:
    """Build a nested dict of model defaults from annotated environment variables."""
    result: dict = {}
    for name, fieldInfo in model.model_fields.items():
        nested = nestedModel(fieldInfo.annotation)
        if nested is not None:
            nestedValues = collectEnvDefaults(nested)
            if nestedValues:
                result[name] = nestedValues
            continue
        envVar = _envVar(fieldInfo)
        if envVar is None:
            continue
        value = os.getenv(envVar.name, "").strip()
        if value:
            result[name] = value
    return result


def nestedModel(annotation: object) -> type[BaseModel] | None:
    """Return a nested Pydantic model type from a field annotation, if any."""
    while get_origin(annotation) is Annotated:
        annotation = get_args(annotation)[0]
    origin = get_origin(annotation)
    if origin is not None:
        for arg in get_args(annotation):
            if isinstance(arg, type) and issubclass(arg, BaseModel):
                return arg
        return None
    if isinstance(annotation, type) and issubclass(annotation, BaseModel):
        return annotation
    return None


def _envVar(fieldInfo: FieldInfo) -> EnvVar | None:
    for item in fieldInfo.metadata:
        if isinstance(item, EnvVar):
            return item
    return None

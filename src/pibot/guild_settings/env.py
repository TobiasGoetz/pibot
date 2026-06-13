"""Environment variable metadata for guild settings."""


class EnvVar:
    """Bind a settings field to an environment variable."""

    def __init__(self, name: str) -> None:
        """Initialize with the environment variable name."""
        self.name = name

"""Guild settings errors."""


class GuildSettingsError(Exception):
    """Guild settings panel and input validation."""


class InvalidSettingValue(GuildSettingsError):
    """Raised when user-provided settings input fails validation."""

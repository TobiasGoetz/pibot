"""Tests for PiBot logging configuration."""

import logging

from pibot.bot import configureLogging


def testConfigureLoggingAppliesLevelToPibotLoggersOnly() -> None:
    """DEBUG applies to PiBot loggers; discord stays at INFO."""
    # Act
    configureLogging(logging.DEBUG)

    # Assert
    assert logging.getLogger("pibot").getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger("pibot.bot").getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger("pibot.cogs.userstats.store").getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger("pibot.guild_settings.service").getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger("pibot.cogs.error_handler").getEffectiveLevel() == logging.DEBUG
    assert logging.getLogger("discord").getEffectiveLevel() == logging.INFO
    assert logging.getLogger("discord.http").getEffectiveLevel() == logging.INFO
    assert logging.getLogger("pymongo").getEffectiveLevel() == logging.INFO


def testConfigureLoggingRespectsInfoLevel() -> None:
    """INFO keeps PiBot loggers at INFO."""
    # Act
    configureLogging(logging.INFO)

    # Assert
    assert logging.getLogger("pibot.bot").getEffectiveLevel() == logging.INFO
    assert logging.getLogger("pibot.cogs.userstats.store").getEffectiveLevel() == logging.INFO

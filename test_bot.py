"""
Unit tests for the Bot library
"""

import bot


class TestBot:

    def test_addition(self):
        assert 4 == bot.add(2, 2)

    def test_subtraction(self):
        assert 2 == bot.subtract(4, 2)

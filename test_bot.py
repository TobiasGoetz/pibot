"""
Unit tests for the 314Bot library
"""

import bot


class Test314Bot:

    def test_addition(self):
        assert 4 == bot.add(2, 2)

    def test_subtraction(self):
        assert 2 == bot.subtract(4, 2)
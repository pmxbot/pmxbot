import importlib

from pmxbot import logging


class TestCommands:
    def test_boo(self):
        assert importlib.import_module('pmxbot.logging') is logging

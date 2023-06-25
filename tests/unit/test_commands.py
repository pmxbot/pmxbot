import importlib

from pmxbot import logging


class TestCommands:
    @classmethod
    def setup_class(cls):
        assert importlib.import_module('pmxbot.logging') is logging

    def test_boo(self):
        ...

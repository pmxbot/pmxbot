import importlib

from pmxbot import logging


def logical_xor(a, b):
    return bool(a) ^ bool(b)


def onetrue(*args):
    truthiness = list(filter(bool, args))
    return len(truthiness) == 1


class TestCommands:
    @classmethod
    def setup_class(cls):
        assert importlib.import_module('pmxbot.logging') is logging

    def test_boo(self):
        ...

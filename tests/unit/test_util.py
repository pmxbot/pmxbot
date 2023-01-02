import pytest

from pmxbot import util


@pytest.mark.xfail(reason="Wordnik is unreliable")
def test_lookup(needs_wordnik):
    assert util.lookup('dachshund') is not None


@pytest.mark.network
def test_emergency_compliment():
    assert util.load_emergency_compliments()


@pytest.mark.network
def test_acronym_lookup():
    assert util.lookup_acronym('NSFW')

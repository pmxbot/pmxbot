import pytest

from pmxbot import util


@pytest.mark.xfail(reason="Wordnik is unreliable")
def test_lookup(needs_wordnik):
    assert util.lookup('dachshund') is not None


@pytest.mark.xfail(reason="#97: Google is unreliable")
def test_emergency_compliment(needs_internet):
    assert util.load_emergency_compliments()


def test_acronym_lookup(needs_internet):
    assert util.lookup_acronym('NSFW')

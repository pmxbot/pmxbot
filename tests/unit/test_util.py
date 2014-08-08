import pytest

from pmxbot import util

@pytest.has_wordnik
def test_lookup():
	assert util.lookup('dachshund') is not None

@pytest.has_internet
def test_emergency_compliment():
	assert util.load_emergency_compliments()

@pytest.has_internet
def test_acronym_lookup():
	assert util.lookup_acronym('NSFW')

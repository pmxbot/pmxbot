import pytest

from pmxbot import util

@pytest.has_wordnik
def test_lookup():
	assert util.lookup('dachshund') is not None

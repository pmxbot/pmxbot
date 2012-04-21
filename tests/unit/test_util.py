import pytest

from pmxbot import util

@pytest.has_internet
def test_lookup():
	assert util.lookup('dachshund') is not None

import functools

import pytest

import pmxbot.util


def throws_exception(call, exceptions=[Exception]):
	"""
	Invoke the function and return True if it raises any of the
	exceptions provided. Otherwise, return False.
	"""
	try:
		call()
	except tuple(exceptions):
		return True
	except Exception:
		pass
	return False


@pytest.fixture
def needs_internet():
	open_google = functools.partial(pmxbot.util.get_html, 'http://www.google.com')
	has_internet = not throws_exception(open_google)
	if not has_internet:
		pytest.skip('Internet connectivity unavailable')


@pytest.fixture
def needs_wordnik(needs_internet):
	if 'wordnik' not in dir(pmxbot.util):
		pytest.skip('Wordnik not available')

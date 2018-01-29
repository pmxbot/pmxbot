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


def pytest_namespace():
	return dict(
		has_internet=pytest.mark.skipif('not pytest.config.has_internet'),
		has_wordnik=pytest.mark.skipif('not pytest.config.has_wordnik'),
	)


def pytest_configure(config):
	open_google = functools.partial(pmxbot.util.get_html, 'http://www.google.com')
	config.has_internet = not throws_exception(open_google)
	config.has_wordnik = config.has_internet and 'wordnik' in dir(pmxbot.util)

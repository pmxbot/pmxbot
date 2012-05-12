from __future__ import print_function

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
		has_internet = pytest.mark.skipif('not pytest.config.has_internet')
	)

def pytest_configure(config):
	open_google = functools.partial(pmxbot.util.get_html,
		'http://www.google.com')
	config.has_internet = not throws_exception(open_google)

def pytest_addoption(parser):
	parser.addoption("--runslow", action="store_true",
		help="run slow tests")

def pytest_runtest_setup(item):
	if 'slow' in item.keywords and not item.config.getvalue("runslow"):
		pytest.skip("need --runslow option to run")

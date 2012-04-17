from __future__ import print_function

import urllib2
import httplib2
import functools

import pytest

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
	open_google = functools.partial(urllib2.urlopen, 'http://www.google.com')
	config.has_internet = not throws_exception(open_google, [Exception, urllib2.URLError])
	# we need to test httplib2 also, because pmxbot uses httplib2 and
	#  httplib2 doesn't handle proxies well.
	http = httplib2.Http(timeout=2)
	open_google = functools.partial(http.request, 'http://www.google.com')
	config.has_internet &= not throws_exception(open_google, [Exception])

def pytest_addoption(parser):
	parser.addoption("--runslow", action="store_true",
		help="run slow tests")

def pytest_runtest_setup(item):
	if 'slow' in item.keywords and not item.config.getvalue("runslow"):
		pytest.skip("need --runslow option to run")

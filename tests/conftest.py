import pytest
from jaraco.context import ExceptionTrap

import pmxbot.util


@pytest.fixture
def needs_internet():
	with ExceptionTrap() as trap:
		pmxbot.util.get_html('http://www.google.com')
	if trap:
		pytest.skip('Internet connectivity unavailable')


@pytest.fixture
def needs_wordnik(needs_internet):
	if 'wordnik' not in dir(pmxbot.util):
		pytest.skip('Wordnik not available')

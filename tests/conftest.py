import pytest
import jaraco.functools
from jaraco.context import ExceptionTrap

from pmxbot import http


@jaraco.functools.once
def has_internet():
    with ExceptionTrap() as trap:
        http.open_url('http://www.google.com')
    return not trap


def check_internet():
    has_internet() or pytest.skip('Internet connectivity unavailable')


@pytest.fixture
def needs_internet():
    check_internet()


@pytest.fixture
def needs_wordnik(needs_internet):
    if 'wordnik' not in dir(pmxbot.util):
        pytest.skip('Wordnik not available')


def pytest_configure():
    pytest.check_internet = check_internet

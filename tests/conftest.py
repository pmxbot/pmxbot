import os

import pytest

import pmxbot.util


@pytest.fixture
def needs_wordnik(needs_internet):
    if 'wordnik' not in dir(pmxbot.util):
        pytest.skip('Wordnik not available')


@pytest.fixture
def google_api_key(monkeypatch):
    key = os.environ.get('GOOGLE_API_KEY')
    if not key:
        pytest.skip("Need GOOGLE_API_KEY environment variable")
    monkeypatch.setitem(pmxbot.config, 'Google API key', key)

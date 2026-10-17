import functools

import pytest

from pmxbot import logging, quotes


@pytest.fixture
def clean_quotes(mongodb_uri):
    q = quotes.Quotes.from_URI(mongodb_uri)
    q.lib = 'test'

    clean = functools.partial(q.db.delete_many, dict(library='test'))
    clean()
    try:
        yield q
    finally:
        clean()


def test_MongoDBQuotes(clean_quotes):
    q = clean_quotes

    q.add('who would ever say such a thing')
    q.add('go ahead, take my pay')
    q.add("let's do the Time Warp again")
    qt, _i, _n = q.lookup('time warp')
    assert qt.startswith("let's")
    q.lookup('nonexistent')
    q.delete('Time Warp')
    qt, _i, _n = q.lookup('Time Warp')
    assert qt == ''


@pytest.fixture
def sqlite_quotes(tmp_path):
    uri = f'sqlite:{tmp_path / "pmxbot.sqlite"}'
    # adding a quote consults the most recent log message
    logging.Logger.from_URI(uri).message('#inane', 'nik', 'hello')
    q = quotes.Quotes.from_URI(uri)
    q.lib = 'test'
    return q


def test_SQLiteQuotes_lookup_with_quote(sqlite_quotes):
    q = sqlite_quotes
    q.add("it's a trap")
    q.add('its a trap')
    assert q.lookup("it's") == ("it's a trap", 1, 1)
    assert q.lookup("trap")[2] == 2

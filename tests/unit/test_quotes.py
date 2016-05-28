import pytest

from pmxbot import quotes


@pytest.yield_fixture
def clean_quotes(mongodb_uri):
	q = quotes.Quotes.from_URI(mongodb_uri)
	q.lib = 'test'
	clean = lambda: q.db.remove({'library': 'test'})
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
	qt, i, n = q.lookup('time warp')
	assert qt.startswith("let's")
	q.lookup('nonexistent')
	q.delete('Time Warp')
	qt, i, n = q.lookup('Time Warp')
	assert qt == ''

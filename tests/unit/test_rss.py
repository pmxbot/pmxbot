import pytest

import pmxbot.rss

sample_feed_entries = [
	{'id': '1234'},
	{'link': 'http://example.com/2012/12/23'},
	{'title': 'A great blog'},
]

@pytest.fixture()
def history(db_uri, request):
	history = pmxbot.rss.FeedHistory(db_uri)
	request.addfinalizer(history._FeedHistory__finalize)
	return history

class TestFeedHistory(object):

	@pytest.mark.parametrize('entry', sample_feed_entries)
	def test_add_seen_feed(self, history, entry):
		"""
		Each entry should be added only once, return True when it's added
		and return False each subsequent time.
		"""
		added = history.add_seen_feed(entry, 'http://example.com')
		assert added == True
		added = history.add_seen_feed(entry, 'http://example.com')
		assert added == False
		assert len(history) == 1

	def test_add_seen_feed_no_identifier(self, history):
		"""
		If an entry can't be identified, it should log a warning but just
		return False.
		"""
		entry = {'foo': 'bar'}
		"an entry with no id/link/title"

		assert not history.add_seen_feed(entry, 'http://example.com')

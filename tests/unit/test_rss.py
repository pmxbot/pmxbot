from __future__ import unicode_literals

try:
	import urllib.parse as urllib_parse
except ImportError:
	import urlparse as urllib_parse

import pytest
import feedparser

import pmxbot.rss

sample_feed_entries = [
	{'id': '1234'},
	{'link': 'http://example.com/2012/12/23'},
	{'title': 'A great blog'},
]

@pytest.fixture()
def history(db_uri, request):
	history = pmxbot.rss.FeedHistory(db_uri)
	request.addfinalizer(history.store.clear)
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
		assert added is True
		added = history.add_seen_feed(entry, 'http://example.com')
		assert added is False
		assert len(history) == 1

	def test_add_seen_feed_no_identifier(self, history):
		"""
		If an entry can't be identified, it should log a warning but just
		return False.
		"""
		entry = {'foo': 'bar'}
		"an entry with no id/link/title"

		assert not history.add_seen_feed(entry, 'http://example.com')

	def test_feeds_loaded(self, history):
		"""
		Feeds saved in one history should be already present when loaded
		subsequently in a new history object.
		"""
		entry = {'id': '1234'}
		history.add_seen_feed(entry, 'http://example.com')
		assert len(history) == 1

		# now create a new history object
		orig_uri = history.store.uri
		new_history = pmxbot.rss.FeedHistory(orig_uri)
		assert len(new_history) == 1
		assert new_history.add_seen_feed(entry, 'http://example.com') is False

@pytest.has_internet
def test_format_entry():
	bitbucket = 'https://bitbucket.org'
	feed_url=urllib_parse.urljoin(bitbucket, '/yougov/pmxbot/rss')
	res = feedparser.parse(feed_url)
	entry = res['entries'][0]
	pmxbot.rss.RSSFeeds.format_entry(entry)

def test_format_entry_unicode():
	pmxbot.rss.RSSFeeds.format_entry(dict(title='\u2013'))

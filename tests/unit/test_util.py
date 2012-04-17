import pytest

from pmxbot import util

class TestMongoDBKarma(object):
	def setup_karma(self, mongodb_uri):
		k = util.Karma.from_URI(mongodb_uri)
		k.db = k.db.database.connection[
			k.db.database.name+'_test'
			][k.db.name]
		self.karma = k

	def teardown_method(self, method):
		if hasattr(self, 'karma'):
			self.karma.db.drop()

	def test_basic_usage(self, mongodb_uri):
		self.setup_karma(mongodb_uri)
		k = self.karma
		k.change('foo', 1)
		k.change('bar', 1)
		k.set('baz', 3)
		k.set('baz', 2)
		k.link('foo', 'bar')
		assert k.lookup('foo') == 2
		k.link('foo', 'baz')
		assert k.lookup('baz') == k.lookup('foo') == 4
		k.change('foo', 1)
		assert k.lookup('foo') == k.lookup('bar') == 5

	def test_linking_same_does_nothing(self, mongodb_uri):
		self.setup_karma(mongodb_uri)
		k = self.karma
		k.set('foo', 99)
		k.link('foo', 'foo')
		assert k.lookup('foo') == 99


def test_MongoDBQuotes(mongodb_uri):
	q = util.Quotes.from_URI(mongodb_uri)
	q.lib = 'test'
	clean = lambda: q.db.remove({'library': 'test'})
	clean()
	try:
		q.quoteAdd('who would ever say such a thing')
		q.quoteAdd('go ahead, take my pay')
		q.quoteAdd("let's do the Time Warp again")
		q.quoteLookup('time warp')
		q.quoteLookup('nonexistent')
	finally:
		clean()

@pytest.has_internet
def test_lookup():
	assert util.lookup('dachshund') is not None

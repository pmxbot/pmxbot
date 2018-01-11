import itertools
import functools

from more_itertools import recipes

import pytest

from pmxbot import saysomething


class TestMongoDBChains:
	@pytest.fixture
	def chains(self, request, db_uri):
		store = saysomething.Chains.from_URI(db_uri)
		request.addfinalizer(store.purge)
		return store

	def test_basic_usage(self, chains):
		chains.feed('foo: what did you say?')
		# because there's only one message, that's the one you'll get
		assert chains.get() == 'foo: what did you say?'

	def test_seed(self, chains):
		chains.feed('bar: what about if you have a seed? What happens then?')
		msg = chains.get('seed?')
		assert msg == 'What happens then?'

	def test_non_deterministic_traversal(self, chains):
		chains.feed('a quick brown fox')
		chains.feed('a cute white hen')
		chains.feed('three white boys')
		# A seed of the word 'a' should lead to several phrases
		from_a = functools.partial(chains.get, 'a')
		msgs = recipes.repeatfunc(from_a)
		# prevent infinite results
		msgs = itertools.islice(msgs, 1000)

		# at least one of those thousand messages should
		# include 'a quick brown fox', 'a cute white hen',
		# and 'a cute white boys'
		assert any('fox' in msg for msg in msgs)
		assert any('hen' in msg for msg in msgs)
		assert any('boys' in msg for msg in msgs)
		assert not any('three' in msg for msg in msgs)

	def test_unusual_text(self, chains):
		chains.feed('<this_thing .has html #3333 and $!@$%stuff. ☉')
		assert chains.get('☉') == ''
		assert chains.get('<this_thing').startswith('.has')
		chains.feed('$foo bar')
		assert chains.get('$foo') == 'bar'

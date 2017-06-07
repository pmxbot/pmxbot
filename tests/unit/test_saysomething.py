import pytest

from pmxbot import saysomething


class TestMongoDBChains:
	@pytest.fixture
	def mongodb_chains(self, request, mongodb_uri):
		k = saysomething.MongoDBChains.from_URI(mongodb_uri)
		k.db = k.db.database.connection[
			k.db.database.name + '_test'
		][k.db.name]
		request.addfinalizer(k.db.drop)
		return k

	def test_basic_usage(self, mongodb_chains):
		chains = mongodb_chains
		chains.save_message('foo: what did you say?')
		# because there's only one message, that's the one you'll get
		assert chains.get_paragraph() == 'foo: what did you say?'

	def test_seed(self, mongodb_chains):
		chains = mongodb_chains
		chains.save_message('bar: what about if you have a seed? What happens then?')
		msg = chains.get_paragraph('seed?')
		assert msg == 'What happens then?'

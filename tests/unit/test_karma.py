import os
import tempfile
import functools

import pytest

from pmxbot import karma

class TestMongoDBKarma(object):
	def setup_karma(self, mongodb_uri):
		k = karma.Karma.from_URI(mongodb_uri)
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
		with pytest.raises(karma.SameName):
			k.link('foo', 'foo')
		assert k.lookup('foo') == 99

	def test_already_linked_raises_error(self, mongodb_uri):
		self.setup_karma(mongodb_uri)
		k = self.karma
		k.set('foo', 50)
		k.set('bar', 50)
		k.link('foo', 'bar')
		assert k.lookup('foo') == k.lookup('bar') == 100
		with pytest.raises(karma.AlreadyLinked):
			k.link('foo', 'bar')
		with pytest.raises(karma.AlreadyLinked):
			k.link('bar', 'foo')
		assert k.lookup('foo') == k.lookup('bar') == 100

class TestSQLiteKarma(object):
	finalizers = []

	@classmethod
	def teardown_class(cls):
		for finalizer in cls.finalizers:
			finalizer()

	def test_linking_same_does_nothing(self):
		tf = tempfile.NamedTemporaryFile(delete=False)
		tf.close()
		self.finalizers.append(functools.partial(os.remove, tf.name))
		k = karma.Karma.from_URI('sqlite://{tf.name}'.format(**vars()))
		k.set('foo', 99)
		k.link('foo', 'foo')
		assert k.lookup('foo') == 99

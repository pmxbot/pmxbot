import os
import itertools
import urlparse

from .classutil import itersubclasses

class SelectableStorage(object):
	"""
	A mix-in for storage classes which will construct a suitable subclass based
	on the URI.
	"""
	@classmethod
	def from_URI(cls, URI):
		candidates = itersubclasses(cls)
		if hasattr(cls, 'scheme'):
			candidates = itertools.chain([cls], candidates)
		matches = (cls for cls in candidates if cls.uri_matches(URI))
		return next(matches)(URI)

	@classmethod
	def uri_matches(cls, uri):
		super_matches = super(SelectableStorage, cls).uri_matches(uri)
		return urlparse.urlparse(uri).scheme == cls.scheme or super_matches

	@classmethod
	def migrate(cls, source_uri, dest_uri):
		source = cls.from_URI(source_uri)
		dest = cls.from_URI(dest_uri)
		map(dest.import_, source.export_all())

class Storage(object):
	# ABC
	@classmethod
	def uri_matches(cls, uri): return False

class SQLiteStorage(Storage):
	scheme = 'sqlite'
	
	@classmethod
	def uri_matches(cls, uri):
		return uri.endswith('.sqlite')

	def __init__(self, uri):
		self._import_modules()
		self.filename = urlparse.urlparse(uri).path
		self.db = sqlite.connect(self.filename, isolation_level=None, timeout=20.0)
		self.init_tables()

	def init_tables(self):
		pass

	def _import_modules(self):
		try:
			from pysqlite2 import dbapi2 as sqlite
		except ImportError:
			from sqlite3 import dbapi2 as sqlite
		globals().update(sqlite=sqlite)

class MongoDBStorage(Storage):
	scheme = 'mongodb'
	
	@classmethod
	def uri_matches(cls, uri):
		return uri.startswith('mongodb:')

	def __init__(self, host_uri):
		# for now do a delayed import to avoid interfering with
		# canonical logging module.
		globals().update(pymongo=__import__('pymongo.objectid'))
		self.db = pymongo.Connection(host_uri).pmxbot[self.collection_name]

def migrate_all(source, dest):
	for cls in SelectableStorage.__subclasses__():
		try:
			cls.migrate(source, dest)
		except AttributeError:
			print("Unable to migrate {cls}".format(**vars()))

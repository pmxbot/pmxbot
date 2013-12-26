from __future__ import absolute_import

import abc
import itertools
import importlib
import logging
import threading
try:
	import urllib.parse as urllib_parse
except ImportError:
	import urlparse as urllib_parse

try:
	import sqlite3 as sqlite
except ImportError:
	pass

try:
	import pymongo
	import bson
except ImportError:
	pass

from jaraco.util.classutil import itersubclasses

log = logging.getLogger(__name__)

class SelectableStorage(object):
	"""
	A mix-in for storage classes which will construct a suitable subclass based
	on the URI.
	"""

	_finalizers = []

	@classmethod
	def from_URI(cls, URI):
		candidates = reversed(list(itersubclasses(cls)))
		if hasattr(cls, 'scheme'):
			candidates = itertools.chain([cls], candidates)
		matches = (cls for cls in candidates if cls.uri_matches(URI))
		return next(matches)(URI)

	@classmethod
	def uri_matches(cls, uri):
		super_matches = super(SelectableStorage, cls).uri_matches(uri)
		return (urllib_parse.urlparse(uri).scheme == cls.scheme
			or super_matches)

	@classmethod
	def migrate(cls, source_uri, dest_uri):
		source = cls.from_URI(source_uri)
		dest = cls.from_URI(dest_uri)
		map(dest.import_, source.export_all())

	@classmethod
	def finalize(cls):
		"Delete the various persistence objects"
		for finalizer in cls._finalizers:
			try:
				finalizer()
			except Exception:
				log.exception("Error in finalizer %s", finalizer)


class Storage(object):
	@classmethod
	@abc.abstractmethod
	def uri_matches(cls, uri):
		return False


class SQLiteStorage(Storage, threading.local):
	scheme = 'sqlite'

	@classmethod
	def uri_matches(cls, uri):
		return uri.endswith('.sqlite')

	def __init__(self, uri):
		importlib.import_module('sqlite3')
		self.uri = uri
		self.filename = urllib_parse.urlparse(uri).path
		self.db = sqlite.connect(self.filename, isolation_level=None,
			timeout=20.0)
		self.init_tables()

	def init_tables(self):
		pass


class MongoDBStorage(Storage):
	scheme = 'mongodb'

	@classmethod
	def uri_matches(cls, uri):
		return uri.startswith('mongodb:')

	def __init__(self, host_uri):
		self.uri = host_uri
		self.db = self._get_collection(host_uri)

	@classmethod
	def _get_collection(cls, uri):
		importlib.import_module('pymongo')
		uri_p = pymongo.uri_parser.parse_uri(uri)
		db_name = uri_p['database'] or 'pmxbot'
		return pymongo.Connection(uri)[db_name][cls.collection_name]

def migrate_all(source, dest):
	for cls in SelectableStorage.__subclasses__():
		try:
			cls.migrate(source, dest)
		except AttributeError:
			print("Unable to migrate {cls}".format(**vars()))

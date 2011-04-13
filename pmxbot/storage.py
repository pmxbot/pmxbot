import os
try:
	from pysqlite2 import dbapi2 as sqlite
except ImportError:
	from sqlite3 import dbapi2 as sqlite

class SQLiteStorage(object):
	def __init__(self, repo):
		self.repo = repo
		self.dbfn = os.path.join(self.repo, 'pmxbot.sqlite')
		self.db = sqlite.connect(self.dbfn, isolation_level=None, timeout=20.0)
		self.init_tables()

	def init_tables(self):
		pass

class MongoDBStorage(object):
	def __init__(self, host_uri):
		# for now do a delayed import to avoid interfering with
		# canonical logging module.
		globals().update(pymongo=__import__('pymongo'))
		self.db = pymongo.Connection(host_uri).pmxbot[self.collection_name]

# vim:ts=4:sw=4:noexpandtab

from __future__ import absolute_import

import random

import pmxbot
from . import storage
from .core import command

class Quotes(storage.SelectableStorage):
	lib = 'pmx'

	@classmethod
	def initialize(cls):
		cls.store = cls.from_URI(pmxbot.config.database)
		cls._finalizers.append(cls.finalize)

	@classmethod
	def finalize(cls):
		del cls.store

class SQLiteQuotes(Quotes, storage.SQLiteStorage):
	def init_tables(self):
		CREATE_QUOTES_TABLE = '''
			CREATE TABLE IF NOT EXISTS quotes (quoteid INTEGER NOT NULL, library VARCHAR, quote TEXT, PRIMARY KEY (quoteid))
		'''
		CREATE_QUOTES_INDEX = '''CREATE INDEX IF NOT EXISTS ix_quotes_library on quotes(library)'''
		CREATE_QUOTE_LOG_TABLE = '''
			CREATE TABLE IF NOT EXISTS quote_log (quoteid varchar, logid INTEGER)
		'''
		self.db.execute(CREATE_QUOTES_TABLE)
		self.db.execute(CREATE_QUOTES_INDEX)
		self.db.execute(CREATE_QUOTE_LOG_TABLE)
		self.db.commit()

	def quoteLookupWNum(self, rest=''):
		rest = rest.strip()
		if rest:
			if rest.split()[-1].isdigit():
				num = rest.split()[-1]
				query = ' '.join(rest.split()[:-1])
				qt, i, n = self.quoteLookup(query, num)
			else:
				qt, i, n = self.quoteLookup(rest)
		else:
			qt, i, n = self.quoteLookup()
		return qt, i, n

	def quoteLookup(self, thing='', num=0):
		lib = self.lib
		BASE_SEARCH_SQL = 'SELECT quoteid, quote FROM quotes WHERE library = ? %s order by quoteid'
		thing = thing.strip().lower()
		num = int(num)
		if thing:
			SEARCH_SQL = BASE_SEARCH_SQL % (' AND %s' % (' AND '.join(["quote like '%%%s%%'" % x for x in thing.split()])))
		else:
			SEARCH_SQL = BASE_SEARCH_SQL % ''
		results = [x[1] for x in self.db.execute(SEARCH_SQL, (lib,)).fetchall()]
		n = len(results)
		if n > 0:
			if num:
				i = num-1
			else:
				i = random.randrange(n)
			quote = results[i]
		else:
			i = 0
			quote = ''
		return (quote, i+1, n)

	def quoteAdd(self, quote):
		lib = self.lib
		quote = quote.strip()
		ADD_QUOTE_SQL = 'INSERT INTO quotes (library, quote) VALUES (?, ?)'
		res = self.db.execute(ADD_QUOTE_SQL, (lib, quote,))
		quoteid = res.lastrowid
		log_id, log_message = self.db.execute('SELECT id, message FROM LOGS order by datetime desc limit 1').fetchone()
		if quote in log_message:
			self.db.execute('INSERT INTO quote_log (quoteid, logid) VALUES (?, ?)', (quoteid, log_id))
		self.db.commit()

	def __iter__(self):
		query = "SELECT quote FROM quotes WHERE library = ?"
		return self.db.execute(query, [self.lib])

	def export_all(self):
		query = "SELECT quote, library, logid from quotes left outer join quote_log on quotes.quoteid = quote_log.quoteid"
		fields = 'text', 'library', 'log_id'
		return (dict(zip(fields, res)) for res in self.db.execute(query))

class MongoDBQuotes(Quotes, storage.MongoDBStorage):
	collection_name = 'quotes'

	def quoteLookupWNum(self, rest=''):
		rest = rest.strip()
		if rest:
			if rest.split()[-1].isdigit():
				num = rest.split()[-1]
				query = ' '.join(rest.split()[:-1])
				qt, i, n = self.quoteLookup(query, num)
			else:
				qt, i, n = self.quoteLookup(rest)
		else:
			qt, i, n = self.quoteLookup()
		return qt, i, n

	def quoteLookup(self, thing='', num=0):
		thing = thing.strip().lower()
		num = int(num)
		words = thing.split()
		def matches(quote):
			quote = quote.lower()
			return all(word in quote for word in words)
		results = [
			row['text'] for row in
			self.db.find(dict(library=self.lib)).sort('_id')
			if matches(row['text'])
		]
		n = len(results)
		if n > 0:
			if num:
				i = num-1
			else:
				i = random.randrange(n)
			quote = results[i]
		else:
			i = 0
			quote = ''
		return (quote, i+1, n)

	def quoteAdd(self, quote):
		quote = quote.strip()
		quote_id = self.db.insert(dict(library=self.lib, text=quote))
		# see if the quote added is in the last IRC message logged
		newest_first = [('_id', storage.pymongo.DESCENDING)]
		last_message = self.db.database.logs.find_one(sort=newest_first)
		if last_message and quote in last_message['message']:
			self.db.update({'_id': quote_id},
				{'$set': dict(log_id=last_message['_id'])})

	def __iter__(self):
		return self.db.find(library=self.lib)

	def _build_log_id_map(self):
		from . import logging
		if not hasattr(logging.Logger, 'log_id_map'):
			log_db = self.db.database.logs
			logging.Logger.log_id_map = dict(
				(logging.MongoDBLogger.extract_legacy_id(rec['_id']), rec['_id'])
				for rec in log_db.find(fields=[])
			)
		return logging.Logger.log_id_map

	def import_(self, quote):
		log_id_map = self._build_log_id_map()
		log_id = quote.pop('log_id', None)
		log_id = log_id_map.get(log_id, log_id)
		if log_id is not None:
			quote['log_id'] = log_id
		self.db.insert(quote)

@command('quote', aliases=('q',), doc='If passed with nothing then get a '
	'random quote. If passed with some string then search for that. If '
	'prepended with "add:" then add it to the db, eg "!quote add: drivers: I '
	'only work here because of pmxbot!"')
def quote(client, event, channel, nick, rest):
	rest = rest.strip()
	if rest.startswith('add: ') or rest.startswith('add '):
		quoteToAdd = rest.split(' ', 1)[1]
		Quotes.store.quoteAdd(quoteToAdd)
		qt = False
		return 'Quote added!'
	qt, i, n = Quotes.store.quoteLookupWNum(rest)
	if not qt: return
	return '(%s/%s): %s' % (i, n, qt)

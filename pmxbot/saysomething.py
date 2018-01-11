import random
import itertools
import abc
import contextlib

from more_itertools.recipes import pairwise, consume
import jaraco.collections
from jaraco.mongodb import fields

import pmxbot.core
import pmxbot.storage


class Chains(
	pmxbot.storage.SelectableStorage,
	metaclass=abc.ABCMeta):
	term = '\n'

	@classmethod
	def initialize(cls):
		cls.store = cls.from_URI()
		cls._finalizers.append(cls.finalize)

	@classmethod
	def finalize(cls):
		del cls.store

	def feed(self, message):
		message = message.rstrip()
		words = message.split(' ') + [self.term]
		self.save(words)

	def save(self, words):
		"""
		Save these words as encountered.
		"""
		# TODO: Need to cap the network, expire old words/phrases
		initial = None,
		all_words = itertools.chain(initial, words)
		consume(itertools.starmap(self.update, pairwise(all_words)))

	def _get_words(self, seed=None):
		word = seed
		while True:
			word = self.next(word)
			yield word

	def get(self, seed=None):
		words = self._get_words(seed)
		p_words = itertools.takewhile(lambda word: word != self.term, words)
		return ' '.join(p_words)

	@staticmethod
	def choose(raw_freq):
		"""
		Given a dictionary of words and their frequencies,
		return a random word weighted to a distribution of
		those frequencies.
		"""
		# Build a map of accumulated frequencies to words
		acc = itertools.accumulate(raw_freq.values())
		lookup = jaraco.collections.RangeMap(zip(acc, raw_freq))

		# choose a random word proportional - to do that, pick a
		# random index from 1 to the total.
		_, total = lookup.bounds()
		return lookup[random.randint(1, total)]

	@abc.abstractmethod
	def update(self, initial, follows):
		"""
		Associate the two words where initial immediately preceeds
		follows.
		"""

	@abc.abstractmethod
	def next(self, initial):
		"""
		Given initial, return a word that would have followed it,
		proportional to the frequency encountered.
		"""


class MongoDBChains(Chains, pmxbot.storage.MongoDBStorage):
	"""
	Store word associations in MongoDB with documents like so:

	{
		'_id': <trigger word or None>,
		'begets': <dict of word:frequency>
	}
	"""
	collection_name = 'chains'

	def update(self, initial, follows):
		"""
		Given two words, initial then follows, associate those words
		"""
		filter = dict(_id=initial)
		key = 'begets.' + fields.encode(follows)
		oper = {'$inc': {key: 1}}
		self.db.update(filter, oper, upsert=True)

	def next(self, initial):
		doc = self.db.find_one(dict(_id=initial))
		return fields.decode(self.choose(doc['begets']))

	def purge(self):
		self.db.drop()


class SQLiteChains(Chains, pmxbot.storage.SQLiteStorage):
	def init_tables(self):
		create_table = """
			CREATE TABLE IF NOT EXISTS chains (
				initial varchar,
				follows varchar,
				count INTEGER
			)
			"""
		self.db.execute(create_table)
		self.db.commit()

	@staticmethod
	def _wrap_initial(initial, query):
		"""
		When 'initial' is None, sqlite requires a different syntax to
		match. Patch queries accordingly.
		"""
		repl = query.replace('initial = ?', 'initial is ?')
		return repl if initial is None else query

	def update(self, initial, follows):
		lookup_q = self._wrap_initial(initial, """
			SELECT count from chains where initial = ? and follows = ?
			""")
		try:
			prior, = self.db.execute(lookup_q, [initial, follows]).fetchone()
		except Exception:
			prior = 0

		value = prior + 1
		update_q = self._wrap_initial(initial, """
			UPDATE chains SET count = ? where initial = ? and follows = ?
			""")
		res = self.db.execute(update_q, (value, initial, follows))
		if res.rowcount == 0:
			insert_q = """
				INSERT INTO chains (initial, follows, count) VALUES (?, ?, ?)
				"""
			self.db.execute(insert_q, (initial, follows, value))
		self.db.commit()

	def next(self, initial):
		search_q = self._wrap_initial(initial, """
			SELECT follows, count FROM chains WHERE initial = ?
			""")
		res = self.db.execute(search_q, [initial])
		raw_freq = dict(res.fetchall())
		return self.choose(raw_freq)

	def purge(self):
		self.db.execute('DELETE from chains')


@pmxbot.core.command()
def saysomething(rest):
	"""
	Generate a Markov Chain response based on past logs. Seed it with
	a starting word by adding that to the end, eg
	'!saysomething dowski:'
	"""
	return Chains.store.get(rest or None)


handler = pmxbot.core.ContentHandler()


@handler.decorate
def capture_message(channel, nick, rest):
	"""
	Capture messages the bot sees to enhance the Markov chains
	"""
	message = ': '.join((nick, rest))
	with contextlib.suppress(Exception):
		Chains.store.feed(message)

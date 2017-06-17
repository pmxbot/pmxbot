import random
import itertools
import abc

from more_itertools.recipes import pairwise, consume

import pmxbot.core
import pmxbot.storage


class Chains(pmxbot.storage.SelectableStorage,
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
		'begets': <array of words that follow>
	}
	"""
	collection_name = 'chains'

	def update(self, initial, follows):
		"""
		Given two words, initial then follows, associate those words
		"""
		filter = dict(_id=initial)
		oper = {'$push': {'begets': follows}}
		self.db.update(filter, oper, upsert=True)

	def next(self, initial):
		doc = self.db.find_one(dict(_id=initial))
		return random.choice(doc['begets'])


class SQLiteChains(Chains, pmxbot.storage.SQLiteStorage):
	def update(self, initial, follows):
		"stubbed"

	def next(self, initial):
		"stubbed"
		return self.term


@pmxbot.core.command()
def saysomething(rest):
	"""
	Generate a Markov Chain response based on past logs. Seed it with
	a starting word by adding that to the end, eg
	'!saysomething dowski:'
	"""
	return Chains.store.get_paragraph(rest or None)


handler = pmxbot.core.ContentHandler()
@handler.decorate
def capture_message(channel, nick, rest):
	"""
	Capture messages the bot sees to enhance the Markov chains
	"""
	message = ': '.join((nick, rest))
	Chains.store.feed(message)

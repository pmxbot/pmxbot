import random
import itertools

from more_itertools.recipes import pairwise, consume

import pmxbot.core
import pmxbot.storage


class Chains(pmxbot.storage.SelectableStorage):
	@classmethod
	def initialize(cls):
		cls.store = cls.from_URI()
		cls._finalizers.append(cls.finalize)

	@classmethod
	def finalize(cls):
		del cls.store


class MongoDBChains(Chains, pmxbot.storage.MongoDBStorage):
	"""
	Store word associations in MongoDB with documents like so:

	{
		'_id': <trigger word or None>,
		'begets': <array of words that follow>
	}
	"""
	collection_name = 'chains'

	def save_message(self, message):
		message = message.rstrip() + ' \n'
		words = message.split(' ')
		self.save_words(words)

	def save_words(self, words):
		"""
		Save these words as encountered.
		"""
		# TODO: Need to cap the network, expire old words/phrases
		initial = None,
		all_words = itertools.chain(initial, words)
		consume(itertools.starmap(self.update, pairwise(all_words)))

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

	def get_paragraph_words(self, seed=None):
		word = seed
		while True:
			word = self.next(word)
			yield word

	def get_paragraph(self, seed=None):
		words = self.get_paragraph_words(seed)
		p_words = itertools.takewhile(lambda word: word != '\n', words)
		return ' '.join(p_words)


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
	Chains.store.save_message(message)

# vim:ts=4:sw=4:noexpandtab

from __future__ import absolute_import

import threading
import random
import logging
import time
import datetime
from itertools import chain

import pmxbot.core
import pmxbot.logging
import pmxbot.quotes
import pmxbot.timing

log = logging.getLogger(__name__)

nlnl = '\n', '\n'

def new_key(key, word):
	if word == '\n': return nlnl
	else: return (key[1], word)

def markov_data_from_words(words):
	data = {}
	key = nlnl
	for word in words:
		data.setdefault(key, []).append(word)
		key = new_key(key, word)
	return data

def words_from_markov_data(data, initial_word='\n'):
	key = '\n', initial_word
	if initial_word != '\n':
		yield initial_word
	while 1:
		word = random.choice(data.get(key, nlnl))
		key = new_key(key, word)
		yield word

def words_from_file(f):
	for line in f:
		words = line.split()
		if len(words):
			for word in words:
				yield word
		else:
			yield '\n'
	yield '\n'

def words_from_logger(logger, max=100000):
	return words_from_lines(logger.get_random_logs(max))

def words_from_quotes(quotes):
	return words_from_lines(quotes)

def words_from_lines(lines):
	for line in lines:
		words = line[0].strip().lower().split()
		for word in words:
			yield word
		yield '\n'

def words_from_logger_and_quotes(logger, quotes):
	return chain(
		words_from_logger(logger),
		words_from_quotes(quotes),
		['\n'],
	)

def paragraph_from_words(words):
	result = []
	for word in words:
		if word == '\n': break
		result.append(word)
	return ' '.join(result)

class FastSayer(object):
	@classmethod
	def init_in_thread(cls):
		threading.Thread(target=cls.init_class).start()

	@classmethod
	def init_class(cls):
		log.info("Initializing FastSayer...")
		timer = pmxbot.timing.Stopwatch()
		cls._wait_for_stores(timer)
		words = words_from_logger_and_quotes(
			pmxbot.logging.Logger.store,
			pmxbot.quotes.Quotes.store,
		)
		cls.markov_data = markov_data_from_words(words)
		log.info("Done initializing FastSayer in %s.", timer.split())

	def saysomething(self, initial_word='\n'):
		return paragraph_from_words(words_from_markov_data(self.markov_data,
			initial_word))

	@classmethod
	def _wait_for_stores(cls, timer):
		while timer.elapsed < datetime.timedelta(seconds=30):
			stores_initialized = (
				hasattr(pmxbot.logging.Logger, 'store') and
				hasattr(pmxbot.quotes.Quotes, 'store')
			)
			if stores_initialized:
				break
			time.sleep(0.1)
		else:
			raise RuntimeError("Timeout waiting for stores to be initialized")

@pmxbot.core.command("saysomething")
def saysomething(client, event, channel, nick, rest):
	"""
	Generate a Markov Chain response based on past logs. Seed it with
	a starting word by adding that to the end, eg
	'!saysomething dowski:'
	"""
	sayer = FastSayer()
	if not hasattr(sayer, 'markov_data'):
		return "Sayer not yet initialized. Try again later."
	if rest:
		return sayer.saysomething(rest)
	else:
		return sayer.saysomething()

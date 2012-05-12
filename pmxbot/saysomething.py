# vim:ts=4:sw=4:noexpandtab

from __future__ import absolute_import

import random
from itertools import chain

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

def saysomething_db(db, initial_word='\n'):
	return paragraph_from_words(
			words_from_markov_data(
				markov_data_from_words(
					words_from_db(db)),
				initial_word))

class FastSayer(object):
	def __init__(self, word_factory):
		if not hasattr(self, 'markovdata'):
			words = word_factory()
			# save the markov data in the class for future instances
			self.__class__.markovdata = markov_data_from_words(words)

	def saysomething(self, initial_word='\n'):
		return paragraph_from_words(words_from_markov_data(self.markovdata, initial_word))

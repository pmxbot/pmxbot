# vim:ts=4:sw=4:noexpandtab
import random

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

def words_from_db(db):
	db.text_factory = str
	WORDS_SQL = '''SELECT message FROM logs UNION SELECT quote FROM quotes where library = 'pmx' '''
	lines = db.execute(WORDS_SQL)
	for line in lines:
		words = line[0].strip().lower().split()
		for word in words:
			yield word
		yield '\n'
	yield '\n'

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
	def __init__(self):
		self.started = False

	def startup(self, db):
		if not self.started:
			self.db = db
			self.markovdata = markov_data_from_words(
						words_from_db(db))
			self.started = True

	def saysomething(self, initial_word='\n'):
		return paragraph_from_words(words_from_markov_data(self.markovdata, initial_word))

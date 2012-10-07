# vim:ts=4:sw=4:noexpandtab
from __future__ import absolute_import

import random
import re
import warnings
try:
	import urllib.parse as urllib_quote
	import urllib.request as urllib_request
except ImportError:
	import urllib as urllib_quote
	import urllib2 as urllib_request

try:
	import wordnik.api.APIClient
	import wordnik.api.WordAPI
	import wordnik.model
except ImportError:
	warnings.warn("Wordnik failed to import")

import pmxbot.phrases

def wchoice(d):
	l = []
	for item, num in d.iteritems():
		l.extend([item] * (num*100))
	return random.choice(l)

def splitem(s):
	s = s.rstrip('?.!')
	if ':' in s:
		question, choices = s.rsplit(':', 1)
	else:
		choices = s

	c = choices.split(',')
	if ' or ' in c[-1]:
		c = c[:-1] + c[-1].split(' or ')

	c = [x.strip() for x in c]
	c = filter(None, c)
	return c

def open_url(url):
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) '
		'Gecko/20100101 Firefox/12.0'}
	req = urllib_request.Request(url, headers=headers)
	return urllib_request.urlopen(req)

def get_html(url):
	return open_url(url).read()

def_exp1 = re.compile(r"<div><span class=f>.*?</span>(.+?)</div>", re.MULTILINE)
def_exp2 = re.compile(r"Definition for.*<div class=s><div>(.+?)<", re.MULTILINE)
urbd_exp = re.compile(r"""<td class=['"]word['"]>(.+?)^</td>$(?:.+?)<div class=['"]definition['"]>(.+?)</div>""", re.MULTILINE | re.DOTALL)

def strip_tags(string):
	"""
	Remove HTML tags from a string.

	>>> strip_tags('<div>foo and <b>bar</b></div>')
	'foo and bar'
	"""
	return re.sub('<.*?>', '', string).replace('&nbsp;', ' ')

def lookup(word):
	'''
	Get a definition for a word (uses Wordnik)
	'''
	# Jason's key - do not abuse
	key = 'edc4b9b94b341eeae350e087c2e05d2f5a2a9e0478cefc6dc'
	client = wordnik.api.APIClient.APIClient(key, 'http://api.wordnik.com/v4')
	words = wordnik.api.WordAPI.WordAPI(client)
	input = wordnik.model.WordDefinitionsInput.WordDefinitionsInput()
	input.word = word
	input.limit = 1
	definitions = words.getDefinitions(input)
	if not definitions:
		return
	definition = definitions[0]
	return unicode(definition.text)
lookup.provider = 'Wordnik'

def urbanlookup(word):
	'''Gets a Urban Dictionary summary for a word.
	'''
	word = urllib_quote.quote_plus(word)
	html = get_html('http://urbandictionary.com/define.php?term=%s' % word)
	match = urbd_exp.search(html)
	if not match:
		return None, None
	word, definition = match.groups()
	definition = ' '.join(definition.replace('<br/>', '').splitlines())
	return word.strip(), definition.strip()

html_strip = re.compile(r'<[^>]+?>')
NUM_ACS = 3

def lookup_acronym(acronym):
	acronym = acronym.strip().upper()
	html = get_html('http://www.acronymfinder.com/%s.html' % acronym)
	idx = html.find('<th>Meaning</th>')
	if idx == -1:
		return None
	all = []
	for x in xrange(NUM_ACS):
		idx = html.find('%s</a>' % acronym, idx)
		idx = html.find('<td>', idx)
		edx = html.find('</td>', idx)
		ans = html[idx+4:edx]
		ans = html_strip.sub('', ans)
		all.append(ans)

	return all

def passagg(recipient='', sender=''):
	adj = random.choice(pmxbot.phrases.adjs)
	if random.randint(0,1):
		lead = ""
		trail=recipient if not recipient else ", %s" % recipient
	else:
		lead=recipient if not recipient else "%s, " % recipient
		trail=""
	start = "%s%s%s." % (lead, random.choice(pmxbot.phrases.adj_intros) % adj, trail)
	if not lead and not start[0].isupper():
		start = "%s%s" % (start[0].upper(), start[1:])
	end = random.choice(pmxbot.phrases.farewells)
	if sender:
		end = "%s, %s" % (end, sender)
	end = "%s." % end
	final = " ".join([start, end])
	return final

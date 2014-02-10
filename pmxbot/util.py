# vim:ts=4:sw=4:noexpandtab
from __future__ import absolute_import

import random
import re
import warnings

import six
import requests

try:
	import wordnik.swagger
	import wordnik.WordApi
except (ImportError, SyntaxError):
	warnings.warn("Wordnik failed to import")

import pmxbot.phrases

def wchoice(d):
	l = []
	for item, num in six.iteritems(d):
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
	c = list(filter(None, c))
	return c

def open_url(url):
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:12.0) '
		'Gecko/20100101 Firefox/12.0'}
	return requests.get(url, headers=headers)

def get_html(url):
	return open_url(url).text


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
	client = wordnik.swagger.ApiClient(key, 'http://api.wordnik.com/v4')
	words = wordnik.WordApi.WordApi(client)
	definitions = words.getDefinitions(word, limit=1)
	if not definitions:
		return
	definition = definitions[0]
	return six.text_type(definition.text)
lookup.provider = 'Wordnik'

def urban_lookup(word):
	'''
	Return a Urban Dictionary definition for a word or None if no result was
	found.
	'''
	url = "http://api.urbandictionary.com/v0/define"
	params = dict(term=word)
	resp = requests.get(url, params=params)
	resp.raise_for_status()
	res = resp.json()
	if not res['list']:
		return
	return res['list'][0]['definition']

html_strip = re.compile(r'<[^>]+?>')
NUM_ACS = 3

def lookup_acronym(acronym):
	acronym = acronym.strip().upper().replace('.','')
	html = get_html('http://www.acronymfinder.com/%s.html' % acronym)
	idx = html.find('<th>Meaning</th>')
	if idx == -1:
		return None
	all = []
	for x in range(NUM_ACS):
		idx = html.find('%s</a>' % acronym, idx)
		idx = html.find('<td>', idx)
		edx = html.find('</td>', idx)
		ans = html[idx+4:edx]
		ans = html_strip.sub('', ans)
		all.append(ans)

	return all

def emergency_complement():
	ecomp_exp = re.compile(r"""\[.*\]""", re.MULTILINE | re.DOTALL)
	compurl = 'http://emergencycompliment.com/js/compliments.js'
	comps = get_html(compurl)
	match = ecomp_exp.search(comps)
	if not match:
		return None
	complist = match.group()
	return complist


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

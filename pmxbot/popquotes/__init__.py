"""
Popular Quotes Database
"""

import pkg_resources

from ..botbase import command
from ..util import SQLiteQuotes

db_file = pkg_resources.resource_filename('pmxbot.popquotes', 'popquotes.sqlite')

def bartletts(lib, nick, qsearch):
	qs = SQLiteQuotes.from_URI('sqlite:' + db_file)
	qs.lib = lib
	qsearch = qsearch.strip()
	if nick == 'pmxbot':
		qt, i, n = qs.quoteLookup()
		if qt:
			if qt.find(':', 0, 15) > -1:
				qt = qt.split(':', 1)[1].strip()
			return qt
	else:
		qt, i, n = qs.quoteLookupWNum(qsearch)
		if qt:
			return u'(%s/%s): %s' % (i, n, qt)

@command('bender', aliases=('bend',), doc='Quote Bender, a la http://en.wikiquote.org/wiki/Futurama')
def bender(client, event, channel, nick, rest):
	return bartletts('bender', nick, rest)

@command('zoidberg', aliases=('zoid',), doc='Quote Zoidberg, a la http://en.wikiquote.org/wiki/Futurama')
def zoidberg(client, event, channel, nick, rest):
	return bartletts('zoid', nick, rest)

@command('simpsons', aliases=('simp',), doc='Quote the Simpsons, a la http://snpp.com/')
def simpsons(client, event, channel, nick, rest):
	return bartletts('simpsons', nick, rest)

@command('hal', aliases=('2001',), doc='HAL 9000')
def hal(client, event, channel, nick, rest):
	return bartletts('hal', nick, rest)

@command('grail', aliases=(), doc='I'' questing baby')
def grail(client, event, channel, nick, rest):
	return bartletts('grail', nick, rest)

@command('anchorman', aliases=(), doc='Quote Anchorman.')
def anchorman(client, event, channel, nick, rest):
	return bartletts('anchorman', nick, rest)

@command('hangover', aliases=(), doc='Quote hangover.')
def hangover(client, event, channel, nick, rest):
	return bartletts('hangover', nick, rest)

@command('R', aliases=('r',), doc='Quote the R mailing list')
def R(client, event, channel, nick, rest):
	return bartletts('R', nick, rest)

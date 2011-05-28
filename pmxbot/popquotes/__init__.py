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
	qt = bartletts('bender', nick, rest)
	if qt:	return qt

@command('zoidberg', aliases=('zoid',), doc='Quote Zoidberg, a la http://en.wikiquote.org/wiki/Futurama')
def zoidberg(client, event, channel, nick, rest):
	qt = bartletts('zoid', nick, rest)
	if qt:	return qt

@command('simpsons', aliases=('simp',), doc='Quote the Simpsons, a la http://snpp.com/')
def simpsons(client, event, channel, nick, rest):
	qt = bartletts('simpsons', nick, rest)
	if qt:	return qt

@command('hal', aliases=('2001',), doc='HAL 9000')
def hal(client, event, channel, nick, rest):
	qt = bartletts('hal', nick, rest)
	if qt:	return qt

@command('grail', aliases=(), doc='I'' questing baby')
def grail(client, event, channel, nick, rest):
	qt = bartletts('grail', nick, rest)
	if qt:	return qt

@command('anchorman', aliases=(), doc='Quote Anchorman.')
def anchorman(client, event, channel, nick, rest):
	qt = bartletts('anchorman', nick, rest)
	if qt:	return qt

@command('hangover', aliases=(), doc='Quote hangover.')
def hangover(client, event, channel, nick, rest):
	qt = bartletts('hangover', nick, rest)
	if qt:	return qt

@command('R', aliases=('r',), doc='Quote the R mailing list')
def R(client, event, channel, nick, rest):
	qt = bartletts('R', nick, rest)
	if qt:	return qt


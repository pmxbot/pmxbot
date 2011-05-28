"""
Popular Quotes Database
"""

import itertools

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

# declare all of the popquotes commands
quote_libs = (
	# name, aliases, doc, lib
	('bender', ('bend',), 'Quote Bender, a la http://en.wikiquote.org/wiki/Futurama', 'bender'),
	('zoidberg', ('zoid',), 'Quote Zoidberg, a la http://en.wikiquote.org/wiki/Futurama', 'zoid'),
	('simpsons', ('simp',), 'Quote the Simpsons, a la http://snpp.com/', 'simpsons'),
	('hal', ('2001',), 'HAL 9000', 'hal'),
	('grail', (), 'I questing baby', 'grail'),
	('anchorman', (), 'Quote Anchorman.', 'anchorman'),
	('hangover', (), 'Quote hangover.', 'hangover'),
	('R', ('r',), 'Quote the R mailing list', 'R'),
)

# create the popquotes commands per the declarations above
def make_command(name, aliases, doc, lib):
	cmd_func = lambda client, event, channel, nick, rest: bartletts(lib, nick, rest)
	cmd_func = command(name, aliases=aliases, doc=doc)(cmd_func)
	globals().update({name: cmd_func})
list(itertools.starmap(make_command, quote_libs))

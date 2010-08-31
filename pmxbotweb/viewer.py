#!/usr/bin/env python
# encoding: utf-8
# -*- coding: utf-8 -*-
import os
import cherrypy
try:
	from pysqlite2 import dbapi2 as sqlite
except ImportError:
	from sqlite3 import dbapi2 as sqlite
from random import shuffle
import cherrypy
import calendar
from jinja2 import Environment, FileSystemLoader

from cgi import escape

BASE = os.path.abspath(os.path.dirname(__file__))
jenv = Environment(loader=FileSystemLoader(os.path.join(BASE, 'templates'), encoding='utf-8'))
TIMEOUT=10.0



colors = ["06F", "900", "093", "F0C", "C30", "0C9", "666", "C90", "C36", "F60", "639", "630", "966", "69C", "039", '7e1e9c', '15b01a', '0343df', 'ff81c0', '653700', 'e50000', '029386', 'f97306', 'c20078', '75bbfd']
shuffle(colors)

def get_context():
	c = cherrypy.request.app.config['botconf']['config']
	d = {'request': cherrypy.request, 'name' : c.bot_nickname, 'config' : c, 'base' : c.web_base, }
	try:
		d['logo'] = c.logo
	except AttributeError:
		d['logo'] = ''
	return d

def make_anchor(line):
	return "%s.%s" % (line[0].replace(':', '.'), line[1])


th_map = {1 : 'st', 2 : 'nd', 3 : 'rd'}
def th_it(num):
	if num in range(11, 14):
		end = 'th'
	elif num % 10 in th_map:
		end = th_map[num % 10]
	else:
		end = 'th'
	return '%s%s' % (num, end)

def pmon(month):
	year, month = month.split('-')
	return '%s, %s' % (calendar.month_name[int(month)], year)

def pday(dayfmt):
	year, month, day = map(int, dayfmt.split('-'))
	return '%s the %s' % (calendar.day_name[calendar.weekday(year, month, day)], 
	th_it(day))

rev_month = {}
for x in xrange(1, 13):
	rev_month[calendar.month_name[x]] = x

def sort_month_key(m):
	parts = m.split(',')
	parts[0] = rev_month[parts[0]]
	return parts[1], parts[0]


class ChannelPage(object):
	def default(self, channel):
		page = jenv.get_template('channel.html')
		dbfile = cherrypy.request.app.config['db']['database']
		db = sqlite.connect(dbfile, isolation_level=None, timeout=TIMEOUT)
		context = get_context()
		CHANNEL_DAYS_SQL = 'select distinct date(datetime) from logs where channel = ?'
		contents = [x[0] for x in db.execute(CHANNEL_DAYS_SQL, [channel])]
		months = {}
		for fn in sorted(contents, reverse=True):
			mon_des, day = fn.rsplit('-', 1)
			months.setdefault(pmon(mon_des), []).append((pday(fn), fn))
		context['months'] = sorted(months.items(), key=lambda v: sort_month_key(v[0]),
		reverse=True) 
		context['channel'] = channel
		return page.render(**context).encode('utf-8')
	default.exposed = True

class DayPage(object):
	def default(self, channel, day):
		page = jenv.get_template('day.html')
		dbfile = cherrypy.request.app.config['db']['database']
		db = sqlite.connect(dbfile, isolation_level=None, timeout=TIMEOUT)
		context = get_context()
		#db.text_factory = lambda x: unicode(x, "utf-8", "ignore")
		DAY_DETAIL_SQL = 'SELECT time(datetime), nick, message from logs where channel = ? and date(datetime) = ? order by datetime'
		day_logs = db.execute(DAY_DETAIL_SQL, [channel, day])
		data = [(t, n, make_anchor((t, n)), escape(m)) for (t,n,m) in day_logs]
		usernames = [x[1] for x in data]
		color_map = {}
		clrs = colors[:]
		for u in usernames:
			if u not in color_map:
				try:
					color = clrs.pop(0)
				except IndexError:
					color = "000"
				color_map[u] = color
		context['color_map'] = color_map
		context['history'] = data
		context['channel'] = channel
		context['pdate'] = "%s of %s" % (pday(day), pmon(day.rsplit('-', 1)[0]))
		return page.render(**context).encode('utf-8')
	default.exposed = True


def karmaList(db, select=0):
	KARMIC_VALUES_SQL = 'SELECT karmaid, karmavalue from karma_values order by karmavalue desc'
	KARMA_KEYS_SQL= 'SELECT karmakey from karma_keys where karmaid = ?'

	karmalist = db.execute(KARMIC_VALUES_SQL).fetchall()
	karmalist.sort(key=lambda x: int(x[1]), reverse=True)
	if select > 0:
		selected = karmalist[:select]
	elif select < 0:
		selected = karmalist[select:]
	else:
		selected = karmalist
	keysandkarma = []
	for karmaid, value in selected:
		keys = ', '.join([x[0] for x in db.execute(KARMA_KEYS_SQL, [karmaid])])
		keysandkarma.append((keys, value))
	return keysandkarma

class KarmaPage(object):
	def default(self, term=""):
		page = jenv.get_template('karma.html')
		context = get_context()
		dbfile = cherrypy.request.app.config['db']['database']
		db = sqlite.connect(dbfile, isolation_level=None, timeout=TIMEOUT)
		term = term.strip()
		if term:
			context['lookup'] = []
			context['term'] = term
			KARMA_SEARCH_SQL = "SELECT distinct karmaid from karma_keys where karmakey like ? "
			KARMA_VALUE_SQL = "SELECT karmavalue from karma_values where karmaid = ?"
			KARMA_KEYS_SQL = "SELECT karmakey from karma_keys where karmaid = ?"
			matches = db.execute(KARMA_SEARCH_SQL, ['%%%s%%' % term])
			KARMA_VALUE_SQL = "SELECT karmavalue from karma_values where karmaid = ?"
			for (id,) in matches:
				karmavalue = db.execute(KARMA_VALUE_SQL, [id]).fetchall()[0][0]
				names = db.execute(KARMA_KEYS_SQL, [id]).fetchall()
				names = sorted([x[0] for x in names])
				context['lookup'].append((', '.join(names), karmavalue))
			if not context['lookup']:
				context['lookup'].append(('NO RESULTS FOUND', ''))
		context['top100'] = karmaList(db, 100)
		context['bottom100'] = karmaList(db, -100)
		return page.render(**context).encode('utf-8')
	default.exposed = True

def search_logs(term, db):
	terms = term.strip().split()

	SEARCH_SQL = 'SELECT id, date(datetime), time(datetime), datetime, channel, nick, message FROM logs WHERE %s' % (' AND '.join(["message like '%%%s%%'" % x for x in terms]))

	matches = []
	alllines = []
	search_res = db.execute(SEARCH_SQL).fetchall()
	for id, date, time, dt, channel, nick, message in search_res:
			line = (time, nick, message)
			if line in alllines:
				continue
			prev2 = db.execute('SELECT time(datetime), nick, message from logs where channel = ? and datetime < ? order by datetime desc limit 2', [channel, dt])
			next2 = db.execute('SELECT time(datetime), nick, message from logs where channel = ? and datetime > ? order by datetime asc limit 2', [channel, dt])
			lines = prev2.fetchall() + [line] + next2.fetchall()
			marker = make_anchor(line)
			matches.append((channel, date, marker, lines))
			alllines.extend(lines)
	return matches		

class SearchPage(object):
	def default(self, term=''):
		page = jenv.get_template('search.html')
		context = get_context()
		dbfile = cherrypy.request.app.config['db']['database']
		db = sqlite.connect(dbfile, isolation_level=None, timeout=TIMEOUT)
		db.text_factory = lambda x: unicode(x, "utf-8", "ignore")
	
		if not term:
			raise cherrypy.HTTPRedirect(cherrypy.request.base)
		results = sorted(search_logs(term, db), key=lambda x: x[1], reverse=True)
		context['search_results'] = results
		context['num_results'] = len(results)
		context['term'] = term
		return page.render(**context).encode('utf-8')
	default.exposed = True
		
	
class HelpPage(object):
	def __init__(self):
		self.run = False
		
	def default(self):
		page = jenv.get_template('help.html')
		context = get_context()
		if not self.run:
			self.commands = []
			self.contains = []
			import pmxbot.pmxbot as p
			p.run(configInput = context['config'], start=False)
			for typ, name, f, doc, channels, exclude, rate, priority in sorted(p._handler_registry, key=lambda x: x[1]):
				if typ == 'command':
					aliases = sorted([x[1] for x in p._handler_registry if x[0] == 'alias' and x[2] == f])
					self.commands.append((name, doc, aliases))
				elif typ == 'contains':
					self.contains.append((name, doc))
			self.run = True
		context['commands'] = self.commands
		context['contains'] = self.contains
		return page.render(**context).encode('utf-8')
	default.exposed = True
	

class PmxbotPages(object):
	channel = ChannelPage()
	day = DayPage()
	karma = KarmaPage()
	search = SearchPage()
	help = HelpPage()
	
	def default(self):
		page = jenv.get_template('index.html')
		dbfile = cherrypy.request.app.config['db']['database']
		db = sqlite.connect(dbfile, isolation_level=None, timeout=TIMEOUT)
		context = get_context()
		CHANNEL_LIST_SQL = "SELECT distinct channel from logs order by lower(channel)"
		LAST_LINE_SQL = '''SELECT strftime("%Y-%m-%d %H:%M", datetime), date(datetime), time(datetime), nick, message from logs where channel = ? order by datetime desc limit 1'''
		chans = []
		for chan in db.execute(CHANNEL_LIST_SQL).fetchall():
			chan = chan[0]
			last = list(db.execute(LAST_LINE_SQL, [chan]).fetchone())
			last[-1] = escape(last[-1][:75])
			last.append(make_anchor((last[2], last[3])))
			chans.append([chan] + last)
		context['chans'] = chans
		return page.render(**context).encode('utf-8')
	default.exposed = True
		
		
		
		
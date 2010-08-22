# vim:ts=4:sw=4:noexpandtab

import sys
import ircbot
import datetime
from sqlite3 import dbapi2 as sqlite
import os
import traceback
import time
import re
import feedparser
import socket
import random

from threading import Thread

exists = os.path.exists
pjoin = os.path.join

LOGWARN_EVERY = 60 # seconds
LOGWARN_MESSAGE = \
'''PRIVACY INFORMATION: LOGGING IS ENABLED!!
  
The following channels are logged are being logged to provide a 
convenient, searchable archive of conversation histories:
%s
'''
warn_history = {}

class NoLog(object): pass

class LoggingCommandBot(ircbot.SingleServerIRCBot):
	def __init__(self, repo, server, port, nickname, channels, nolog_channels=None, feed_interval=60, feeds=[]):
		ircbot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		nolog_channels = nolog_channels or []
		self.nickname = nickname
		self._channels = channels + nolog_channels
		self._nolog = set(('#' + c if not c.startswith('#') else c) for c in nolog_channels)
		setup_repo(repo)
		self._repo = repo
		self._nickname = nickname
		self._feed_interval = feed_interval
		self._feeds = feeds

	def on_welcome(self, c, e):
		for channel in self._channels:
			if not channel.startswith('#'):
				channel = '#' + channel
			c.join(channel)
		for action in _delay_registry:
			name, channel, howlong, func, args, doc = action 
			c.execute_delayed(howlong, self.background_runner, arguments=(c, e, channel, func, args))
		c.execute_delayed(30, self.feed_parse, arguments=(c, e, self._feed_interval, self._feeds))

	def on_join(self, c, e):
		nick = e.source().split('!', 1)[0]
		channel = e.target()
		if channel in self._nolog or nick == self._nickname:
			return
		if time.time() - warn_history.get(nick, 0) > LOGWARN_EVERY:
			warn_history[nick] = time.time()
			msg = LOGWARN_MESSAGE % (', '.join(['#'+chan for chan in self._channels if '#'+chan not in self._nolog]))
			for line in msg.splitlines():
				c.notice(nick, line)
	
	def on_pubmsg(self, c, e):
		msg = (''.join(e.arguments())).decode('utf8', 'ignore')
		nick = e.source().split('!', 1)[0]
		channel = e.target()
		if msg > '':
			if channel not in self._nolog:
				logger.message(channel, nick, msg)
			self.handle_action(c, e, channel, nick, msg)
			
	
	def on_privmsg(self, c, e):
		msg = (''.join(e.arguments())).decode('utf8', 'ignore')
		nick = e.source().split('!', 1)[0]
		channel = nick
		if msg > '':
			self.handle_action(c, e, channel, nick, msg)

	def on_invite(self, c, e):
		nick = e.source().split('!', 1)[0]
		channel = e.arguments()[0]
		if channel.startswith('#'):
			channel = channel[1:]
		self._channels.append(channel)
		channel = '#' + channel
		self._nolog.add(channel)
		time.sleep(1)
		c.join(channel)
		time.sleep(1)
		c.privmsg(channel, "You summoned me, master %s?" % nick)
		
	def background_runner(self, c, e, channel, func, args):
		"""
		Wrapper to run scheduled type tasks cleanly.
		"""
		secret = False
		res = func(c, e, *args)
		def out(s):
			if s.startswith('/me '):
				c.action(channel, s.split(' ', 1)[-1].lstrip())
			else:
				c.privmsg(channel, s)
				if channel not in self._nolog and not secret:
					logger.message(channel, self._nickname, s)
		if res:
			if isinstance(res, basestring):
				out(res)
			else:
				for item in res:
					if item == NoLog:
						secret = True
					else:
						out(item)


	def handle_action(self, c, e, channel, nick, msg):
		lc_msg = msg.lower()
		lc_cmd = msg.split()[0]
		res = None
		secret = False
		for typ, name, f, doc, channels, exclude, rate in _handler_registry:
			if typ in ('command', 'alias') and lc_cmd == '!%s' % name:
				if ' ' in msg:
					msg = msg.split(' ', 1)[-1].lstrip()
				else:
					msg = ''
				try:
					res = f(c, e, channel, nick, msg)
				except Exception, e:
					res = "DO NOT TRY TO BREAK PMXBOT!!!"
					res += '\n%s' % e
					traceback.print_exc()
				break
			elif typ in('contains', '#') and name in lc_msg:
				if channels and (channel not in channels \
				or (channels == "logged" and channel in self._nolog) \
				or (channels == "unlogged" and channel not in self._nolog)):
					continue
				if exclude and (channel not in exclude \
				or (exclude == "logged" and channel in self._nolog) \
				or (exclude == "unlogged" and channel not in self._nolog)):
					continue
				if random.random() <= rate:
					try:
						res = f(c, e, channel, nick, msg)
					except Exception, e:
						res = "DO NOT TRY TO BREAK PMXBOT!!!"
						res += '\n%s' % e
						traceback.print_exc()
					break
		def out(s):
			if s.startswith('/me '):
				c.action(channel, s.split(' ', 1)[-1].lstrip())
			else:
				c.privmsg(channel, s)
				if channel not in self._nolog and not secret:
					logger.message(channel, self._nickname, s)
		if res:
			if isinstance(res, basestring):
				out(res)
			else:
				for item in res:
					if item == NoLog:
						secret = True
					else:
						out(item)



	def feed_parse(self, c, e, interval, feeds):
		"""
		This is used to parse RSS feeds and spit out new articles at
		regular intervals in the relevant channels.
		"""
		def check_single_feed(this_feed):
			"""
			This function is run in a new thread for each feed, so we don't
			lock up the main thread while checking (potentially slow) RSS feeds
			"""
			socket.setdefaulttimeout(20)
			outputs = []
			NEWLY_SEEN = []
			try:
				feed = feedparser.parse(this_feed['url'])
			except:
				pass
			for entry in feed['entries']:
				if entry.has_key('id'):
					id = entry['id']
				elif entry.has_key('link'):
					id = entry['link']
				elif entry.has_key('title'):
					id = entry['title']
				else:
					continue #this is bad...
				#If this is google let's overwrite
				if 'google.com' in this_feed['url'].lower():
					GNEWS_RE = re.compile(r'[?&]url=(.+?)[&$]', re.IGNORECASE)
					try:
						id = GNEWS_RE.findall(entry['link'])[0]
					except:
						pass
				if id in FEED_SEEN:
					continue
				FEED_SEEN.append(id)
				NEWLY_SEEN.append(id)
				if ' by ' in entry['title']: #We don't need to add the author
					out = '%s' % entry['title']
				else:
					try:
						out = '%s by %s' % (entry['title'], entry['author'])
					except KeyError:
						out = '%s' % entry['title']
				outputs.append(out)
			if outputs:
				c.execute_delayed(20, self.add_feed_entries, arguments=(NEWLY_SEEN,))
				txt = 'News from %s %s : %s' % (this_feed['name'], this_feed['linkurl'], ' || '.join(outputs[:10]))
				txt = txt.encode('utf-8')
				c.privmsg(this_feed['channel'], txt)
		#end of check_single_feed
		db = logger.db
		try:
			res = db.execute('select key from feed_seen')
			FEED_SEEN = [x[0] for x in res]
		except:
			db.execute('CREATE TABLE feed_seen (key varchar)')
			db.execute('CREATE INDEX IF NOT EXISTS ix_feed_seen_key ON feed_seen (key)')
			db.commit()
			FEED_SEEN = []
		for feed in feeds:
			t = Thread(target=check_single_feed, args=[feed])
			t.setDaemon(True)
			t.start()
		c.execute_delayed(interval, self.feed_parse, arguments=(c, e, interval, feeds))

	def add_feed_entries(self, entries):
		"""
		This is to let the main pmxbot thread update the database and avoid
		issues with accessing sqlite from multiple threads
		"""
		logger.db.executemany('INSERT INTO feed_seen (key) values (?)', [(x,) for x in entries])
		logger.db.commit()

_handler_registry = []
_handler_sort_order = {'command' : 1, 'alias' : 2, 'contains' : 3}
_delay_registry = []

def contains(name, channels=None, exclude=None, rate=1.0, priority=1, doc=None):
	def deco(func):
		if name == '#' or priority == 2:
			_handler_registry.append(('contains', name.lower(), func, doc, channels, exclude, rate))
		else:
			_handler_registry.append(('contains', name.lower(), func, doc, channels, exclude, rate))
		_handler_registry.sort(key=lambda x: (_handler_sort_order[x[0]], 0-len(x[1]), x[1]))
		return func
	return deco

def command(name, aliases=None, doc=None):
	def deco(func):
		_handler_registry.append(('command', name.lower(), func, doc, None, None, None))
		if aliases:
			for a in aliases:
				if not a.endswith(' '):
					pass
					#a += ' '
				_handler_registry.append(('alias', a, func, doc, None, None, None))
		_handler_registry.sort(key=lambda x: (_handler_sort_order[x[0]], 0-len(x[1]), x[1]))
		return func
	return deco
	
def execdelay(name, channel, howlong, args=[], doc=None):
	def deco(func):
		_delay_registry.append((name.lower(), channel, howlong, func, args, doc))
		return func
	return deco

class Logger(object):

	def __init__(self, repo):
		self.repo = repo
		self.dbfn = pjoin(self.repo, 'pmxbot.sqlite')
		self.db = sqlite.connect(self.dbfn)
		LOG_CREATE_SQL = '''
		CREATE TABLE IF NOT EXISTS logs (
			id INTEGER NOT NULL,
			datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
			channel VARCHAR NOT NULL,
			nick VARCHAR NOT NULL,
			message TEXT,
			PRIMARY KEY (id) )
		'''
		INDEX_DTC_CREATE_SQL = 'CREATE INDEX IF NOT EXISTS ix_logs_datetime_channel ON logs (datetime, channel)'
		INDEX_DT_CREATE_SQL = 'CREATE INDEX IF NOT EXISTS ix_logs_datetime ON logs (datetime desc)'
		self.db.execute(LOG_CREATE_SQL)
		self.db.execute(INDEX_DTC_CREATE_SQL)
		self.db.execute(INDEX_DT_CREATE_SQL)
		self.db.commit()
		
	def message(self, channel, nick, msg):
		INSERT_LOG_SQL = 'INSERT INTO logs (datetime, channel, nick, message) VALUES (?, ?, ?, ?)'
		now = datetime.datetime.now()
		channel = channel.replace('#', '')
		self.db.execute(INSERT_LOG_SQL, [now, channel.lower(), nick, msg])
		self.db.commit()

	def last_seen(self, nick):
		FIND_LAST_SQL = 'SELECT datetime, channel FROM logs WHERE nick = ? ORDER BY datetime DESC LIMIT 1'
		res = list(self.db.execute(FIND_LAST_SQL, [nick]))
		self.db.commit()
		if not res:
			return None
		else:
			return res[0]

	def strike(self, channel, nick, count):
		count += 1 # let's get rid of 'the last !strike' too!
		if count > 20:
			count = 20
		LAST_N_IDS_SQL = '''select channel, nick, id from logs where channel = ? and nick = ? and date(datetime) = date('now','localtime') order by datetime desc limit ?'''
		DELETE_LINE_SQL = '''delete from logs where channel = ? and nick = ? and id = ?'''
		channel = channel.replace('#', '')
		
		ids_to_delete = self.db.execute(LAST_N_IDS_SQL, [channel.lower(), nick, count]).fetchall()
		if ids_to_delete:
			deleted = self.db.executemany(DELETE_LINE_SQL, ids_to_delete)
			self.db.commit()
			rows_deleted = deleted.rowcount - 1
		else:
			rows_deleted = 0
		rows_deleted = deleted.rowcount - 1
		self.db.commit()
		return rows_deleted
		

logger = None

def setup_repo(path):
	global logger
	logger = Logger(path)

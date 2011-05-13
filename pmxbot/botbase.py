# vim:ts=4:sw=4:noexpandtab

import sys
import ircbot
import datetime
import os
import traceback
import time
import re
import itertools
import operator
import feedparser
import socket
import random

from .storage import SQLiteStorage, MongoDBStorage
from . import util
from .logging import init_logger

from py25compat import next

exists = os.path.exists

LOGWARN_EVERY = 60 # seconds
LOGWARN_MESSAGE = \
'''PRIVACY INFORMATION: LOGGING IS ENABLED!!
  
The following channels are logged are being logged to provide a 
convenient, searchable archive of conversation histories:
%s
'''
warn_history = {}
logger = None

class NoLog(object): pass

class LoggingCommandBot(ircbot.SingleServerIRCBot):
	def __init__(self, repo, server, port, nickname, channels, nolog_channels=None, feed_interval=60, feeds=[]):
		ircbot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
		nolog_channels = nolog_channels or []
		self.nickname = nickname
		self._channels = channels + nolog_channels
		self._nolog = set(('#' + c if not c.startswith('#') else c) for c in nolog_channels)
		self._repo = repo
		globals().update(logger=init_logger(repo))
		util.init_karma(repo)
		util.init_quotes(repo, 'pmx')
		self._nickname = nickname
		self._feed_interval = feed_interval
		self._feeds = feeds

	def out(self, channel, s, log=True):
		if s.startswith('/me '):
			self.c.action(channel, s.encode('utf-8').split(' ', 1)[-1].lstrip())
		else:
			self.c.privmsg(channel, s.encode('utf-8'))
			if channel in self._channels and channel not in self._nolog and log:
				logger.message(channel, self._nickname, s)

	def _schedule_at(self, name, channel, when, func, args, doc):
		if type(when) == datetime.datetime:
			difference = when - datetime.datetime.now()
			repeat=False
		elif type(when) == datetime.date:
			whendt = datetime.datetime.fromordinal(tomorrow.toordinal())
			difference = whendt - datetime.datetime.now()
			repeat=False
		elif type(when) == datetime.time:
			if when > datetime.datetime.now().time():
				nextday = datetime.date.today()
			else:
				nextday = datetime.date.today() + datetime.timedelta(days=1)
			whendt = datetime.datetime.combine(nextday, when)
			difference = whendt - datetime.datetime.now()
			repeat=True
		howlong = (difference.days * 86400) + difference.seconds
		if howlong > 0:
			self.c.execute_delayed(howlong, self.background_runner, arguments=(self.c, channel, func, args, None, when, repeat))

	def on_welcome(self, c, e):
		self.c = c
		for channel in self._channels:
			if not channel.startswith('#'):
				channel = '#' + channel
			c.join(channel)
		for name, channel, howlong, func, args, doc, repeat in _delay_registry:
			self.c.execute_delayed(howlong, self.background_runner, arguments=(self.c, channel, func, args, howlong, None, repeat))
		for action in _at_registry:
			self._schedule_at(*action)
		c.execute_delayed(30, self.feed_parse, arguments=(c, e, self._feed_interval, self._feeds))

	def on_join(self, c, e):
		nick = e.source().split('!', 1)[0]
		channel = e.target()
		if channel in self._nolog or nick == self._nickname:
			return
		if time.time() - warn_history.get(nick, 0) > LOGWARN_EVERY:
			warn_history[nick] = time.time()
			msg = LOGWARN_MESSAGE % (', '.join([chan for chan in sorted(self._channels) if chan not in self._nolog]))
			for line in msg.splitlines():
				c.notice(nick, line)
	
	def on_pubmsg(self, c, e):
		msg = (''.join(e.arguments())).decode('utf8', 'ignore')
		nick = e.source().split('!', 1)[0]
		channel = e.target()
		if msg.strip() > '':
			if channel not in self._nolog:
				logger.message(channel, nick, msg)
			self.handle_action(c, e, channel, nick, msg)
			
	
	def on_privmsg(self, c, e):
		msg = (''.join(e.arguments())).decode('utf8', 'ignore')
		nick = e.source().split('!', 1)[0]
		channel = nick
		if msg.strip() > '':
			self.handle_action(c, e, channel, nick, msg)

	def on_invite(self, c, e):
		nick = e.source().split('!', 1)[0]
		channel = e.arguments()[0]
		if not channel.startswith('#'):
			channel = '#' + channel
		self._channels.append(channel)
		self._nolog.add(channel)
		time.sleep(1)
		c.join(channel)
		time.sleep(1)
		c.privmsg(channel, "You summoned me, master %s?" % nick)
		
	def background_runner(self, c, channel, func, args, howlong, when, repeat):
		"""
		Wrapper to run scheduled type tasks cleanly.
		"""
		try:
			secret = False
			res = func(c, None, *args)
			if res:
				if isinstance(res, basestring):
					self.out(channel, res)
				else:
					for item in res:
						if item == NoLog:
							secret = True
						else:
							self.out(channel, item, not secret)
		except:
			print datetime.datetime.now(), "Error in bacakground runner for ", func
			traceback.print_exc()
		if repeat and howlong:
			self.c.execute_delayed(howlong, self.background_runner, arguments=(self.c, channel, func, args, howlong, None, repeat))
		elif repeat and when:
			self._schedule_at('rescheduled task', channel, when, func, args, '')


	def handle_action(self, c, e, channel, nick, msg):
		lc_msg = msg.lower()
		lc_cmd = msg.split()[0]
		res = None
		secret = False
		for typ, name, f, doc, channels, exclude, rate, priority in _handler_registry:
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
					print datetime.datetime.now(), "Error with command %s" % name
					traceback.print_exc()
				break
			elif typ in('contains', '#') and name in lc_msg:
				if (not channels and not exclude) \
				or channel in channels \
				or (exclude and channel not in exclude) \
				or (channels == 'logged' and channel in self._channels and channel not in self._nolog) \
				or (channels == "unlogged" and channel in self._nolog) \
				or (exclude == "logged" and channel in self._nolog) \
				or (exclude == "unlogged" and channel in self._channels and channel not in self._nolog):
					if random.random() <= rate:
						try:
							res = f(c, e, channel, nick, msg)
						except Exception, e:
							print datetime.datetime.now(), "Error with contains  %s" % name
							traceback.print_exc()
						break
		if res:
			if isinstance(res, basestring):
				self.out(channel, res)
			else:
				for item in res:
					if item == NoLog:
						secret = True
					else:
						self.out(channel, item, not secret)



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
				c.execute_delayed(60, self.add_feed_entries, arguments=(NEWLY_SEEN,))
				txt = 'News from %s %s : %s' % (this_feed['name'], this_feed['linkurl'], ' || '.join(outputs[:10]))
				txt = txt.encode('utf-8')
				c.privmsg(this_feed['channel'], txt)
		#end of check_single_feed
		db = get_feedparser_db(self._repo)
		FEED_SEEN = db.get_seen_feeds()
		for feed in feeds:
			check_single_feed(feed)
		c.execute_delayed(interval, self.feed_parse, arguments=(c, e, interval, feeds))

	def add_feed_entries(self, entries):
		"""
		This is to let the main pmxbot thread update the database and avoid
		issues with accessing sqlite from multiple threads
		"""
		try:
			db = get_feedparser_db(self._repo)
			db.add_entries(entries)
		except Exception, e:
			print datetime.datetime.now(), "Oh crap, couldn't add_feed_entries"
			print e


_handler_registry = []
_handler_sort_order = {'command' : 1, 'alias' : 2, 'contains' : 4}
_delay_registry = []
_at_registry = []


def contains(name, channels=None, exclude=None, rate=1.0, priority=1, doc=None):
	def deco(func):
		try:
			priority
		except UnboundLocalError:
			priority=1
		if name == '#':
			priority += 1
		_handler_registry.append(('contains', name.lower(), func, doc, channels, exclude, rate, priority))
		_handler_registry.sort(key=lambda x: (_handler_sort_order[x[0]], 0-x[7], 0-len(x[1])))
		return func
	return deco

def command(name, aliases=[], doc=None):
	def deco(func):
		_handler_registry.append(('command', name.lower(), func, doc, None, None, None, 5))
		for a in aliases:
			_handler_registry.append(('alias', a, func, doc, None, None, None, 4))
		_handler_registry.sort(key=lambda x: (_handler_sort_order[x[0]], 0-x[7], 0-len(x[1])))
		return func
	return deco
	
def execdelay(name, channel, howlong, args=[], doc=None, repeat=False):
	def deco(func):
		_delay_registry.append((name.lower(), channel, howlong, func, args, doc, repeat))
		return func
	return deco
	
	
def execat(name, channel, when, args=[], doc=None):
	def deco(func):
		if type(when) not in (datetime.date, datetime.datetime, datetime.time):
			raise TypeError
		_at_registry.append((name.lower(), channel, when, func, args, doc))
		return func
	return deco

class FeedparserDB(SQLiteStorage):
	def init_tables(self):
		self.db.execute("CREATE TABLE IF NOT EXISTS feed_seen (key varchar)")
		self.db.execute('CREATE INDEX IF NOT EXISTS ix_feed_seen_key ON feed_seen (key)')
		self.db.commit()

	def get_seen_feeds(self):
		return [row[0] for row in self.db.execute('select key from feed_seen')]

	def add_entries(self, entries):
		self.db.executemany('INSERT INTO feed_seen (key) values (?)', [(x,) for x in entries])
		self.db.commit()

class MongoDBFeedparserDB(MongoDBStorage):
	collection_name = 'feed history'
	def get_seen_feeds(self):
		return [row['key'] for row in self.db.find()]

	def add_entries(self, entries):
		for entry in entries:
			self.db.insert(dict(key=entry))
		

def get_feedparser_db(uri):
	class_ = MongoDBFeedparserDB if uri.startswith('mongodb://') else FeedparserDB
	return class_(uri)

# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:noexpandtab
# c-basic-indent: 4; tab-width: 4; indent-tabs-mode: true;
from __future__ import absolute_import

import socket
import re
import datetime

import feedparser

from . import storage

class FeedparserSupport(object):
	"""
	Mix-in for a bot class to give feedparser support.
	"""

	def __init__(self, feed_interval=60, feeds=[]):
		self._feed_interval = feed_interval
		self._feeds = feeds

	def on_welcome(self, c, e):
		if self._feeds:
			# Feeds configured, check them periodically
			c.execute_delayed(30, self.feed_parse,
				arguments=(c, e, self._feed_interval, self._feeds))

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
		db = init_feedparser_db(self.db_uri)
		FEED_SEEN = db.get_seen_feeds()
		for feed in feeds:
			check_single_feed(feed)
		c.execute_delayed(interval, self.feed_parse, arguments=(c, e, interval, feeds))

	def add_feed_entries(self, entries):
		"""
		A callback to let the main pmxbot thread update the database and avoid
		issues with accessing sqlite from multiple threads
		"""
		try:
			db = init_feedparser_db(self.db_uri)
			db.add_entries(entries)
		except Exception, e:
			print datetime.datetime.now(), "Oh crap, couldn't add_feed_entries"
			print e

class FeedparserDB(storage.SelectableStorage):
	pass

class SQLiteFeedparserDB(FeedparserDB, storage.SQLiteStorage):
	def init_tables(self):
		self.db.execute("CREATE TABLE IF NOT EXISTS feed_seen (key varchar)")
		self.db.execute('CREATE INDEX IF NOT EXISTS ix_feed_seen_key ON feed_seen (key)')
		self.db.commit()

	def get_seen_feeds(self):
		return [row[0] for row in self.db.execute('select key from feed_seen')]

	def add_entries(self, entries):
		self.db.executemany('INSERT INTO feed_seen (key) values (?)', [(x,) for x in entries])
		self.db.commit()

	export_all = get_seen_feeds

class MongoDBFeedparserDB(FeedparserDB, storage.MongoDBStorage):
	collection_name = 'feed history'
	def get_seen_feeds(self):
		return [row['key'] for row in self.db.find()]

	def add_entries(self, entries):
		for entry in entries:
			self.db.insert(dict(key=entry))

	def import_(self, item):
		self.add_entries([item])

def init_feedparser_db(uri):
	return FeedparserDB.from_URI(uri)

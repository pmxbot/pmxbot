# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:noexpandtab
# c-basic-indent: 4; tab-width: 4; indent-tabs-mode: true;
from __future__ import absolute_import, print_function

import socket
import re
import datetime
import logging

import feedparser

import pmxbot
from . import core
from . import storage
from . import timing

log = logging.getLogger(__name__)

class RSSFeeds(object):
	"""
	Plugin for feedparser support.
	"""

	def __init__(self):
		self.feed_interval = pmxbot.config.feed_interval
		self.feeds = pmxbot.config.feeds
		self.store = FeedparserDB.from_URI(pmxbot.config.database)
		for feed in self.feeds:
			core.execdelay(
				name = 'feedparser',
				channel = feed['channel'],
				howlong = datetime.timedelta(minutes=self.feed_interval),
				args = [feed],
				repeat = True,
				)(self.parse_feed)
		timer = timing.Stopwatch()
		self.seen_feeds = set(self.store.get_seen_feeds())
		log.info("Loaded feed history in %s", timer.split())
		storage.SelectableStorage._finalizers.append(self.finalize)

	def finalize(self):
		del self.store

	def parse_feed(self, client, event, feed):
		"""
		Parse RSS feeds and spit out new articles at
		regular intervals in the relevant channels.
		"""
		socket.setdefaulttimeout(20)
		outputs = []
		try:
			resp = feedparser.parse(feed['url'])
		except:
			log.exception("Error retrieving feed %s", feed['url'])
		for entry in resp['entries']:
			if 'id' in entry:
				id = entry['id']
			elif 'link' in entry:
				id = entry['link']
			elif 'title' in entry:
				id = entry['title']
			else:
				log.warning("Unrecognized entry in feed from %s: %s",
					feed['url'],
					entry)
				continue
			#If this is google let's overwrite
			if 'google.com' in feed['url'].lower():
				GNEWS_RE = re.compile(r'[?&]url=(.+?)[&$]', re.IGNORECASE)
				try:
					id = GNEWS_RE.findall(entry['link'])[0]
				except:
					pass
			if not self.add_seen_feed(id):
				continue

			if ' by ' in entry['title']:
				# We don't need to add the author
				out = '%s' % entry['title']
			else:
				try:
					out = '%s by %s' % (entry['title'], entry['author'])
				except KeyError:
					out = '%s' % entry['title']
			outputs.append(out)

		if not outputs:
			return

		txt = 'News from %s %s : %s' % (feed['name'],
			feed['linkurl'], ' || '.join(outputs[:10]))
		yield core.NoLog
		yield txt

	def add_seen_feed(self, entry):
		"""
		Update the database with the new entry.
		Return True if it was a new feed and was added.
		"""
		if entry in self.seen_feeds:
			return False
		self.seen_feeds.add(entry)
		try:
			self.store.add_entries([entry])
		except Exception:
			log.exception("Unable to add seen feed")
			return False
		return True

class FeedparserDB(storage.SelectableStorage):
	pass

class SQLiteFeedparserDB(FeedparserDB, storage.SQLiteStorage):
	def init_tables(self):
		self.db.execute("CREATE TABLE IF NOT EXISTS feed_seen (key varchar)")
		self.db.execute('CREATE INDEX IF NOT EXISTS ix_feed_seen_key ON '
			'feed_seen (key)')
		self.db.commit()

	def get_seen_feeds(self):
		return [row[0]
			for row in self.db.execute('select key from feed_seen')]

	def add_entries(self, entries):
		self.db.executemany('INSERT INTO feed_seen (key) values (?)',
			[(x,) for x in entries])
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

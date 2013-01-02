# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:noexpandtab
# c-basic-indent: 4; tab-width: 4; indent-tabs-mode: true;
from __future__ import absolute_import, print_function, unicode_literals

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

class FeedHistory(set):
	"""
	A database-backed set of feed entries that have been seen before.
	"""
	def __init__(self, db_uri=None):
		super(FeedHistory, self).__init__()
		db_uri = db_uri or pmxbot.config.database
		self.store = FeedparserDB.from_URI(db_uri)
		timer = timing.Stopwatch()
		self.update(self.store.get_seen_feeds())
		log.info("Loaded feed history in %s", timer.split())
		storage.SelectableStorage._finalizers.append(self.__finalize)

	def __finalize(self):
		del self.store

	@classmethod
	def get_entry_id(cls, entry, url):
		if 'id' in entry:
			id = entry['id']
		elif 'link' in entry:
			id = entry['link']
		elif 'title' in entry:
			id = entry['title']
		else:
			raise ValueError("need id, link, or title field")

		# Special-case for Google
		if 'google.com' in url.lower():
			GNEWS_RE = re.compile(r'[?&]url=(.+?)[&$]', re.IGNORECASE)
			try:
				id = GNEWS_RE.findall(entry['link'])[0]
			except Exception:
				pass

		return id

	def add_seen_feed(self, entry, url):
		"""
		Update the database with the new feedparser entry.
		Return True if it was a new feed and was added.
		"""
		try:
			id = self.get_entry_id(entry, url)
		except ValueError:
			log.exception("Unrecognized entry in feed from %s: %s",
				url, entry)
			return False

		if id in self:
			return False
		self.add(id)
		try:
			self.store.add_entries([id])
		except Exception:
			log.exception("Unable to add seen feed")
			return False
		return True

class RSSFeeds(FeedHistory):
	"""
	Plugin for feedparser support.
	"""

	def __init__(self):
		super(RSSFeeds, self).__init__()
		self.feed_interval = pmxbot.config.feed_interval
		self.feeds = pmxbot.config.feeds
		for feed in self.feeds:
			core.execdelay(
				name = 'feedparser',
				channel = feed['channel'],
				howlong = datetime.timedelta(minutes=self.feed_interval),
				args = [feed],
				repeat = True,
				)(self.parse_feed)

	def parse_feed(self, client, event, feed):
		"""
		Parse RSS feeds and spit out new articles at
		regular intervals in the relevant channels.
		"""
		socket.setdefaulttimeout(20)
		try:
			resp = feedparser.parse(feed['url'])
		except:
			log.exception("Error retrieving feed %s", feed['url'])

		outputs = [
			self.format_entry(entry)
			for entry in resp['entries']
			if self.add_seen_feed(entry, feed['url'])
		]

		if not outputs:
			return

		txt = 'News from %s %s : %s' % (feed['name'],
			feed['linkurl'], ' || '.join(outputs[:10]))
		yield core.NoLog
		yield txt

	@staticmethod
	def format_entry(entry):
		"""
		Format the entry suitable for output (add the author if suitable).
		"""
		needs_author = ' by ' not in entry['title'] and 'author' in entry
		template = '{title} by {author}' if needs_author else '{title}'
		return template.format(**entry)


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

	def clear(self):
		"Clear all entries"
		self.db.execute('DELETE FROM feed_seen')

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

	def clear(self):
		"Clear all entries"
		self.db.remove(safe=True)

# vim:ts=4:sw=4:noexpandtab

from __future__ import absolute_import, print_function

import sys
import datetime
import traceback
import time
import random
import collections
import textwrap
import functools
import argparse
import logging

import irc.bot
import pkg_resources

import pmxbot.itertools
import pmxbot.dictlib

log = logging.getLogger('pmxbot')

class WarnHistory(dict):
	warn_every = datetime.timedelta(seconds=60)
	warn_message = textwrap.dedent("""
		PRIVACY INFORMATION: LOGGING IS ENABLED!!

		The following channels are logged are being logged to provide a
		convenient, searchable archive of conversation histories:
		{logged_channels_string}
		""").lstrip()

	def needs_warning(self, key):
		now = datetime.datetime.utcnow()
		if not key in self or self._expired(self[key], now):
			self[key] = now
			return True
		return False

	def _expired(self, last, now):
		return now - last > self.warn_every

class NoLog(object):
	@classmethod
	def secret_items(cls, items):
		"""
		Iterate over the items, and yield each item with an indicator of
		whether it should be secret or not.

		>>> tuple(NoLog.secret_items(['a', 'b', NoLog, 'c']))
		((False, 'a'), (False, 'b'), (True, 'c'))
		"""
		secret = False
		for item in items:
			if item is cls:
				secret = True
				continue
			yield secret, item

class LoggingCommandBot(irc.bot.SingleServerIRCBot):
	def __init__(self, db_uri, server, port, nickname, channels,
			password=None):
		server_list = [(server, port, password)]
		irc.bot.SingleServerIRCBot.__init__(self, server_list, nickname,
			nickname)
		self.nickname = nickname
		self._channels = channels
		self.db_uri = db_uri
		self._nickname = nickname
		self.warn_history = WarnHistory()

	def connect(self, *args, **kwargs):
		factory = irc.connection.Factory()
		factory.from_legacy_params(ssl=pmxbot.config.use_ssl)
		return irc.bot.SingleServerIRCBot.connect(self,
			connect_factory = factory, *args, **kwargs)

	def out(self, channel, s, log=True):
		func = self.c.privmsg
		if s.startswith(u'/me '):
			func = self.c.action
			s = s.split(' ', 1)[-1].lstrip()
			log = False
		func(channel, s)
		if (
				channel in self._channels
				and channel in pmxbot.config.log_channels
				and log
				):
			pmxbot.logging.Logger.store.message(channel, self._nickname, s)

	def _schedule_at(self, name, channel, when, func, args, doc):
		arguments = self.c, channel, func, args
		if isinstance(when, datetime.date):
			midnight = datetime.time(0,0)
			when = datetime.datetime.combine(when, midnight)
		if isinstance(when, datetime.datetime):
			cmd = irc.client.DelayedCommand.at_time(
				when, self.background_runner, arguments)
			self.c.irclibobj._schedule_command(cmd)
			return
		if not isinstance(when, datetime.time):
			raise ValueError("when must be datetime, date, or time")
		daily = datetime.timedelta(days=1)
		# convert when to the next datetime matching this time
		when = datetime.datetime.combine(datetime.date.today(), when)
		if when < datetime.datetime.now():
			when += daily
		cmd = irc.client.PeriodicCommandFixedDelay.at_time(
			when, daily, self.background_runner, arguments)
		self.c.irclibobj._schedule_command(cmd)

	def on_welcome(self, c, e):
		self.c = c
		for channel in self._channels:
			if not channel.startswith('#'):
				channel = '#' + channel
			c.join(channel)
		for name, channel, howlong, func, args, doc, repeat in _delay_registry:
			arguments = self.c, channel, func, args
			executor = (
				self.c.execute_every if repeat else self.c.execute_delayed)
			executor(howlong, self.background_runner, arguments)
		for action in _at_registry:
			self._schedule_at(*action)

	def on_join(self, c, e):
		nick = e.source().nick
		channel = e.target()
		for func in _join_registry:
			try:
				func(client=c, event=e, nick=nick, channel=channel)
			except Exception:
				print(datetime.datetime.now(),
					"Error in on_join handler %s" % func,
					file=sys.stderr)
				traceback.print_exc()

		if channel not in pmxbot.config.log_channels:
			return
		if nick == self._nickname:
			return
		if not self.warn_history.needs_warning(nick):
			return
		msg = self.warn_history.warn_message.format(
			logged_channels_string = ', '.join(pmxbot.config.log_channels))
		for line in msg.splitlines():
			c.notice(nick, line)

	def on_pubmsg(self, c, e):
		msg = u''.join(e.arguments())
		if not msg.strip():
			return
		nick = e.source().nick
		channel = e.target()
		if channel in pmxbot.config.log_channels:
			pmxbot.logging.Logger.store.message(channel, nick, msg)
		self.handle_action(c, e, channel, nick, msg)

	def on_privmsg(self, c, e):
		msg = u''.join(e.arguments())
		if not msg.strip():
			return
		nick = e.source().nick
		channel = nick
		self.handle_action(c, e, channel, nick, msg)

	def on_invite(self, c, e):
		nick = e.source().nick
		channel = e.arguments()[0]
		if not channel.startswith('#'):
			channel = '#' + channel
		self._channels.append(channel)
		time.sleep(1)
		c.join(channel)
		time.sleep(1)
		c.privmsg(channel, "You summoned me, master %s?" % nick)

	def _handle_output(self, channel, output):
		for secret, item in NoLog.secret_items(output):
			self.out(channel, item, not secret)

	def background_runner(self, c, channel, func, args):
		"""
		Wrapper to run scheduled type tasks cleanly.
		"""
		def on_error(exception):
			print(datetime.datetime.now(), "Error in background runner for ",
				func)
			traceback.print_exc()
		func = functools.partial(func, c, None, *args)
		self._handle_output(channel, pmxbot.itertools.trap_exceptions(
			pmxbot.itertools.generate_results(func),
			on_error))

	def _handle_exception(self, exception, **kwargs):
		expletives = ['Yikes!', 'Zoiks!', 'Ouch!']
		res = [
			"{expletive} An error occurred: {exception}".format(
				expletive=random.choice(expletives),
				**vars())
		]
		res.append('!{name} {doc}'.format(**kwargs))
		print(datetime.datetime.now(), "Error with command {type}"
			.format(**kwargs))
		traceback.print_exc()
		return res

	def handle_action(self, c, e, channel, nick, msg):
		"""Core message parser and dispatcher"""
		lc_msg = msg.lower()
		cmd, _, cmd_args = msg.partition(' ')

		messages = ()
		for handler in _handler_registry:
			typ, name, f, doc, channels, exclude, rate, priority = handler
			exception_handler = functools.partial(
				self._handle_exception,
				type = typ,
				name = name,
				doc = doc,
				)
			if typ in ('command', 'alias') and cmd.lower() == '!%s' % name:
				f = functools.partial(f, c, e, channel, nick, cmd_args)
				messages = pmxbot.itertools.trap_exceptions(
					pmxbot.itertools.generate_results(f),
					exception_handler
				)
				break
			elif typ in ('contains', '#') and name in lc_msg:
				f = functools.partial(f, c, e, channel, nick, msg)
				if (
						not channels and not exclude
						or channel in channels
						or exclude and channel not in exclude
						or channels == "logged"
							and channel in pmxbot.config.log_channels
						or channels == "unlogged"
							and channel not in pmxbot.config.log_channels
						or exclude == "logged"
							and channel not in pmxbot.config.log_channels
						or exclude == "unlogged"
							and channel in pmxbot.config.log_channels
						):
					if random.random() > rate:
						continue
					messages = pmxbot.itertools.trap_exceptions(
						pmxbot.itertools.generate_results(f),
						exception_handler
					)
					break
		self._handle_output(channel, messages)


class SilentCommandBot(LoggingCommandBot):
	"""
	A version of the bot that doesn't say anything (just logs and
	processes commands).
	"""
	def out(self, *args, **kwargs):
		"Do nothing"

	def on_join(self, *args, **kwargs):
		"Do nothing"


_handler_registry = []
_delay_registry = []
_at_registry = []
_join_registry = []

class Handler(collections.namedtuple('HandlerTuple',
	'type_ name func doc channels exclude rate priority')):
	sort_order = dict(
		# command processed before alias before contains
		command = 1,
		alias = 2,
		contains = 4,
	)
	@property
	def sort_key(self):
		return self.sort_order[self.type_], -self.priority, -len(self.name)

	def __gt__(self, other):
		return self.sort_key > other.sort_key

def contains(name, channels=None, exclude=None, rate=1.0, priority=1,
		doc=None):
	def deco(func):
		effective_priority = priority+1 if name == '#' else priority
		_handler_registry.append(Handler('contains', name.lower(), func, doc,
			channels, exclude, rate, effective_priority))
		_handler_registry.sort()
		return func
	return deco

def command(name, aliases=[], doc=None):
	def deco(func):
		_handler_registry.append(Handler('command', name.lower(), func,
			doc, None, None, None, 5))
		for a in aliases:
			_handler_registry.append(Handler('alias', a, func, doc, None,
				None, None, 4))
		_handler_registry.sort()
		return func
	return deco

def execdelay(name, channel, howlong, args=[], doc=None, repeat=False):
	def deco(func):
		_delay_registry.append((name.lower(), channel, howlong, func, args,
			doc, repeat))
		return func
	return deco

def execat(name, channel, when, args=[], doc=None):
	def deco(func):
		date_types = datetime.date, datetime.datetime, datetime.time
		if not isinstance(when, date_types):
			raise TypeError("when must be a date or time object")
		_at_registry.append((name.lower(), channel, when, func, args, doc))
		return func
	return deco

def on_join(doc=None):
	def deco(func):
		_join_registry.append(func)
		return func
	return deco

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('config', type=pmxbot.dictlib.ConfigDict.from_yaml,
		default={}, nargs='?')
	return parser.parse_args()

def run():
	initialize(get_args().config).start()

def initialize(config):
	"""
	Initialize the bot with a dictionary of config items
	"""
	pmxbot.config.update(config)
	config = pmxbot.config

	logging.basicConfig(level=logging.INFO, format="%(message)s")
	_load_library_extensions()
	if not _handler_registry:
		raise RuntimeError("No handlers registered")

	class_ = SilentCommandBot if config.silent_bot else LoggingCommandBot

	channels = config.log_channels + config.other_channels

	return class_(config.database, config.server_host, config.server_port,
		config.bot_nickname, channels=channels, password=config.password)

def _load_library_extensions():
	"""
	Locate all setuptools entry points by the name 'pmxbot_handlers'
	and initialize them.
	Any third-party library may register an entry point by adding the
	following to their setup.py::

		entry_points = {
			'pmxbot_handlers': [
				'plugin_name = mylib.mymodule:initialize_func',
			],
		},

	`plugin_name` can be anything, and is only used to display the name
	of the plugin at initialization time.
	"""
	group = 'pmxbot_handlers'
	entry_points = pkg_resources.iter_entry_points(group=group)
	for ep in entry_points:
		try:
			log.info('Loading %s', ep.name)
			init_func = ep.load()
			if callable(init_func):
				init_func()
		except Exception:
			log.exception("Error initializing plugin %s." % ep)

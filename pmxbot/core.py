# vim:ts=4:sw=4:noexpandtab

from __future__ import absolute_import, print_function

import sys
import datetime
import traceback
import time
import random
import textwrap
import functools
import argparse
import logging
import itertools
import pprint
import re

import irc.bot
import irc.client
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

class AugmentableMessage(unicode):
	"A text string which may be augmented with attributes"

	def __new__(cls, other, **kwargs):
		return super(AugmentableMessage, cls).__new__(cls, other)

	def __init__(self, other, **kwargs):
		if hasattr(other, '__dict__'):
			self.__dict__.update(vars(other))
		self.__dict__.update(**kwargs)

class NoLog(object):
	"""
	A sentinel indicating that subsequent items should not be logged.
	"""

	@classmethod
	def secret_items(cls, items):
		"""
		Iterate over the items, adding a 'secret' attribute for each item
		indicating whether it should be secret or not.

		>>> res = tuple(NoLog.secret_items(['a', 'b', NoLog, 'c']))
		>>> res
		(u'a', u'b', u'c')
		>>> [msg.secret for msg in res]
		[False, False, True]
		"""
		secret = False
		for item in items:
			if item is cls:
				secret = True
				continue
			yield AugmentableMessage(item, secret=secret)

class SwitchChannel(unicode):
	"""
	A sentinel indicating a new channel for subsequent messages.
	"""

	@classmethod
	def channel_items(cls, items, channel=None):
		"""
		Iterate over the items, augmenting each with an attribute indicating
		the target channel, defaulting to `channel`.

		>>> res = tuple(SwitchChannel.channel_items(['a', 'b',
		...  SwitchChannel('#foo'), 'c']))
		>>> res
		(u'a', u'b', u'c')
		>>> [msg.channel for msg in res]
		[None, None, u'#foo']
		"""
		for item in items:
			if isinstance(item, cls):
				channel = item
				if not channel.startswith('#'):
					channel = '#' + channel
				continue
			yield AugmentableMessage(item, channel=channel)

class LoggingCommandBot(irc.bot.SingleServerIRCBot):
	def __init__(self, server, port, nickname, channels, password=None):
		server_list = [(server, port, password)]
		irc.bot.SingleServerIRCBot.__init__(self, server_list, nickname,
			nickname)
		self.nickname = nickname
		self._channels = channels
		self._nickname = nickname
		self.warn_history = WarnHistory()

	def connect(self, *args, **kwargs):
		factory = irc.connection.Factory()
		factory.from_legacy_params(ssl=pmxbot.config.use_ssl)
		return irc.bot.SingleServerIRCBot.connect(self,
			connect_factory = factory, *args, **kwargs)

	def out(self, channel, s, log=True):
		sent = self._out(self.connection, channel, s)
		log &= (channel in self._channels
			and channel in pmxbot.config.log_channels
			and not s.startswith('/me ')
		)
		if sent and log:
			pmxbot.logging.Logger.store.message(channel, self._nickname, sent)

	@staticmethod
	def _out(conn, channel, msg):
		"""
		Transmit `msg` on irc.client.ServerConnection `conn` using
		`channel`. If `msg` looks like an action, transmit it as such.
		Suppress all exceptions (but log warnings for each).
		"""
		func = conn.privmsg
		if msg.startswith(u'/me '):
			func = conn.action
			msg = msg.split(' ', 1)[-1].lstrip()
		try:
			func(channel, msg)
			return msg
		except irc.client.MessageTooLong:
			# some messages will fail because they're too long
			log.warning("Long message could not be transmitted: %s", msg)
		except irc.client.InvalidCharacters:
			log.warning("Message contains carriage returns, "
				"which aren't allowed in IRC messages: %r", msg)
		except Exception:
			log.exception("Unhandled exception transmitting message: %r", msg)

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

	def on_welcome(self, connection, event):
		# join channels
		for channel in self._channels:
			if not channel.startswith('#'):
				channel = '#' + channel
			connection.join(channel)

		# set up delayed tasks
		for name, channel, howlong, func, args, doc, repeat in _delay_registry:
			arguments = connection, channel, func, args
			executor = (
				connection.execute_every if repeat
				else connection.execute_delayed
			)
			executor(howlong, self.background_runner, arguments)
		for action in _at_registry:
			self._schedule_at(*action)

	def on_join(self, connection, event):
		nick = event.source.nick
		channel = event.target
		for func in _join_registry:
			try:
				func(client=connection, event=event, nick=nick,
					channel=channel)
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
			connection.notice(nick, line)

	def on_pubmsg(self, connection, event):
		msg = u''.join(event.arguments)
		if not msg.strip():
			return
		nick = event.source.nick
		channel = event.target
		if channel in pmxbot.config.log_channels:
			pmxbot.logging.Logger.store.message(channel, nick, msg)
		self.handle_action(connection, event, channel, nick, msg)

	def on_privmsg(self, connection, event):
		msg = u''.join(event.arguments)
		if not msg.strip():
			return
		nick = event.source.nick
		channel = nick
		self.handle_action(connection, event, channel, nick, msg)

	def on_invite(self, connection, event):
		nick = event.source.nick
		channel = event.arguments[0]
		if not channel.startswith('#'):
			channel = '#' + channel
		self._channels.append(channel)
		time.sleep(1)
		connection.join(channel)
		time.sleep(1)
		connection.privmsg(channel, "You summoned me, master %s?" % nick)

	def _handle_output(self, channel, output):
		"""
		Given an initial channel and a sequence of messages or sentinels,
		output the messages.
		"""
		secret_items = NoLog.secret_items(output)
		channel_items = SwitchChannel.channel_items(secret_items, channel)
		for item in channel_items:
			self.out(item.channel, item, not item.secret)

	def background_runner(self, connection, channel, func, args):
		"""
		Wrapper to run scheduled type tasks cleanly.
		"""
		def on_error(exception):
			print(datetime.datetime.now(), "Error in background runner for ",
				func)
			traceback.print_exc()
		func = functools.partial(func, connection, None, *args)
		self._handle_output(channel, pmxbot.itertools.trap_exceptions(
			pmxbot.itertools.generate_results(func),
			on_error))

	def _handle_exception(self, exception, handler):
		expletives = ['Yikes!', 'Zoiks!', 'Ouch!']
		res = [
			"{expletive} An error occurred: {exception}".format(
				expletive=random.choice(expletives),
				**vars())
		]
		res.append('!{name} {doc}'.format(name=handler.name, doc=handler.doc))
		print(datetime.datetime.now(), "Error with command {handler}"
			.format(handler=handler))
		traceback.print_exc()
		return res

	def handle_action(self, connection, event, channel, nick, msg):
		"""Core message parser and dispatcher"""

		messages = ()
		matching_handlers = (
			handler for handler in _handler_registry
			if handler.match(msg, channel))
		for handler in matching_handlers:
			exception_handler = functools.partial(
				self._handle_exception,
				handler = handler,
				)
			f = functools.partial(handler.func, connection, event, channel,
				nick, handler.process(msg))
			messages = itertools.chain(messages,
				pmxbot.itertools.trap_exceptions(
					pmxbot.itertools.generate_results(f),
					exception_handler
			)	)
			if not handler.allow_chain:
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

class Handler(object):
	class_priority = 1
	"priority of this class relative to other classes, precedence to higher"

	priority = 1
	"priority relative to other handlers of this class, precedence to higher"

	allow_chain = False
	"allow subsequent handlers to also process the same message"

	def __init__(self, name, func, **kwargs):
		self.name = name
		self.func = func
		self.__dict__.update(kwargs)

	@property
	def sort_key(self):
		return -self.class_priority, -self.priority, -len(self.name)

	def __gt__(self, other):
		return self.sort_key > other.sort_key

	def match(self, message, channel):
		"""
		Return True if the message is matched by this handler.
		"""
		return False

	def process(self, message):
		return message

class ContainsHandler(Handler):
	channels = ()
	exclude = ()
	rate = 1.0
	"rate to invoke handler"
	doc = None
	class_priority = 1

	def match(self, message, channel):
		return (
			self.name in message.lower()
			and self._channel_match(channel)
			and self._rate_match()
		)

	def _channel_match(self, channel):
		return (
			not self.channels and not self.exclude
			or channel in self.channels
			or self.exclude and channel not in self.exclude
			or self.channels == "logged"
				and channel in pmxbot.config.log_channels
			or self.channels == "unlogged"
				and channel not in pmxbot.config.log_channels
			or self.exclude == "logged"
				and channel not in pmxbot.config.log_channels
			or self.exclude == "unlogged"
				and channel in pmxbot.config.log_channels
		)

	def _rate_match(self):
		return random.random() > self.rate

class CommandHandler(Handler):
	class_priority = 3

	def match(self, message, channel):
		cmd, _, cmd_args = message.partition(' ')
		return cmd.lower() == '!{name}'.format(name = self.name)

	def process(self, message):
		cmd, _, cmd_args = message.partition(' ')
		return cmd_args

class AliasHandler(CommandHandler):
	class_priority = 2

class RegexpHandler(ContainsHandler):
	class_priority = 4

	def match(self, message, channel):
		return self.pattern.search(message)

	def process(self, message):
		return self.pattern.search(message)


def contains(name, channels=(), exclude=(), rate=1.0, priority=1,
		doc=None, **kwargs):
	def deco(func):
		effective_priority = priority+1 if name == '#' else priority
		_handler_registry.append(ContainsHandler(
			name=name.lower(),
			func=func,
			doc=doc,
			channels=channels,
			exclude=exclude,
			rate=rate,
			priority=effective_priority,
			**kwargs))
		_handler_registry.sort()
		return func
	return deco

def command(name, aliases=[], doc=None):
	def deco(func):
		ch = CommandHandler(
			name=name.lower(),
			func=func,
			doc=doc,
			aliases=[],
		)
		_handler_registry.append(ch)
		for alias in aliases:
			ah = AliasHandler(
				name=alias,
				func=func,
				doc=doc)
			ch.aliases.append(ah)
			_handler_registry.append(ah)
		_handler_registry.sort()
		return func
	return deco

def regexp(name, regexp, doc=None):
	def deco(func):
		_handler_registry.append(RegexpHandler(
			name=name.lower(),
			func=func,
			doc=doc,
			pattern=re.compile(regexp, re.IGNORECASE),
		))
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
	global _bot
	_bot = initialize(get_args().config)
	_bot.start()

def _setup_logging():
	log_level = pmxbot.config['log level']
	if isinstance(log_level, basestring):
		log_level = getattr(logging, log_level.upper())
	logging.basicConfig(level=log_level, format="%(message)s")

def initialize(config):
	"""
	Initialize the bot with a dictionary of config items
	"""
	pmxbot.config.update(config)
	config = pmxbot.config

	_setup_logging()
	_load_library_extensions()
	if not _handler_registry:
		raise RuntimeError("No handlers registered")

	class_ = SilentCommandBot if config.silent_bot else LoggingCommandBot

	channels = config.log_channels + config.other_channels

	log.info('Running with config')
	log.info(pprint.pformat(config))

	return class_(config.server_host, config.server_port,
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

# vim:ts=4:sw=4:noexpandtab

from __future__ import absolute_import, print_function, unicode_literals

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
import numbers

import six
import irc.bot
import irc.client
import irc.schedule
import pkg_resources
from jaraco import dateutil
from jaraco.util.itertools import always_iterable

import pmxbot.itertools
import pmxbot.dictlib
import pmxbot.buffer

log = logging.getLogger('pmxbot')

class WarnHistory(dict):
	warn_every = datetime.timedelta(seconds=60)
	warn_message = textwrap.dedent("""
		PRIVACY INFORMATION: LOGGING IS ENABLED!!

		The following channels are being logged to provide a
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

class AugmentableMessage(six.text_type):
	"""
	A text string which may be augmented with attributes

	>>> msg = AugmentableMessage('foo', bar='baz')
	>>> msg == 'foo'
	True
	>>> msg.bar == 'baz'
	True
	"""

	def __new__(cls, other, **kwargs):
		return super(AugmentableMessage, cls).__new__(cls, other)

	def __init__(self, other, **kwargs):
		if hasattr(other, '__dict__'):
			self.__dict__.update(vars(other))
		self.__dict__.update(**kwargs)

class Sentinel(object):
	"""
	A base Sentinel object which can be injected into a series of messages to
	alter the properties of subsequent messages.
	"""

	@classmethod
	def augment_items(cls, items, **defaults):
		"""
		Iterate over the items, keeping a adding properties as supplied by
		Sentinel objects encountered.

		>>> from more_itertools.recipes import consume
		>>> res = Sentinel.augment_items(['a', 'b', NoLog, 'c'], secret=False)
		>>> res = tuple(res)
		>>> consume(map(print, res))
		a
		b
		c
		>>> [msg.secret for msg in res]
		[False, False, True]

		>>> msgs = ['a', NoLog, 'b', SwitchChannel('#foo'), 'c']
		>>> res = Sentinel.augment_items(msgs, secret=False, channel=None)
		>>> res = tuple(res)
		>>> consume(map(print, res))
		a
		b
		c
		>>> [msg.channel for msg in res] == [None, None, '#foo']
		True
		>>> [msg.secret for msg in res]
		[False, True, True]

		>>> res = tuple(Sentinel.augment_items(msgs, channel='#default', secret=False))
		>>> consume(map(print, [msg.channel for msg in res]))
		#default
		#default
		#foo
		"""
		properties = defaults
		for item in items:
			# allow the Sentinel to be just the class itself, which is to be
			#  constructed with no parameters.
			if isinstance(item, type) and issubclass(item, Sentinel):
				item = item()
			if isinstance(item, Sentinel):
				properties.update(item.properties)
				continue
			yield AugmentableMessage(item, **properties)

class NoLog(Sentinel):
	"""
	A sentinel indicating that subsequent items should not be logged.
	"""

	@property
	def properties(self):
		return dict(secret=True)

class SwitchChannel(six.text_type, Sentinel):
	"""
	A sentinel indicating a new channel for subsequent messages.
	"""

	def __new__(cls, other):
		if not other.startswith('#'):
			other = '#' + other
		return super(SwitchChannel, cls).__new__(cls, other)

	@property
	def properties(self):
		return dict(channel=self)

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
		sent = self._out(self._conn, channel, s)
		log &= (
			channel in self._channels
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
		if msg.startswith('/me '):
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

	def _schedule_at(self, conn, name, channel, when, func, args, doc):
		runner_func = functools.partial(self.background_runner, conn, channel,
			func, args)
		if isinstance(when, datetime.date):
			midnight = datetime.time(0,0)
			when = datetime.datetime.combine(when, midnight)
		if isinstance(when, datetime.datetime):
			cmd = irc.schedule.DelayedCommand.at_time(when, runner_func)
			conn.irclibobj._schedule_command(cmd)
			return
		if not isinstance(when, datetime.time):
			raise ValueError("when must be datetime, date, or time")
		cmd = irc.schedule.PeriodicCommandFixedDelay.daily_at(when,
			runner_func)
		conn.irclibobj._schedule_command(cmd)

	def on_welcome(self, connection, event):
		# save the connection object so .out has something to call
		self._conn = connection
		if pmxbot.config.nickserv_password:
			connection.privmsg('NickServ', 'identify %s' %
				pmxbot.config.nickserv_password)

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
			self._schedule_at(connection, *action)

		self._set_keepalive(connection)

	def _set_keepalive(self, connection):
		if 'TCP keepalive' not in pmxbot.config:
			return
		period = pmxbot.config['TCP keepalive']
		if isinstance(period, numbers.Number):
			period = datetime.timedelta(seconds=period)
		if isinstance(period, six.string_types):
			period = dateutil.parse_timedelta(period)
		log.info("Setting keepalive for %s", period)
		pinger = functools.partial(connection.ping, 'keep-alive')
		connection.execute_every(period, pinger)

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

	def on_leave(self, connection, event):
		nick = event.source.nick
		channel = event.target
		for func in _leave_registry:
			try:
				func(client=connection, event=event, nick=nick,
					channel=channel)
			except Exception:
				print(datetime.datetime.now(),
					"Error in on_leave handler %s" % func,
					file=sys.stderr)
				traceback.print_exc()

	def on_pubmsg(self, connection, event):
		msg = ''.join(event.arguments)
		if not msg.strip():
			return
		nick = event.source.nick
		channel = event.target
		if channel in pmxbot.config.log_channels:
			pmxbot.logging.Logger.store.message(channel, nick, msg)
		self.handle_action(connection, event, channel, nick, msg)

	def on_privmsg(self, connection, event):
		msg = ''.join(event.arguments)
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
		augmented_messages = Sentinel.augment_items(output,
			channel=channel, secret=False)
		for message in augmented_messages:
			self.out(message.channel, message, not message.secret)

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
			handler for handler in Handler._registry
			if handler.match(msg, channel))
		for handler in matching_handlers:
			exception_handler = functools.partial(
				self._handle_exception,
				handler = handler,
				)
			f = functools.partial(handler.func, connection, event, channel,
				nick, handler.process(msg))
			results = pmxbot.itertools.generate_results(f)
			clean_results = pmxbot.itertools.trap_exceptions(results,
				exception_handler)
			messages = itertools.chain(messages, clean_results)
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

class FinalRegistry:
	"""
	A list of callbacks to run at exit.
	"""
	_finalizers = []

	@classmethod
	def at_exit(cls, finalizer):
		cls._finalizers.append(finalizer)

	@classmethod
	def finalize(cls):
		for callback in cls._finalizers:
			try:
				callback()
			except:
				pass

_delay_registry = []
_at_registry = []
_join_registry = []
_leave_registry = []

class Handler(object):
	_registry = []

	class_priority = 1
	"priority of this class relative to other classes, precedence to higher"

	priority = 1
	"priority relative to other handlers of this class, precedence to higher"

	allow_chain = False
	"allow subsequent handlers to also process the same message"

	def __init__(self, **kwargs):
		self.__dict__.update(kwargs)

	def register(self):
		self._registry.append(self)
		self._registry.sort()

	def decorate(self, func):
		self.func = func
		self._set_implied_name()
		self.register()
		return func

	def _set_implied_name(self):
		"""
		Allow the name of this handler to default to the function name.
		"""
		if getattr(self, 'name', None) is None:
			self.name = self.func.__name__
		self.name = self.name.lower()

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
		return random.random() <= self.rate

class CommandHandler(Handler):
	class_priority = 3
	aliases = ()

	def decorate(self, func):
		self._set_doc(func)
		for alias in self.aliases:
			func = alias.decorate(func)
		return super(CommandHandler, self).decorate(func)

	def _set_doc(self, func):
		"""
		If no doc was explicitly set, use the function's docstring, trimming
		whitespace and replacing newlines with spaces.
		"""
		if not self.doc and func.__doc__:
			self.doc = func.__doc__.strip().replace('\n', ' ')

	def match(self, message, channel):
		cmd, _, cmd_args = message.partition(' ')
		return cmd.lower() == '!{name}'.format(name = self.name)

	def process(self, message):
		cmd, _, cmd_args = message.partition(' ')
		return cmd_args

	@property
	def alias_names(self):
		return [alias.name for alias in self.aliases]

class AliasHandler(CommandHandler):
	class_priority = 2

	@property
	def doc(self):
		return self.parent.doc

	def __str__(self):
		return self.name
	__unicode__ = __str__

class RegexpHandler(ContainsHandler):
	class_priority = 4

	def __init__(self, *args, **kwargs):
		super(RegexpHandler, self).__init__(*args, **kwargs)
		if isinstance(self.pattern, six.string_types):
			self.pattern = re.compile(self.pattern, re.IGNORECASE)

	def match(self, message, channel):
		return self.pattern.search(message)

	def process(self, message):
		return self.pattern.search(message)

def contains(name, channels=(), exclude=(), rate=1.0, priority=1,
		doc=None, **kwargs):
	return ContainsHandler(
		name=name,
		doc=doc,
		channels=channels,
		exclude=exclude,
		rate=rate,
		priority=priority,
		**kwargs).decorate

def command(name=None, aliases=None, doc=None):
	handler = CommandHandler(name=name, doc=doc)
	aliases = [
		AliasHandler(name=alias, parent=handler)
		for alias in always_iterable(aliases)
	]
	handler.aliases = aliases
	return handler.decorate

def regexp(name, regexp, doc=None, **kwargs):
	return RegexpHandler(
		name=name,
		doc=doc,
		pattern=regexp,
		**kwargs
	).decorate

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

def on_leave(doc=None):
	def deco(func):
		_leave_registry.append(func)
		return func
	return deco

class ConfigMergeAction(argparse.Action):
	def __call__(self, parser, namespace, values, option_string=None):
		def merge_dicts(a, b):
			a.update(b)
			return a
		setattr(namespace, self.dest, six.moves.reduce(merge_dicts, values))

def get_args(*args, **kwargs):
	parser = argparse.ArgumentParser()
	parser.add_argument('config', type=pmxbot.dictlib.ConfigDict.from_yaml,
		default={}, nargs='*', action=ConfigMergeAction)
	return parser.parse_args(*args, **kwargs)

def run():
	global _bot
	_bot = initialize(get_args().config)
	try:
		_bot.start()
	finally:
		FinalRegistry.finalize()

def _setup_logging():
	log_level = pmxbot.config['log level']
	if isinstance(log_level, six.string_types):
		log_level = getattr(logging, log_level.upper())
	logging.basicConfig(level=log_level, format="%(message)s")

def initialize(config):
	"""
	Initialize the bot with a dictionary of config items
	"""
	pmxbot.config.update(config)
	config = pmxbot.config

	pmxbot.buffer.ErrorReportingBuffer.install()
	_setup_logging()
	_load_library_extensions()
	if not Handler._registry:
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

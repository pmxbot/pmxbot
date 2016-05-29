# vim:ts=4:sw=4:noexpandtab

import datetime
import random
import functools
import argparse
import logging
import pprint
import re
import importlib
import abc

import pkg_resources
from jaraco.itertools import always_iterable

import pmxbot.dictlib
import pmxbot.buffer
from .dictlib import ConfigDict


log = logging.getLogger('pmxbot')


class AugmentableMessage(str):
	"""
	A text string which may be augmented with attributes

	>>> msg = AugmentableMessage('foo', bar='baz')
	>>> msg == 'foo'
	True
	>>> msg.bar == 'baz'
	True
	"""

	def __new__(cls, other, **kwargs):
		return super().__new__(cls, other)

	def __init__(self, other, **kwargs):
		if hasattr(other, '__dict__'):
			self.__dict__.update(vars(other))
		self.__dict__.update(**kwargs)


class Sentinel:
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
	"A sentinel indicating that subsequent items should not be logged."

	@property
	def properties(self):
		return dict(secret=True)


class SwitchChannel(str, Sentinel):
	"A sentinel indicating a new channel for subsequent messages."

	def __new__(cls, other):
		if not other.startswith('#'):
			other = '#' + other
		return super().__new__(cls, other)

	@property
	def properties(self):
		return dict(channel=self)


class FinalRegistry:
	"A list of callbacks to run at exit."
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


class Handler:
	_registry = []

	class_priority = 1
	"priority of this class relative to other classes, precedence to higher"

	priority = 1
	"priority relative to other handlers of this class, precedence to higher"

	allow_chain = False
	"allow subsequent handlers to also process the same message"

	@classmethod
	def find_matching(cls, message, channel):
		"""
		Yield ``cls`` subclasses that match message and channel
		"""
		return (
			handler
			for handler in cls._registry
			if isinstance(handler, cls)
			and handler.match(message, channel)
		)

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
		"Allow the name of this handler to default to the function name."
		if getattr(self, 'name', None) is None:
			self.name = self.func.__name__
		self.name = self.name.lower()

	@property
	def sort_key(self):
		return -self.class_priority, -self.priority, -len(self.name)

	def __gt__(self, other):
		return self.sort_key > other.sort_key

	def match(self, message, channel):
		"Return True if the message is matched by this handler."
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
		return super().decorate(func)

	def _set_doc(self, func):
		"""
		If no doc was explicitly set, use the function's docstring, trimming
		whitespace and replacing newlines with spaces.
		"""
		if not self.doc and func.__doc__:
			self.doc = func.__doc__.strip().replace('\n', ' ')

	def match(self, message, channel):
		cmd, _, cmd_args = message.partition(' ')
		return cmd.lower() == '!{name}'.format(name=self.name)

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
		super().__init__(*args, **kwargs)
		if isinstance(self.pattern, str):
			self.pattern = re.compile(self.pattern, re.IGNORECASE)

	def match(self, message, channel):
		return self.pattern.search(message)

	def process(self, message):
		return self.pattern.search(message)


class ContentHandler(ContainsHandler):
	"""
	A custom handler that by default handles all messages.
	"""
	class_priority = 5
	allow_chain = True
	name = ''


def contains(name, channels=(), exclude=(), rate=1.0, priority=1, doc=None, **kwargs):
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
		_delay_registry.append((name.lower(), channel, howlong, func, args, doc, repeat))
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
		setattr(namespace, self.dest, functools.reduce(merge_dicts, values))


class Bot(metaclass=abc.ABCMeta):
	def out(self, channel, s, log=True):
		sent = self.transmit(channel, s)
		if not sent or not log or s.startswith('/me'):
			return

		# the bot has just said something, feed that
		# message into the logging handler to be included
		# in the logs.
		res = ContentHandler.find_matching(message=sent, channel=channel)
		for handler in res:
			handler.func(self._conn, None, channel, self._nickname, sent)

	@abc.abstractmethod
	def transmit(self, channel, message):
		"""
		Transmit `message` using
		`channel`. If `message` looks like an action, transmit it as such.
		Suppress all exceptions (but log warnings for each).
		Return the message as sent.
		"""


def get_args(*args, **kwargs):
	parser = argparse.ArgumentParser()
	parser.add_argument(
		'config', type=pmxbot.dictlib.ConfigDict.from_yaml,
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
	log_level = pmxbot.config.get('log level', logging.INFO)
	if isinstance(log_level, str):
		log_level = getattr(logging, log_level.upper())
	logging.basicConfig(level=log_level, format="%(message)s")


def _load_bot_class():
	default = 'pmxbot.irc:LoggingCommandBot'
	class_spec = pmxbot.config.get('bot class', default)
	mod_name, sep, name = class_spec.partition(':')
	module = importlib.import_module(mod_name)
	return eval(name, vars(module))


def init_config(overrides):
	"""
	Install the config dict as pmxbot.config, setting overrides,
	and return the result.
	"""
	pmxbot.config = config = ConfigDict()
	config.setdefault('bot_nickname', 'pmxbot')
	config.update(overrides)
	return config


def initialize(config):
	"Initialize the bot with a dictionary of config items"
	config = init_config(config)

	pmxbot.buffer.ErrorReportingBuffer.install()
	_setup_logging()
	_load_library_extensions()
	if not Handler._registry:
		raise RuntimeError("No handlers registered")

	class_ = _load_bot_class()

	config.setdefault('log_channels', [])
	config.setdefault('other_channels', [])

	channels = config.log_channels + config.other_channels

	log.info('Running with config')
	log.info(pprint.pformat(config))

	host = config.get('server_host', 'localhost')
	port = config.get('server_port', 6667)

	return class_(
		host,
		port,
		config.bot_nickname,
		channels=channels,
		password=config.get('password'),
	)


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

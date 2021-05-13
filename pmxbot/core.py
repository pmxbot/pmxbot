import datetime
import random
import functools
import argparse
import logging
import pprint
import re
import importlib
import abc
import inspect
import traceback
import itertools

from typing import List, Callable

import importlib_metadata
from jaraco.itertools import always_iterable
from jaraco.collections import Projection
from tempora import schedule

import pmxbot.dictlib
import pmxbot.itertools
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

        >>> res = Sentinel.augment_items(msgs, channel='#default', secret=False)
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

    @property
    def properties(self):
        return dict(channel=self)


class FinalRegistry:
    "A list of callbacks to run at exit."
    _finalizers: List[Callable] = []

    @classmethod
    def at_exit(cls, finalizer):
        cls._finalizers.append(finalizer)

    @classmethod
    def finalize(cls):
        for callback in cls._finalizers:
            try:
                callback()
            except Exception:
                pass


class Handler:
    _registry: List['Handler'] = []

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
            if isinstance(handler, cls) and handler.match(message, channel)
        )

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def register(self):
        if self in self._registry:
            return
        self._registry.append(self)
        self._registry.sort()

    def decorate(self, func):
        """
        Decorate a handler function. The handler should accept keyword
        parameters for values supplied by the bot, a subset of:
        - client
        - connection (alias for client)
        - event
        - channel
        - nick
        - rest
        """
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

    def __eq__(self, other):
        return vars(self) == vars(other)

    def match(self, message, channel):
        "Return True if the message is matched by this handler."
        return False

    def process(self, message):
        return message

    def attach(self, params):
        """
        Attach relevant params to func, returning a callable
        that takes no parameters.
        """
        return attach(self.func, params)


def attach(func, params):
    """
    Given a function and a namespace of possible parameters,
    bind any params matching the signature of the function
    to that function.
    """
    sig = inspect.signature(func)
    params = Projection(sig.parameters.keys(), params)
    return functools.partial(func, **params)


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
            not self.channels
            and not self.exclude
            or channel in self.channels
            or self.exclude
            and channel not in self.exclude
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

    def __eq__(self, other):
        def rem_alias(ob):
            """
            When comparing for equality, remove the 'aliases'
            attribute to avoid infinite recursion when comparing.
            """
            copy = dict(vars(ob))
            copy.pop('aliases', None)
            return copy

        return rem_alias(self) == rem_alias(other)

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


class Scheduled(Handler):
    _registry: List[Handler] = []


class DelayHandler(Scheduled):
    def as_cmd(self):
        cls = schedule.PeriodicCommand if self.repeat else schedule.DelayedCommand
        return cls.after(self.duration, self)


class AtHandler(Scheduled):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        date_types = datetime.date, datetime.datetime, datetime.time
        if not isinstance(self.when, date_types):
            raise TypeError("when must be a date or time object")

    def as_cmd(self):
        factory = (
            schedule.PeriodicCommandFixedDelay.daily_at
            if isinstance(self.when, datetime.time)
            else schedule.DelayedCommand.at_time
        )
        return factory(self.when, self)


class JoinHandler(Handler):
    _registry: List[Handler] = []


class LeaveHandler(Handler):
    """
    Handles quits and parts.
    """

    _registry: List[Handler] = []


def contains(name, channels=(), exclude=(), rate=1.0, priority=1, doc=None, **kwargs):
    return ContainsHandler(
        name=name,
        doc=doc,
        channels=channels,
        exclude=exclude,
        rate=rate,
        priority=priority,
        **kwargs
    ).decorate


def command(name=None, aliases=None, doc=None):
    if callable(name):
        raise ValueError("Name should be a string, did you forget ()?")
    handler = CommandHandler(name=name, doc=doc)
    aliases = [
        AliasHandler(name=alias, parent=handler) for alias in always_iterable(aliases)
    ]
    handler.aliases = aliases
    return handler.decorate


def regexp(name, regexp, doc=None, **kwargs):
    return RegexpHandler(name=name, doc=doc, pattern=regexp, **kwargs).decorate


def execdelay(name, channel, howlong, doc=None, repeat=False):
    return DelayHandler(
        name=name.lower(), channel=channel, duration=howlong, doc=doc, repeat=repeat
    ).decorate


def execat(name, channel, when, doc=None):
    return AtHandler(name=name.lower(), channel=channel, when=when, doc=doc).decorate


def on_join(doc=None):
    return JoinHandler(doc=doc).decorate


def on_leave(doc=None):
    return LeaveHandler(doc=doc).decorate


class ConfigMergeAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        def merge_dicts(a, b):
            a.update(b)
            return a

        setattr(namespace, self.dest, functools.reduce(merge_dicts, values, {}))


class Bot(metaclass=abc.ABCMeta):
    """
    The abstract interface for the bot.
    """

    def out(self, channel, s, log=True):
        try:
            sent = self.allow(channel, s) and self.transmit(channel, s)
        except Exception:
            msg = "Unhandled exception transmitting message: %r"
            globals()['log'].exception(msg, s)
            return

        if not sent or not log or s.startswith('/me'):
            return

        # the bot has just said something, feed that
        # message into the content handlers.
        params = dict(channel=channel, nick=self._nickname, rest=sent)
        res = ContentHandler.find_matching(message=sent, channel=channel)
        for handler in res:
            handler.attach(params)()

    @abc.abstractmethod
    def transmit(self, channel, message):
        """
        Transmit `message` using
        `channel`. If `message` looks like an action, transmit it as such.
        Suppress all exceptions (but log warnings for each).
        Return the message as sent.
        """

    def allow(self, channel, message):
        """
        Allow plugins to filter content.
        """
        return all(filter(channel, message) for filter in _load_filters())

    def _handle_exception(self, exception, handler):
        expletives = ['Yikes!', 'Zoiks!', 'Ouch!']
        res = [
            "{expletive} An error occurred: {exception}".format(
                expletive=random.choice(expletives), **locals()
            )
        ]
        res.append('!{name} {doc}'.format(name=handler.name, doc=handler.doc))
        print(
            datetime.datetime.now(),
            "Error with command {handler}".format(handler=handler),
        )
        traceback.print_exc()
        return res

    def _handle_output(self, channel, output):
        """
        Given an initial channel and a sequence of messages or sentinels,
        output the messages.
        """
        augmented = Sentinel.augment_items(output, channel=channel, secret=False)
        for message in augmented:
            self.out(message.channel, message, not message.secret)

    def handle_action(self, channel, nick, msg):
        "Core message parser and dispatcher"

        messages = ()
        for handler in Handler.find_matching(msg, channel):
            exception_handler = functools.partial(
                self._handle_exception, handler=handler
            )
            rest = handler.process(msg)
            client = connection = event = None
            # for regexp handlers
            match = rest
            f = handler.attach(locals())
            results = pmxbot.itertools.generate_results(f)
            clean_results = pmxbot.itertools.trap_exceptions(results, exception_handler)
            messages = itertools.chain(messages, clean_results)
            if not handler.allow_chain:
                break
        self._handle_output(channel, messages)

    def init_schedule(self, scheduler):
        for handler in Scheduled._registry:
            scheduler.add(handler.as_cmd())

    def handle_scheduled(self, target):
        """
        target is a Handler or simple callable
        """
        if not isinstance(target, Handler):
            return target()

        return self._handle_scheduled(target)

    def _handle_scheduled(self, handler):
        exception_handler = functools.partial(self._handle_exception, handler=handler)
        channel = handler.channel
        client = connection = event = None
        f = handler.attach(locals())
        results = pmxbot.itertools.generate_results(f)
        clean_results = pmxbot.itertools.trap_exceptions(results, exception_handler)
        self._handle_output(handler.channel, clean_results)


def get_args(*args, **kwargs):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'config',
        type=pmxbot.dictlib.ConfigDict.from_yaml,
        nargs='*',
        action=ConfigMergeAction,
    )
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
    if 'slack token' in pmxbot.config:
        default = 'pmxbot.slack:Bot'
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
                'plugin name = mylib.mymodule:initialize_func',
            ],
        },

    `plugin name` can be anything, and is only used to display the name
    of the plugin at initialization time.
    """
    entry_points = importlib_metadata.entry_points(group='pmxbot_handlers')
    for ep in entry_points:
        try:
            log.info('Loading %s', ep.name)
            init_func = ep.load()
            if callable(init_func):
                init_func()
        except Exception:
            log.exception("Error initializing plugin %s." % ep)


@functools.lru_cache()
def _load_filters():
    """
    Locate all entry points by the name 'pmxbot_filters', each of
    which should refer to a callable(channel, msg) that must return
    True for the message not to be excluded.
    """
    eps = importlib_metadata.entry_points(group='pmxbot_filters')
    return [ep.load() for ep in eps]

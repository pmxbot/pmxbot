import textwrap
import datetime
import importlib
import functools
import logging
import numbers
import itertools
import traceback
import time
import random

import pytz
import irc.bot
import irc.schedule
import irc.client
import tempora

import pmxbot.itertools
from . import core


log = logging.getLogger(__name__)


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
		if key not in self or self._expired(self[key], now):
			self[key] = now
			return True
		return False

	def _expired(self, last, now):
		return now - last > self.warn_every

	def warn(self, nick, connection):
		if pmxbot.config.get('privacy warning') == 'suppress':
			return
		if not self.needs_warning(nick):
			return
		logged_channels_string = ', '.join(pmxbot.config.log_channels)
		msg = self.warn_message.format(**locals())
		for line in msg.splitlines():
			connection.notice(nick, line)

class LoggingCommandBot(core.Bot, irc.bot.SingleServerIRCBot):
	def __init__(self, server, port, nickname, channels, password=None):
		server_list = [(server, port, password)]
		irc.bot.SingleServerIRCBot.__init__(self, server_list, nickname, nickname)
		self.nickname = nickname
		self._channels = channels
		self._nickname = nickname
		self.warn_history = WarnHistory()
		self._scheduled_tasks = set()

	def connect(self, *args, **kwargs):
		factory = irc.connection.Factory(wrapper=self._get_wrapper())
		res = irc.bot.SingleServerIRCBot.connect(
			self,
			connect_factory=factory,
			*args, **kwargs
		)
		limit = pmxbot.config.get('message rate limit', float('inf'))
		self.connection.set_rate_limit(limit)
		return res

	@staticmethod
	def _get_wrapper():
		"""
		Get a socket wrapper based on SSL config.
		"""
		if not pmxbot.config.get('use_ssl', False):
			return lambda x: x
		return importlib.import_module('ssl').wrap_socket

	def transmit(self, channel, msg):
		conn = self._conn
		func = conn.privmsg
		if msg.startswith('/me '):
			func = conn.action
			msg = msg.split(' ', 1)[-1].lstrip()
		try:
			func(channel, msg)
			return msg
		except irc.client.MessageTooLong:
			# some msgs will fail because they're too long
			log.warning("Long message could not be transmitted: %s", msg)
		except irc.client.InvalidCharacters:
			log.warning(
				"Message contains carriage returns,"
				"which aren't allowed in IRC messages: %r", msg)
		except Exception:
			log.exception("Unhandled exception transmitting message: %r", msg)

	def _schedule_at(self, conn, name, channel, when, func, args, doc):
		unique_task = (func, tuple(args), name, channel, when, doc)
		if unique_task in self._scheduled_tasks:
			return
		self._scheduled_tasks.add(unique_task)
		runner_func = functools.partial(self.background_runner, conn, channel,
			func, args)
		if isinstance(when, datetime.date):
			midnight = datetime.time(0, 0, tzinfo=pytz.UTC)
			when = datetime.datetime.combine(when, midnight)
		if isinstance(when, datetime.datetime):
			cmd = irc.schedule.DelayedCommand.at_time(when, runner_func)
			conn.reactor._schedule_command(cmd)
			return
		if not isinstance(when, datetime.time):
			raise ValueError("when must be datetime, date, or time")
		cmd = irc.schedule.PeriodicCommandFixedDelay.daily_at(when,
			runner_func)
		conn.reactor._schedule_command(cmd)

	def on_welcome(self, connection, event):
		# save the connection object so .out has something to call
		self._conn = connection
		if pmxbot.config.get('nickserv_password'):
			msg = 'identify %s' % pmxbot.config.nickserv_password
			connection.privmsg('NickServ', msg)

		# join channels
		for channel in self._channels:
			if not channel.startswith('#'):
				channel = '#' + channel
			connection.join(channel)

		# set up delayed tasks
		for name, channel, howlong, func, args, doc, repeat in core._delay_registry:
			arguments = connection, channel, func, args
			executor = (
				connection.execute_every if repeat
				else connection.execute_delayed
			)
			executor(howlong, self.background_runner, arguments)
		for action in core._at_registry:
			try:
				self._schedule_at(connection, *action)
			except Exception:
				log.exception("Error scheduling %s", action)

		self._set_keepalive(connection)

	def _set_keepalive(self, connection):
		if 'TCP keepalive' not in pmxbot.config:
			return
		period = pmxbot.config['TCP keepalive']
		if isinstance(period, numbers.Number):
			period = datetime.timedelta(seconds=period)
		if isinstance(period, str):
			period = tempora.parse_timedelta(period)
		log.info("Setting keepalive for %s", period)
		connection.set_keepalive(period)

	def on_join(self, connection, event):
		nick = event.source.nick
		channel = event.target
		for func in core._join_registry:
			try:
				func(client=connection, event=event, nick=nick, channel=channel)
			except Exception:
				log.exception("Error in on_join handler %s", func)

		if channel not in pmxbot.config.log_channels:
			return
		if nick == self._nickname:
			return
		self.warn_history.warn(nick, connection)

	def on_leave(self, connection, event):
		nick = event.source.nick
		channel = event.target
		for func in core._leave_registry:
			try:
				func(client=connection, event=event, nick=nick, channel=channel)
			except Exception:
				log.exception("Error in on_leave handler %s", func)

	def on_pubmsg(self, connection, event):
		msg = ''.join(event.arguments)
		if not msg.strip():
			return
		nick = event.source.nick
		channel = event.target
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
		augmented_messages = core.Sentinel.augment_items(output, channel=channel, secret=False)
		for message in augmented_messages:
			self.out(message.channel, message, not message.secret)

	def background_runner(self, connection, channel, func, args):
		"Wrapper to run scheduled type tasks cleanly."
		def on_error(exception):
			print(datetime.datetime.now(), "Error in background runner for ", func)
			traceback.print_exc()
		func = functools.partial(func, connection, None, *args)
		results = pmxbot.itertools.generate_results(func)
		clean_results = pmxbot.itertools.trap_exceptions(results, on_error)
		self._handle_output(channel, clean_results)

	def _handle_exception(self, exception, handler):
		expletives = ['Yikes!', 'Zoiks!', 'Ouch!']
		res = [
			"{expletive} An error occurred: {exception}".format(
				expletive=random.choice(expletives),
				**vars())
		]
		res.append('!{name} {doc}'.format(name=handler.name, doc=handler.doc))
		print(datetime.datetime.now(), "Error with command {handler}".format(handler=handler))
		traceback.print_exc()
		return res

	def handle_action(self, connection, event, channel, nick, msg):
		"Core message parser and dispatcher"

		messages = ()
		for handler in core.Handler.find_matching(msg, channel):
			exception_handler = functools.partial(
				self._handle_exception,
				handler=handler,
			)
			f = functools.partial(handler.func, connection, event, channel, nick, handler.process(msg))
			results = pmxbot.itertools.generate_results(f)
			clean_results = pmxbot.itertools.trap_exceptions(results, exception_handler)
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

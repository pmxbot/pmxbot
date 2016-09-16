import textwrap
import datetime
import importlib
import logging
import numbers
import time

import irc.bot
import irc.schedule
import irc.client
import tempora
from jaraco.stream import buffer

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


class Scheduler(tempora.schedule.CallbackScheduler, irc.schedule.IScheduler):
	# implement abstract methods that will never get called
	def execute_every(self, *args, **kwargs):
		pass
	execute_after = execute_at = execute_every



class LoggingCommandBot(core.Bot, irc.bot.SingleServerIRCBot):
	def __init__(self, server, port, nickname, channels, password=None):
		ErrorReportingBuffer.install()
		server_list = [(server, port, password)]
		irc.bot.SingleServerIRCBot.__init__(self, server_list, nickname, nickname)
		self.reactor.scheduler = Scheduler(dispatch=self.handle_scheduled)
		self.nickname = nickname
		self._channels = channels
		self._nickname = nickname
		self.warn_history = WarnHistory()

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
			tmpl = (
				"Message contains carriage returns, "
				"which aren't allowed in IRC messages: %r"
			)
			log.warning(tmpl, msg)

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

		self.init_schedule(self.reactor.scheduler)

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
		client = connection
		for handler in core.JoinHandler._registry:
			try:
				handler.attach(locals())()
			except Exception:
				log.exception("Error in %s", handler)

		if channel not in pmxbot.config.log_channels:
			return
		if nick == self._nickname:
			return
		self.warn_history.warn(nick, connection)

	def on_leave(self, connection, event):
		nick = event.source.nick
		channel = event.target
		client = connection
		for handler in core.JoinHandler._registry:
			try:
				handler.attach(locals())()
			except Exception:
				log.exception("Error in %s", handler)

	def on_pubmsg(self, connection, event):
		msg = ''.join(event.arguments)
		if not msg.strip():
			return
		nick = event.source.nick
		channel = event.target
		self.handle_action(channel, nick, msg)

	def on_privmsg(self, connection, event):
		msg = ''.join(event.arguments)
		if not msg.strip():
			return
		nick = event.source.nick
		channel = nick
		self.handle_action(channel, nick, msg)

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


class SilentCommandBot(LoggingCommandBot):
	"""
	A version of the bot that doesn't say anything (just logs and
	processes commands).
	"""
	def out(self, *args, **kwargs):
		"Do nothing"

	def on_join(self, *args, **kwargs):
		"Do nothing"


class ErrorReportingBuffer(buffer.LineBuffer):
	encoding = 'utf-8'

	def lines(self):
		lines = super().lines()
		for line in lines:
			try:
				yield line.decode(self.encoding)
			except UnicodeDecodeError:
				log.error("Unable to decode line: {line!r}".format(line=line))

	@classmethod
	def install(cls):
		irc.client.ServerConnection.buffer_class = cls

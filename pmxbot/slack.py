import time
import importlib
import logging
import re
import collections
import html

from tempora import schedule

import pmxbot
from pmxbot import core


log = logging.getLogger(__name__)


class Bot(pmxbot.core.Bot):
	def __init__(self, server, port, nickname, channels, password=None):
		token = pmxbot.config['slack token']
		sc = importlib.import_module('slackclient')
		self.slack = sc.SlackClient(token)
		sr = importlib.import_module('slacker')
		self.slacker = sr.Slacker(token)

		self.scheduler = schedule.CallbackScheduler(self.handle_scheduled)

	def start(self):
		res = self.slack.rtm_connect()
		assert res, "Error connecting"
		self.init_schedule(self.scheduler)
		while True:
			for msg in self.slack.rtm_read():
				self.handle_message(msg)
			self.scheduler.run_pending()
			time.sleep(0.1)

	def handle_message(self, msg):
		if msg.get('type') != 'message':
			return

		# resolve nick based on message subtype
		# https://api.slack.com/events/message
		method_name = '_resolve_nick_{subtype}'.format_map(
			collections.defaultdict(lambda: 'standard', msg),
		)
		resolve_nick = getattr(self, method_name, None)
		if not resolve_nick:
			log.debug('Unhandled message %s', msg)
			return
		nick = resolve_nick(msg)

		channel = self.slack.server.channels.find(msg['channel']).name
		channel = core.AugmentableMessage(channel, thread=msg.get('thread_ts'))

		self.handle_action(channel, nick, html.unescape(msg['text']))

	def _resolve_nick_standard(self, msg):
		return self.slack.server.users.find(msg['user']).name

	_resolve_nick_me_message = _resolve_nick_standard

	def _resolve_nick_bot_message(self, msg):
		return msg.get('username') or msg.get('bot_id') or 'Anonymous Bot'

	def _find_user_channel(self, username):
		"""
		Use slacker to resolve the username to an opened IM channel
		"""
		user_id = self.slacker.users.get_user_id(username)
		im = user_id and self.slacker.im.open(user_id).body['channel']['id']
		return im and self.slack.server.channels.find(im)

	def transmit(self, channel, message):
		"""
		Send the message to Slack.

		:param channel: channel or user to whom the message should be sent.
			If a ``thread`` attribute is present, that thread ID is used.
		:param str message: message to send.
		"""
		target = (
			self.slack.server.channels.find(channel)
			or self._find_user_channel(username=channel)
		)
		message = self._expand_references(message)

		target.send_message(message, thread=getattr(channel, 'thread', None))

	def _expand_references(self, message):
		resolvers = {
			'@': self.slacker.users.get_user_id,
			'#': self.slacker.channels.get_channel_id,
		}

		def _expand(match):
			match_type = match.groupdict()['type']
			match_name = match.groupdict()['name']

			try:
				ref = resolvers[match_type](match_name)
				assert ref is not None
			except Exception:
				# capture any exception, fallback to original text
				log.exception("Error resolving slack reference: {}".format(message))
				return match.group(0)

			return '<{match_type}{ref}>'.format_map(locals())

		regex = r'(?P<type>[@#])(?P<name>[\w\d\.\-_\|]*)'
		slack_refs = re.compile(regex)
		return slack_refs.sub(_expand, message)

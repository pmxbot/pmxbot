import time
import importlib
import logging

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
		if not msg.get('user'):
			log.warning("Unknown message %s", msg)
			return
		channel = self.slack.server.channels.find(msg['channel']).name
		nick = self.slack.server.users.find(msg['user']).name

		channel = core.AugmentableMessage(channel, thread=msg.get('thread_ts'))

		self.handle_action(channel, nick, msg['text'])

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
			self.slack.server.channels.find(channel) or
			self._find_user_channel(username=channel)
		)
		target.send_message(message, thread=getattr(channel, 'thread', None))

import time
import importlib
import logging

from tempora import schedule

import pmxbot


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

		context = dict()
		if msg.get('thread_ts'):
			# If the 'thread_ts' attribute is present in the incoming
			# message then we're part of a thread, and should reply in
			# the same thread by including the parent thread ID in the reply.
			context['thread_ts'] = msg['thread_ts']

		self.handle_action(channel, nick, msg['text'], context)

	def _find_user_channel(self, username):
		"""
		Use slacker to resolve the username to an opened IM channel
		"""
		user_id = self.slacker.users.get_user_id(username)
		im = user_id and self.slacker.im.open(user_id).body['channel']['id']
		return im and self.slack.server.channels.find(im)

	def transmit(self, channel, message, context=None):
		"""
		Send the message to Slack.

		:param channel: channel or user to whom the message should be sent.
		:param str message: message to send.
		:param dict context: optional dict containing extra details about
			the message, such as the current 'thread' in Slack.
		"""

		kwargs = dict(message=message)
		if context is not None:
			kwargs['thread'] = context.get('thread_ts')

		target = (
			self.slack.server.channels.find(channel) or
			self._find_user_channel(username=channel)
		)
		target.send_message(message, **kwargs)

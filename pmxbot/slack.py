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
		self.client = sc.SlackClient(token)
		self.scheduler = schedule.CallbackScheduler(self.handle_scheduled)

	def start(self):
		res = self.client.rtm_connect()
		assert res, "Error connecting"
		self.init_schedule(self.scheduler)
		while True:
			for msg in self.client.rtm_read():
				self.handle_message(msg)
			self.scheduler.run_pending()
			time.sleep(0.1)

	def handle_message(self, msg):
		if msg.get('type') != 'message':
			return
		if not msg.get('user'):
			log.warning("Unknown message %s", msg)
			return
		channel = self.client.server.channels.find(msg['channel']).name
		nick = self.client.server.users.find(msg['user']).name
		self.handle_action(channel, nick, msg['text'])

	def _find_user_channel(self, username):
		"""
		slackclient doesn't make it easy to send a message to a user.
		"""
		user = self.client.server.users.find(username)
		items = (
			im
			for im in self.client.server.login_data['ims']
			if user and im['user'] == user.id
		)
		im = next(items, None)
		return im and self.client.server.channels.find(im['id'])

	def transmit(self, channel, message):
		target = (
			self.client.server.channels.find(channel)
			or self._find_user_channel(username=channel)
		)
		target.send_message(message)

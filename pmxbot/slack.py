import time
import importlib

import pmxbot


class Bot:
	def __init__(self, server, port, nickname, channels, password=None):
		token = pmxbot.config['slack token']
		sc = importlib.import_module('slackclient')
		self.client = sc.SlackClient(token)

	def start(self):
		res = self.client.rtm_connect()
		assert res, "Error connecting"
		while True:
			for msg in self.client.rtm_read():
				self.handle_message(msg)
			self.handle_scheduled_tasks()
			time.sleep(0.1)

	def handle_message(self, msg):
		"stubbed"

	def handle_scheduled_tasks(self):
		"stubbed"

	def transmit(self, channel, message):
		channel = self.client.server.channels.find(channel)
		channel.send_message(message)

import subprocess
import shlex
import os
import yaml
import irclib
import time
import sqlite3

import py.test

class TestingClient(object):
	def __init__(self, server, port, nickname):
		self.irc = irclib.IRC()
		self.c = self.irc.server()
		self.c.connect(server, port, nickname)
		self.irc.process_once(0.1)		
		
	def send_message(self, channel, message):
	   	self.c.privmsg(channel, message)
		time.sleep(0.05)

class PmxbotHarness(object):
	@classmethod
	def setup_class(cls):
		"""Start a tcl IRC server, launch the bot, and
		ask it to do stuff"""
		path = os.path.dirname(os.path.abspath(__file__))
		configfile = os.path.join(path, 'testconf.yaml')
		cls.config = yaml.load(open(configfile))
		cls.dbfile = os.path.join(cls.config['database_dir'], 'pmxbot.sqlite')
		cls.db = sqlite3.connect(cls.dbfile)
		
		serverargs = shlex.split('/usr/bin/tclsh tclird/ircd.tcl')
		try:
			cls.server = subprocess.Popen(['tclsh', os.path.join(path,
				'tclircd/ircd.tcl')], stdout=open(os.path.devnull, 'w'),
				stderr=open(os.path.devnull, 'w'))
		except OSError:
			py.test.skip("Unable to launch irc server (tclsh must be in the path)")
		time.sleep(0.5)
		cls.bot = subprocess.Popen(['pmxbot', configfile])
		time.sleep(0.5)
		
		cls.client = TestingClient('localhost', 6668, 'testingbot')

	def check_logs(cls, channel='', nick='', message=''):
		if channel.startswith('#'):
			channel = channel[1:]
		time.sleep(0.1)
		cursor = cls.db.cursor()
		query = "select * from logs where 1=1"
		if channel:
			query += " and channel = :channel"
		if nick:
			query += " and nick = :nick"
		if message:
			query += " and message = :message"
		cursor.execute(query, {'channel' : channel, 'nick' : nick, 'message' : message})
		res = cursor.fetchall()
		print res
		if len(res) >= 1:
			return True
		else:
			return False
	
	@classmethod
	def teardown_class(cls):
		if hasattr(cls, 'bot'):
			cls.bot.terminate()
		if hasattr(cls, 'server'):
			cls.server.terminate()
		if hasattr(cls, 'db'):
			cls.db.rollback()
			cls.db.close()
		os.remove(cls.dbfile)

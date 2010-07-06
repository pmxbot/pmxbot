import subprocess
import shlex
import os
import yaml
import irclib
import time
import sqlite3

class TestingClient(object):
	def __init__(self, server, port, nickname):
		self.irc = irclib.IRC()
		self.c = self.irc.server()
		self.c.connect(server, port, nickname)
		self.irc.process_once(0.1)		
		
	def send_message(self, channel, message):
	   	self.c.privmsg(channel, message)
		time.sleep(0.1)

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
		cls.server = subprocess.Popen(['tclsh', os.path.join(path, 'tclircd/ircd.tcl')])
		time.sleep(1)
		cls.bot = subprocess.Popen(['pmxbot', configfile])
		time.sleep(1)
		
		cls.client = TestingClient('localhost', 6668, 'testingbot')

	def check_logs(cls, channel='', nick='', message=''):
		if channel.startswith('#'):
			channel = channel[1:]
		time.sleep(0.25)
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
		time.sleep(1)
		cls.bot.terminate()
		cls.server.terminate()
		cls.db.rollback()
		cls.db.close()
		os.remove(cls.dbfile)
		
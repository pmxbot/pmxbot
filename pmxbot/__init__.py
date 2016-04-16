# vim:ts=4:sw=4:noexpandtab

import socket
import logging as _logging

from .dictlib import ConfigDict

config = ConfigDict(
	bot_nickname='pmxbot',
	database='sqlite:pmxbot.sqlite',
	server_host='localhost',
	server_port=6667,
	use_ssl=False,
	password=None,
	nickserv_password=None,
	silent_bot=False,
	log_channels=[],
	other_channels=[],
	librarypaste='http://paste.jaraco.com',
)
config['logs URL'] = 'http://' + socket.getfqdn()
config['log level'] = _logging.INFO

"The config object"

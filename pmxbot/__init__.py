# vim:ts=4:sw=4:noexpandtab

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
"The config object"

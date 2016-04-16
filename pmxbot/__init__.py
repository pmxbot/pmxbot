# vim:ts=4:sw=4:noexpandtab

from .dictlib import ConfigDict

config = ConfigDict(
	bot_nickname='pmxbot',
	password=None,
	nickserv_password=None,
	log_channels=[],
	other_channels=[],
)
"The config object"

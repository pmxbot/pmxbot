# vim:ts=4:sw=4:noexpandtab

from .dictlib import ConfigDict

config = ConfigDict(
	bot_nickname='pmxbot',
	use_ssl=False,
	password=None,
	nickserv_password=None,
	silent_bot=False,
	log_channels=[],
	other_channels=[],
)
"The config object"

import os

from pmxbot.dictlib import ConfigDict

config = ConfigDict(
	web_base = '',
	host = '::0',
	port = int(os.environ.get('PORT', 8080)),
)

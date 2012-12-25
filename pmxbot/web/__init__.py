import os

import pmxbot

pmxbot.config.update(
	web_base = '/',
	host = '::0',
	port = int(os.environ.get('PORT', 8080)),
)

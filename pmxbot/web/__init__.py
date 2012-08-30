import os
import importlib

import pmxbot

pmxbot.config.update(
	web_base = '',
	host = '::0',
	port = int(os.environ.get('PORT', 8080)),
)

if __name__ == '__main__':
	importlib.import_module('pmxbot.web.viewer').run()

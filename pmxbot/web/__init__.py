import os

import pmxbot.dictlib

# copy the default config from the pmxbot application
config = pmxbot.dictlib.ConfigDict(pmxbot.config)
config.update(
	web_base = '',
	host = '::0',
	port = int(os.environ.get('PORT', 8080)),
)

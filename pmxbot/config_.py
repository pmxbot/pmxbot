from __future__ import absolute_import

import re
import socket
import logging

import yaml

import pmxbot
#from pmxbot.core import command
from .dictlib import ConfigDict


#@command()
def config(client, event, channel, nick, rest):
	"Change the running config, something like a=b or a+=b or a-=b"
	pattern = re.compile('(?P<key>\w+)\s*(?P<op>[+-]?=)\s*(?P<value>.*)$')
	match = pattern.match(rest)
	if not match:
		return "Command not recognized"
	res = match.groupdict()
	key = res['key']
	op = res['op']
	value = yaml.safe_load(res['value'])
	if op in ('+=', '-='):
		# list operation
		op_name = {'+=': 'append', '-=': 'remove'}[op]
		op_name
		if key not in pmxbot.config:
			msg = "{key} not found in config. Can't {op_name}."
			return msg.format(**vars())
		if not isinstance(pmxbot.config[key], (list, tuple)):
			msg = "{key} is not list or tuple. Can't {op_name}."
			return msg.format(**vars())
		op = getattr(pmxbot.config[key], op_name)
		op(value)
	else:  # op is '='
		pmxbot.config[key] = value


defaults = ConfigDict(
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
	places=['London', 'Tokyo', 'New York'],
	feed_interval=15,  # minutes
	feeds=[dict(
		name='pmxbot bitbucket',
		channel='#inane',
		linkurl='http://bitbucket.org/yougov/pmxbot',
		url='http://bitbucket.org/yougov/pmxbot',
	)],
	librarypaste='http://paste.jaraco.com',
)
defaults['logs URL'] = 'http://' + socket.getfqdn()
defaults['log level'] = logging.INFO


def initialize(config):
	"Initialize the library with a dictionary of config items"
	pmxbot.config = defaults
	pmxbot.config.update(config)
	return pmxbot.config

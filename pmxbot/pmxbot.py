# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:noexpandtab
# c-basic-indent: 4; tab-width: 4; indent-tabs-mode: true;
from __future__ import absolute_import, division

import argparse
import logging

from . import dictlib
from . import botbase

log = logging.getLogger(__name__)
config = None

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('config', type=dictlib.ConfigDict.from_yaml)
	return parser.parse_args()

def run():
	initialize(get_args().config).start()

def initialize(config):
	"""
	Initialize the bot with a pmxbot.dictlib.ConfigDict
	"""
	assert isinstance(config, dictlib.ConfigDict)
	globals().update(config=config)

	_setup_logging()
	_load_library_extensions()

	use_ssl = getattr(config, 'use_ssl', False)
	password = getattr(config, 'password', None)

	silent_bot = getattr(config, 'silent', False)

	class_ = (botbase.LoggingCommandBot
		if not silent_bot else botbase.SilentCommandBot)

	return class_(config.database, config.server_host, config.server_port,
		config.bot_nickname, config.log_channels, config.other_channels,
		use_ssl=use_ssl, password=password)


_finalizers = [
	botbase.LoggingCommandBot._finalize_logger,
]

def _cleanup():
	"Delete the various persistence objects"
	for finalizer in _finalizers:
		try:
			finalizer()
		except Exception:
			log.exception("Error in finalizer %s", finalizer)

def _setup_logging():
	logging.basicConfig(level=logging.INFO, format="%(message)s")

def _load_library_extensions():
	"""
	Locate all setuptools entry points by the name 'pmxbot_handlers'
	and initialize them.
	Any third-party library may register an entry point by adding the
	following to their setup.py::

		entry_points = {
			'pmxbot_handlers': [
				'plugin_name = mylib.mymodule:initialize_func',
			],
		},

	`plugin_name` can be anything, and is only used to display the name
	of the plugin at initialization time.
	"""

	try:
		import pkg_resources
	except ImportError:
		log.warning('setuptools not available - entry points cannot be '
			'loaded')
		return

	group = 'pmxbot_handlers'
	entry_points = pkg_resources.iter_entry_points(group=group)
	for ep in entry_points:
		try:
			log.info('Loading %s', ep.name)
			init_func = ep.load()
			if callable(init_func):
				init_func()
		except Exception:
			log.exception("Error initializing plugin %s." % ep)

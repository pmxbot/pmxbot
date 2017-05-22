#!/usr/bin/env python

# Project skeleton maintained at https://github.com/jaraco/skeleton

import io

import setuptools

with io.open('README.rst', encoding='utf-8') as readme:
	long_description = readme.read()

name = 'pmxbot'
description = 'IRC bot - full featured, yet extensible and customizable'

params = dict(
	name=name,
	use_scm_version=True,
	author="YouGov, Plc.",
	author_email="dev@yougov.com",
	maintainer="Jason R. Coombs",
	maintainer_email="jaraco@jaraco.com",
	description=description or name,
	long_description=long_description,
	url="https://github.com/yougov/" + name,
	packages=setuptools.find_packages(),
	include_package_data=True,
	namespace_packages=['pmxbot'],
	install_requires=[
		"requests",
		"pyyaml",
		"feedparser",
		"pytz",
		"beautifulsoup4",
		"jaraco.compat>=1.0.3",
		"backports.method_request",
		"wordnik-py3",
		"more_itertools",
		"jaraco.timing",
		"tempora",
		"jaraco.collections>=1.5",
		"jaraco.itertools",
		"jaraco.context",
		"jaraco.classes",
		"jaraco.functools",
		"inflect",
		"python-dateutil",
	],
	extras_require={
		'mongodb': ['pymongo>=3'],
		'viewer': ['cherrypy>=3.2.3', 'jinja2'],
		'slack': ['slackclient', 'slacker'],
		'irc': ['irc>=15.0,<16dev'],
		'newrelic': ['yg.newrelic>=1.13,<2dev'],
	},
	setup_requires=[
		'setuptools_scm>=1.15.0',
		'wheel>=0.25.0',
	],
	classifiers=[
		"Development Status :: 5 - Production/Stable",
		"License :: OSI Approved :: MIT License",
		"Programming Language :: Python :: 3",
		"Topic :: Communications :: Chat :: Internet Relay Chat",
		"Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
	],
	entry_points={
		'console_scripts': [
			'pmxbot=pmxbot.core:run',
			'pmxbotweb=pmxbot.web.viewer:run',
		],
		'pmxbot_handlers': [
			'pmxbot logging = pmxbot.logging:Logger.initialize',
			'pmxbot karma = pmxbot.karma:Karma.initialize',
			'pmxbot quotes = pmxbot.quotes:Quotes.initialize',
			'pmxbot core commands = pmxbot.commands',
			'pmxbot notifier = pmxbot.notify:Notify.init',
			'pmxbot rolls = pmxbot.rolls:ParticipantLogger.initialize',
			'pmxbot config = pmxbot.config_',
			'pmxbot system commands = pmxbot.system',
			'pmxbot say something = pmxbot.saysomething:FastSayer.init_in_thread',
		],
	},
)
if __name__ == '__main__':
	setuptools.setup(**params)

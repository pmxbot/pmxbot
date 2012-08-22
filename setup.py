# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:noexpandtab
# c-basic-indent: 4; tab-width: 4; indent-tabs-mode: true;
import sys

import setuptools

py26reqs = ['importlib'] if sys.version_info < (2, 7) else []

setup_params = dict(
	name="pmxbot",
	use_hg_version=True,
	packages=setuptools.find_packages(),
	include_package_data=True,
	entry_points=dict(
		console_scripts = [
			'pmxbot=pmxbot.pmxbot:run',
			'pmxbotweb=pmxbotweb.pmxbotweb:run',
		],
		pmxbot_handlers = [
			'pmxbot notifier = pmxbot.notify:Notify.init',
			'pmxbot feedparser = pmxbot.rss:RSSFeeds',
		],
	),
	install_requires=[
		"irc>=2.0,<3.0dev",
		"popquotes>=1.1",
		"excuses>=1.1.2",
		"pyyaml",
		"feedparser",
		"pytz",
		"wordnik>=2.0,<3.0",
		#for viewer
		"jinja2",
		"cherrypy",
	] + py26reqs,
	description="IRC bot - full featured, yet extensible and customizable",
	license = 'MIT',
	author="YouGov, Plc.",
	author_email="open.source@yougov.com",
	maintainer = 'Jason R. Coombs',
	maintainer_email = 'Jason.Coombs@YouGov.com',
	url = 'http://bitbucket.org/yougov/pmxbot',
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'License :: OSI Approved :: MIT License',
		'Operating System :: POSIX',
		'Operating System :: Microsoft :: Windows',
		'Operating System :: MacOS :: MacOS X',
		'Programming Language :: Python :: 2.6',
		'Programming Language :: Python :: 2.7',
		'Topic :: Communications :: Chat :: Internet Relay Chat',
		'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
	],
	long_description = open('README').read(),
	setup_requires=[
		'hgtools',
		'pytest-runner',
	],
	tests_require=[
		'pymongo',
		'pytest',
	],
)

if __name__ == '__main__':
	setuptools.setup(**setup_params)

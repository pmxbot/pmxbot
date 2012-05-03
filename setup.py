# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:noexpandtab
# c-basic-indent: 4; tab-width: 4; indent-tabs-mode: true;
from setuptools import find_packages

setup_params = dict(
	name="pmxbot",
	use_hg_version=True,
	packages=find_packages(),
	include_package_data=True,
	entry_points=dict(
		console_scripts = [
			'pmxbot=pmxbot.pmxbot:run',
			'pmxbotweb=pmxbotweb.pmxbotweb:run',
		],
		pmxbot_handlers = [
			'pmxbot notifier = pmxbot.notify:Notify.init'
		],
	),
	install_requires=[
		"popquotes>=1.1",
		"excuses>=1.1.2",
		"pyyaml",
		"irc>=0.7b1,<2.0dev",
		"httplib2",
		"feedparser",
		"pytz",
		"wordnik==2.0dev-rb0221ccc",
		#for viewer
		"jinja2",
		"cherrypy",
	],
	dependency_links=[
		'https://bitbucket.org/jaraco/httplib2/downloads',
		'https://github.com/jaraco/wordnik-python/downloads',
	],
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
	],
)

if __name__ == '__main__':
	from setuptools import setup
	setup(**setup_params)

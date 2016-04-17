# vim:ts=4:sw=4:noexpandtab
# c-basic-indent: 4; tab-width: 4; indent-tabs-mode: true;

import setuptools

setup_params = dict(
	name="pmxbot",
	use_scm_version=True,
	packages=setuptools.find_packages(),
	include_package_data=True,
	entry_points=dict(
		console_scripts=[
			'pmxbot=pmxbot.core:run',
			'pmxbotweb=pmxbot.web.viewer:run',
		],
		pmxbot_handlers=[
			'pmxbot logging = pmxbot.logging:Logger.initialize',
			'pmxbot karma = pmxbot.karma:Karma.initialize',
			'pmxbot quotes = pmxbot.quotes:Quotes.initialize',
			'pmxbot core commands = pmxbot.commands',
			'pmxbot notifier = pmxbot.notify:Notify.init',
			'pmxbot feedparser = pmxbot.rss:RSSFeeds',
			'pmxbot rolls = pmxbot.rolls:ParticipantLogger.initialize',
			'pmxbot config = pmxbot.config_',
			'pmxbot system commands = pmxbot.system',
			'pmxbot say something = pmxbot.saysomething:FastSayer.init_in_thread',
		],
	),
	install_requires=[
		"irc>=14.2,<15dev",
		'requests',
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
		"jaraco.collections",
		"jaraco.itertools",
		"jaraco.context",
		"jaraco.classes",
		"jaraco.functools",
		"inflect",

		# for viewer
		"cherrypy>=3.2.3",
		"jinja2",
	],
	extras_require={
	},
	description="IRC bot - full featured, yet extensible and customizable",
	author="YouGov, Plc.",
	author_email="open.source@yougov.com",
	maintainer='Jason R. Coombs',
	maintainer_email='Jason.Coombs@YouGov.com',
	url='https://github.com/yougov/pmxbot',
	classifiers=[
		'Development Status :: 5 - Production/Stable',
		'License :: OSI Approved :: MIT License',
		'Operating System :: POSIX',
		'Operating System :: Microsoft :: Windows',
		'Operating System :: MacOS :: MacOS X',
		'Programming Language :: Python :: 3',
		'Topic :: Communications :: Chat :: Internet Relay Chat',
		'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
	],
	long_description=open('README.rst').read(),
	setup_requires=[
		'setuptools_scm',
		'pytest-runner>=2.1',
	],
	tests_require=[
		'pymongo>=3',
		'pytest',
		'jaraco.test>=2.0.4',
		'more_itertools',
	],
)

if __name__ == '__main__':
	setuptools.setup(**setup_params)

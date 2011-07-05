from setuptools import setup

setup(
	name="pmxbot",
	version="1100b2",
	packages=["pmxbot", "pmxbotweb", "pmxbot.popquotes"],
	package_data={
		'pmxbot' : ["popquotes.sqlite",],
		'pmxbotweb' : ["templates/*.html", "templates/pmxbot.png",],
	},
	entry_points=dict(
		console_scripts = [
			'pmxbot=pmxbot.pmxbot:run',
			'pmxbotweb=pmxbotweb.pmxbotweb:run',
		],
	),
	install_requires=[
		"pyyaml",
		"python-irclib",
		"httplib2",
		"feedparser",
		"pytz",
		#for viewer
		"jinja2",
		"cherrypy",
	],
	description="IRC bot - full featured, yet extensible and customizable",
	license = 'MIT',
	author="You Gov, Plc. (jamwt, mrshoe, cperry, chmullig, and others)",
	author_email="open.source@yougov.com",
	maintainer = 'chmullig',
	maintainer_email = 'chmullig@gmail.com',
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
)

from setuptools import setup

setup(name="pmxbot",
    version="1002-beta",
    packages=["pmxbot"],
    package_data={'pmxbot' : ["popquotes.sqlite"]},
    entry_points={
            'console_scripts' : 
'''
pmxbot=pmxbot.pmxbot:run
pmxbotweb=pmxbotweb.pmxbotweb:run
'''
    },
    install_requires=[
        "pyyaml",
        "python-irclib",
        "simplejson",
        "httplib2",
        "feedparser",
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
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.5',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
    ],
    long_description = """
    pmxbot
    ======
    
    pmxbot is an IRC bot written in python. Originally built for internal use,
    it's been sanitized and set free upon the world.
    
    
    Commands
    ========
    pmxbot listens to commands prefixed by a '!'
    If it's a command it knows it will reply, take an action, etc.
    It can search the web, quote you, track karma, make decisions,
    and do just about anything else you could want. It logs text in a sqlite3
    database, and eventually we'll write a web interface to it.

    Web
    ===
    pmxbotweb is the web interface to view and search all the logs.
    """,
    )
    

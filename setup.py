from setuptools import setup

setup(name="pmxbot",
    version="1001",
    author="You Gov, Plc. (jamwt, mrshoe, cperry, chmullig, and others)",
    author_email="open.source@yougov.com",
    packages=["pmxbot"],
    package_data={'pmxbot' : ["popquotes.sqlite"]},
    entry_points={
            'console_scripts' : 
'''
pmxbot=pmxbot.pmxbot:run
'''
    },
    install_requires=[
        "pyyaml",
        "python-irclib",
        "simplejson",
        "httplib2",
        "feedparser",
    ]
    )
    

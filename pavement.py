
import pkg_resources
# from jaraco.develop import bitbucket
from paver.easy import task

import pmxbot.core
import pmxbot.web.viewer


def to_wiki(commands):
	yield '|= Command |= Aliases |= Description |'
	for command, doc, aliases in commands:
		aliases = ', '.join(repr(alias.name) for alias in aliases)
		doc = doc.replace('|', '~|')
		yield '| {command} | {aliases} | {doc} |'.format(**vars())


@task
def update_wiki():
	pmxbot.core._load_library_extensions()
	pmxbot.web.viewer._init_config()
	ctx = pmxbot.web.viewer.HelpPage.get_context()
	commands = ctx['commands']
	project = 'yougov/pmxbot'
	title = 'Home'
	path = 'home.wiki'
	req = pkg_resources.require('pmxbot')
	usage = pkg_resources.resource_stream('pmxbot', 'example usage.txt')
	content = home_wiki % dict(
		commands='\n'.join(to_wiki(commands)),
		usage=usage.read(),
		version=req[0].version,
	)
	# api is broken, so copy/paste
	# bitbucket.update_wiki(project, title, path, content)
	print("You need to update the wiki yourself: ")
	print(content)

home_wiki = """
== Welcome ==
{{https://bitbucket.org/yougov/pmxbot/raw/8af8328a91ce/pmxbotweb/templates/pmxbot.png|pmxbot skynet logo}}{{https://bitbucket.org/yougov/pmxbot/raw/tip/horrible-logos-pmxbot.gif|pmxbot horrible logo}}

Welcome to pmxbot!

== Feature List ==
While pmxbot's feature set is always growing and changing, here's a list of the current features included as part of version %(version)s.

%(commands)s

== Example Session ==
It's sometimes hard to get a sense of what pmxbot is like if you've never used it, so here's an example IRC discussion where we heavily use pmxbot.

{{{
%(usage)s
}}}
"""

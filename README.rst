.. image:: https://img.shields.io/pypi/v/pmxbot.svg
   :target: https://pypi.org/project/pmxbot

.. image:: https://img.shields.io/pypi/pyversions/pmxbot.svg

.. image:: https://img.shields.io/pypi/dm/pmxbot.svg

.. image:: https://img.shields.io/travis/yougov/pmxbot/master.svg
   :target: http://travis-ci.org/yougov/pmxbot


pmxbot is an IRC bot written in python. Originally built for internal use,
it's been sanitized and set free upon the world. You can find out more details
on `the project website <https://github.com/yougov/pmxbot>`_.

License
=======

License is indicated in the project metadata (typically one or more
of the Trove classifiers). For more details, see `this explanation
<https://github.com/jaraco/skeleton/issues/1>`_.

Commands
========

pmxbot listens to commands prefixed by a '!'
If it's a command, it knows it will reply, take an action, etc.
It can search the web, store quotes you, track karma, make decisions,
and do just about anything else you could want. It stores logs and quotes
and karma in either a sqlite or MongoDB
database, and there's a web interface for reviewing the logs and karma.

Contains
========

pmxbot will respond to things you say if it detects words and phrases it's
been told to recognize. For example, mention sql on rails.

Requirements
============

`pmxbot` requires Python 3. It also requires a few python packages as defined
in setup.py.

If using the MongoDB backend, it requires pymongo (otherwise, sqlite will
be used).

Testing
=======

`pmxbot` includes a test suite that does some functional tests written against
the Python IRC server and quite a few unit tests as well. Install
`tox <https://pypi.org/project/tox>`_ and run ``tox`` to invoke the tests.

Configuration
=============
Configuration is based on very easy YAML files. Check out config.yaml in the
source tree for an example.

Usage
=====
Once you've setup a config file, you just need to call ``pmxbot config.yaml``
and it will join and connect. We recommend running pmxbot under
daemontools, upstart, supervisord, or your favorite supervisor to make it
automatically restart if it crashes (or terminates due to a planned
restart).


Custom Features
===============

Setuptools Entry Points Plugin
------------------------------

`pmxbot` provides an extension mechanism for adding commands, and uses this
mechanism even for its own built-in commands.

To create a setuptools (or distribute or compatible packaging tool)
entry point plugin, package your modules using
the setuptools tradition and install it alongside pmxbot. Your package
should define an entry point in the group `pmxbot_handlers` by including
something similar to the following in the package's setup.py::

    entry_points = {
        'pmxbot_handlers': [
            'plugin name = pmxbot.mymodule',
        ],
    },

During startup,
pmxbot will load `pmxbot.mymodule`. `plugin name` can be anything, but should
be a name suitable to identify the plugin (and it will be displayed during
pmxbot startup).

Note that the ``pmxbot`` package is a namespace package, and you're welcome
to use that namespace for your plugin.

If your plugin requires any initialization, specify an initialization function
(or class method) in the entry point. For example::

    'plugin name = pmxbot.mymodule:initialize_func'

On startup, pmxbot will call `initialize_func` with no parameters.

Within the script you'll want to import the decorates you need to use with:
`from pmxbot.core import command, contains, regexp, execdelay, execat`. You'll
then decorate each function with the appropriate line so pmxbot registers it.

A command (!g) gets the @command decorator::

  @command(aliases=('tt', 'tear', 'cry'))
  def tinytear(client, event, channel, nick, rest):
    "I cry a tiny tear for you."
    if rest:
      return "/me sheds a single tear for %s" % rest
    else:
      return "/me sits and cries as a single tear slowly trickles down its cheek"

A response (when someone says something) uses the @contains decorator::

  @contains("sqlonrails")
  def yay_sor(client, event, channel, nick, rest):
    karma.Karma.store.change('sql on rails', 1)
    return "Only 76,417 lines..."

A more complicated response (when you want to extract data from a message) uses
the @regexp decorator::

  @regexp("jira", r"(?<![a-zA-Z0-9/])(OPS|LIB|SALES|UX|GENERAL|SUPPORT)-\d\d+")
  def jira(client, event, channel, nick, match_obj):
    return "https://jira.example.com/browse/%s" % match_obj.group()

For an example of how to implement a setuptools-based plugin, see one of the
many examples in the pmxbot project itself or one of the popular third-party
projects:

 - `motivation <https://bitbucket.org/yougov/motivation>`_.
 - `wolframalpha <https://github.com/jaraco/wolframalpha>`_.
 - `jaraco.translate <https://bitbucket.org/jaraco/jaraco.translate>`_.
 - `excuses <https://bitbucket.org/yougov/excuses>`_.

Web Interface
=============
pmxbot includes a web server for allowing users to view the logs, read the
help, and check karma. You specify the host, port, base path, logo, title,
etc with the same YAML config file. Just run like ``pmxbotweb config.yaml``
and it will start up. Like pmxbot, use of a supervisor is recommended to
restart the process following termination.

pmxbot as a Slack bot
=====================

As Slack provides an IRC interface, it's easy to configure pmxbot for use
in Slack. Here's how:

1. `Enable the IRC Gateway <https://slack.zendesk.com/hc/en-us/articles/201727913-Connecting-to-Slack-over-IRC-and-XMPP>`.
2. Create an e-mail for the bot.
3. Create the account for the bot in Slack and activate its account.
4. Log into Slack using that new account and `get the IRC gateway
   password <https://my.slack.com/account/gateways>` for that
   account.
5. Configure the pmxbot as you would for an IRC server, but use these
   settings for the connection:

    message rate limit: 2.5
    password: <gateway password>
    server_host: <team name>.irc.slack.com
    server_port: 6667

   The rate limit is necessary because Slack will kick the bot if it issues more than 25 messages in 10 seconds, so throttling it to 2.5 messages per
   second avoids hitting the limit.
6. Consider leaving 'log_channels' and 'other_channels' empty, especially
   if relying on Slack logging. Slack will automatically re-join pmxbot to
   any channels to which it has been ``/invited``.

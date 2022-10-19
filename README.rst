.. image:: https://img.shields.io/pypi/v/pmxbot.svg
   :target: `PyPI link`_

.. image:: https://img.shields.io/pypi/pyversions/pmxbot.svg
   :target: `PyPI link`_

.. _PyPI link: https://pypi.org/project/pmxbot

.. image:: https://github.com/pmxbot/pmxbot/workflows/tests/badge.svg
   :target: https://github.com/pmxbot/pmxbot/actions?query=workflow%3A%22tests%22
   :alt: tests

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: Black

.. image:: https://readthedocs.org/projects/pmxbot/badge/?version=latest
   :target: https://pmxbot.readthedocs.io/en/latest/?badge=latest

.. image:: https://img.shields.io/badge/skeleton-2022-informational
   :target: https://blog.jaraco.com/skeleton

.. image:: https://tidelift.com/badges/package/pypi/pmxbot
   :target: https://tidelift.com/subscription/pkg/pypi-pmxbot?utm_source=pypi-pmxbot&utm_medium=readme

pmxbot is bot for IRC and Slack written in
`Python <https://python.org>`_. Originally built for internal use
at `YouGov <https://yougov.com/>`_,
it's been sanitized and set free upon the world. You can find out more details
on `the project website <https://github.com/pmxbot/pmxbot>`_.

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
in setup.py. Some optional dependencies are installed with
`extras
<https://packaging.python.org/installing/#installing-setuptools-extras>`_:

- mongodb: Enable MongoDB persistence (instead of sqlite).
- irc: IRC bot client.
- slack: Slack bot client.
- viewer: Enable the web viewer application.

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
your favorite process supervisor to make it
automatically restart if it crashes (or terminates due to a planned
restart).

Custom Features
===============

Setuptools Entry Points Plugin
------------------------------

``pmxbot`` provides an extension mechanism for adding commands, and uses this
mechanism even for its own built-in commands.

To create a setuptools
entry point plugin, package your modules using
the setuptools tradition and install it alongside pmxbot. Your package
should define an entry point in the group ``pmxbot_handlers`` by including
something similar to the following in the package's setup.py::

    entry_points = {
        'pmxbot_handlers': [
            'plugin name = pmxbot.mymodule',
        ],
    },

During startup,
pmxbot will load ``pmxbot.mymodule``. ``plugin name`` can be anything, but should
be a name suitable to identify the plugin (and it will be displayed during
pmxbot startup).

Note that the ``pmxbot`` package is a namespace package, and you're welcome
to use that namespace for your plugin (e.g.
`pmxbot.nsfw <https://github.com/pmxbot/pmxbot.nsfw>`_).

If your plugin requires any initialization, specify an initialization function
(or class method) in the entry point. For example::

    'plugin name = pmxbot.mymodule:initialize_func'

On startup, pmxbot will call ``initialize_func`` with no parameters.

Within the script you'll want to import the decorator(s) you need to use with::

    from pmxbot.core import command, contains, regexp, execdelay, execat`.

You'll
then decorate each function with the appropriate line so pmxbot registers it.

A command (!g) gets the @command decorator::

  @command(aliases=('tt', 'tear', 'cry'))
  def tinytear(rest):
    "I cry a tiny tear for you."
    if rest:
      return "/me sheds a single tear for %s" % rest
    else:
      return "/me sits and cries as a single tear slowly trickles down its cheek"

A response (when someone says something) uses the @contains decorator::

  @contains("sqlonrails")
  def yay_sor():
    karma.Karma.store.change('sql on rails', 1)
    return "Only 76,417 lines..."

Each handler may solicit any of the following parameters:

 - channel (the channel in which the message occurred)
 - nick (the nickname that triggered the command or behavior)
 - rest (any text after the command)

A more complicated response (when you want to extract data from a message) uses
the @regexp decorator::

    @regexp("jira", r"(?<![a-zA-Z0-9/])(OPS|LIB|SALES|UX|GENERAL|SUPPORT)-\d\d+")
    def jira(client, event, channel, nick, match):
        return "https://jira.example.com/browse/%s" % match.group()

For an example of how to implement a setuptools-based plugin, see one of the
many examples in the pmxbot project itself or one of the popular third-party
projects:

 - `motivation <https://github.com/pmxbot/motivation>`_.
 - `wolframalpha <https://github.com/jaraco/wolframalpha>`_.
 - `jaraco.translate <https://github.com/jaraco/jaraco.translate>`_.
 - `excuses <https://github.com/pmxbot/excuses>`_.

Web Interface
=============

pmxbot includes a web server for allowing users to view the logs, read the
help, and check karma. You specify the host, port, base path, logo, title,
etc with the same YAML config file. Just run like ``pmxbotweb config.yaml``
and it will start up. Like pmxbot, use of a supervisor is recommended to
restart the process following termination.

pmxbot as a Slack bot (native)
==============================

To use pmxbot as a Slack bot, install with ``pmxbot[slack]``,
and set ``slack token`` in your config to the token from your
`Bot User <https://api.slack.com/bot-users>`_. Easy, peasy.

pmxbot as a Slack bot (IRC)
===========================

As Slack provides an IRC interface, it's easy to configure pmxbot for use
in Slack. Here's how:

0. Install with ``pmxbot[irc]``.
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

For Enterprise
==============

Available as part of the Tidelift Subscription.

This project and the maintainers of thousands of other packages are working with Tidelift to deliver one enterprise subscription that covers all of the open source you use.

`Learn more <https://tidelift.com/subscription/pkg/pypi-pmxbot?utm_source=pypi-pmxbot&utm_medium=referral&utm_campaign=github>`_.

Security Contact
================

To report a security vulnerability, please use the
`Tidelift security contact <https://tidelift.com/security>`_.
Tidelift will coordinate the fix and disclosure.

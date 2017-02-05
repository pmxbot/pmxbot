1117.3.4
========

* #51: Restore insult command by updating URL for autoinsult.

1117.3.3
========

* Declare missing dependency on python-dateutil, introduced
  in 1117.3.

1117.3.2
========

* #49: Fix infinitite recursion when comparing a command
  and its aliases.

1117.2.4
========

* Fix error in FullTextMongoDBLogger sort.

1117.2.3
========

* In FullTextMongoDBLogger, sort results by relevance and
  limit results to 200.

1117.2.2
========

* Fix error logging in web viewer.

1117.2.1
========

* Fix error where ``log`` meant two things in the logging
  module.

1117.2
======

* During logging initialization, log which logger class
  is being used.

1117.1
======

* Bot defaults to Slack if 'slack token' appears in the
  config.

1117.0
======

* Preliminary Slack support is now available. Simply
  set following in the config:

  - slack token: <your bot auth token>
  - bot class: pmxbot.slack:Bot

* Handler functions now are only ever passed None
  for the client, connection, and event parameters.
  Plugins are adviced to rely only on channel, nick,
  and rest.

* ``execdelay`` and ``execat`` no longer accept ``args``
  parameters.

1116.0
======

* Handler functions no longer solicit positional arguments
  but instead should solicit whatever parameters they
  require. Functions using the following names will
  continue to work as before::

    def handler(client, event, channel, nick, rest)

  But handlers not needing all of those parameters should
  remove the unused names, e.g.::

    @pmxbot.command
    def handler(nick):
        return "Hello, " + nick

* RSS support has been moved to the
  `pmxbot.rss <https://pypi.org/project/pmxbot.rss>`_
  plugin.

1115.5
======

* Add a pluggable filter system. Now any library can
  expose any number of "pmxbot_filters" entry points,
  each pointing to a callable accepting
  ``(channel, message)``. If any filter returns
  anything other than a truthy value, the message will
  not be transmitted.

1115.4.1
========

* Re-release for improper tag/merge.

1115.4
======

* #47: !password now generates more secure passwords.

1115.3
======

* Add ``delete`` support to quotes command (currently
  only for MongoDB storage).

1115.2.1
========

* Fix bug in log viewer startup.

1115.2
======

* Issue #38: Google Search now works again, but requires
  an API key. Request an API key for your deployment
  and set the 'Google API key' config variable to that
  value to restore the !g command.
* Moved most of the logging logic into the ``logging``
  module, making it an optional module that could be
  extracted to a separate package except for dependencies
  in the viewer and saysomething modules.
* Added a new ``core.ContentHandler`` message
  handler, suitable for handling any messages that passes
  through the bot.

1115.1
======

* ``rand_bot`` commands can now be configured in the
  ``random commands`` config variable. Because it now
  resolves commands by name, it's possible for rand_bot
  to now respond with commands from other plugins.

1115.0
======

* Dropped support for Python 3.2.

1114.0
======
* Moved paste command to librarypaste package.
  Require it in your deployment to retain the paste command.
* Removed support for 'silent_bot' config variable. Instead,
  to override the default command bot, pass the path to the
  class as ``"bot class": "pmxbot.irc:SilentCommandBot"``.
* Removed implicit construction of ``pmxbot.config``. Instead,
  that ConfigDict is constructed explicitly during initialization
  of the bot or the viewer.

1113.6
======

* Add missing import

1113.5
======

* Fix `saysomething` command

1113.4
======

* Unpin upper dependency on CherryPy, allowing later versions
  to be used.

1113.3
======

* Remove use of 8ball delegator. Its responses are not nearly
  as interesting (or correct) as pmxbot's own.

1113.2
======

* Use `8ball delegator <https://8ball.delegator.com>`_ for
  ``!8`` command.

1113.1
======

* Restored support for versions of MongoDB earlier than 2.6
  because we <3 #dcpython.

1113.0
======

* Fixed full text search on MongoDB 3.0 and later. For full text
  support, pmxbot now requires MongoDB 2.6 or later.

1112.2
======

* Moved hosting to Github.
* Restored support for installing to Python 3.2 by installing old
  versions of Jinja2.

1112.1
======

* Log an exception when failing to schedule an action.

1112.0
======

* Bump to IRC 13.0. Scheduled commands now must be timezone aware.

1111.1
======

* Added ability to rate-limit outgoing mesasges. Set ``message rate limit``
  to a non-infinite value to restrict messages to that many per second.

1111.0
======

* MongoDB based deployments now require PyMongo 3.

1110.7
======

* Linking karma values will now always create both names in the
  Karma database if they don't already exist.
* Fixed broken stock quotes.

1110.3
======

* Scheduled commands with the same arguments are now suppressed on subsequent
  invocations of ``_schedule_at``. This prevents duplicate scheduled
  notifications on systems such as Slack.

1110.2
======

* Bump requirement on ``irc`` 10.

1110.1
======

* Allow ``irc`` 9 and 10.

1110.0
======

* Issue #20: Removed time and weather commands. They depended on a brittle
  and deprecated Google service. Contributors are welcome to share a
  replacement implementation.

1109.3
======

* Improved FastSayer startup time on MongoDB when logs database is millions
  of rows.

1109.0
======

* Dropped support for Python 2.

1108.0
======

* ``popquotes`` and ``excuses`` are removed from the package. Include them
  explicitly in your deployment to maintain compatibility.

1107.4
======

* ``paste`` command now allows for auth to be provided.

1107.1
======

* ``saysomething`` no longer requires 30 seconds to startup, but will time
  out waiting for the quotes and logging to startup after 30 seconds.

1107.0
======

* ``pmxbot.core.AliasHandler`` now expects a 'parent' argument referring to
  the parent command. The ``doc`` parameter is no longer honored, but instead
  refers to ``parent.doc``. Commands that construct AliasHandlers explicitly
  will need to be updated, though no known implementations do so.
* ``commands`` will now defer to the decorated function's docstring for the
  command help if no doc is supplied. So now the following are equivalent::

    @command('something', doc='do something special')
    def func(...):
        return 'something'

    @command('foo')
    def func(...):
        """
        do something
        special
        """
        return 'something'

1106.2
======

* Use wordnik-py3 on Python 3

1106.1.2
========

* Fix issue in new MongoDBFullTextLogger where docs weren't processed.

1106.1.1
========

* Fix issue in log search on Python 3.

1106.1
======

* Added MongoDBFullTextLogger, leveraging MongoDB Full Text Search on MongoDB
  2.4 or later (if enabled).

1106
====

* Removed !googlecalc, which depended on iGoogle, now defunct.
* Restored !urbandict using the API instead of HTML scraping.

1105.7
======

* Include channel in hyperlink for logs for logged channels.

1105.6
======

* Added support for logging leave events as well as join events.
* Added a new ``@on_leave`` decorator, suitable for implementing custom
  handlers for leave events.
* ``pmxbot`` command now optionally accepts multiple config files.

1105.5
======

* Added support for keepalives. To enable, set the 'TCP keepalive' config
  value to a non-zero number of seconds or a period string like '3 minutes'.
  If configured correctly, pmxbot will report during startup the interval
  that it detected, and every interval, it will send a 'ping' message to the
  server.
* Issue #27: Fix display of aliases in web help.
* Added a version command to get the pmxbot version or version of other
  package in the environment.

1105.3
======

* Allow keyword arguments to @regexp decorator.

1105.2
======

* Added `pmxbot.core.FinalRegistry` for registering callback functions to be
  called when the bot exits.

1105.1
======

* Extracted `RSSFeeds.format_entry`.

1105.0
======

* Added `pmxbot.core.SwitchChannel`. Handlers can yield this sentinel,
  constructed with the name of a new channel, to cause subsequest messages
  to be sent on the indicated channel.
* Removed db_uri from LoggingCommandBot (attribute and constructor).
  Clients that invoke the constructor or expect the attribute to be present
  will need to be updated to use the value from the config instead.

1104.4
======

* Refactored FeedHistory, allowing for other classes to re-use the history
  concept in other RSS handlers.
* Exposed the bot instance as `pmxbot.core._bot` (experimental).

1104.3
======

* New @regexp decorator. Similar to @contains, except allows regular
  expressions instead of simple string matching. See the README for an example
  of usage. Thanks to `Craig Wright <https://bitbucket.org/crw>`_ for the
  contribution.

1104.2
======

* pmxbot will assume local host name is appropriate for logs URL if no logs
  URL is specified in the config.

1104.1
======

* One may now specify the database name in the URI.
* pmxbot will log the config when starting up.

1104
====

* Updated to work with irc 5.0

1103.6
======

* @contains decorator has a new keyword parameter: `allow_chain`. Set to True
  to allow subsequent @contains decorators to match.
* Issue #18: Strip periods from acronym, fixing errors from remote service.

1103.5
======

* Now use irc 3.3.
* Python 3 bug fixes.

1103.4
======

* Updated to irc 3.1.
* Replaced cleanhtml with BeautifulSoup.
* Preliminary Python 3 support (compiles and runs).

1103.3
======

* Initial support for logging joins/parts in logged channels.

1103.2
======

* Added !logs command to query for the location of the logs.

1103.1
======

* Moved config to 'pmxbot.config'.
* Config parameter no longer required.

1103
====

This release incorporates another substantial refactor. The `pmxbotweb`
package is being removed in favor of the namespaced-package `pmxbot.web`.

Additionally, config entries for the pmxbotweb command have been renamed::

 - `web_host` is now simply `host`
 - `web_port` is now simply `port`

A backward-compatibility shim has been added to support the old config values
until version 1104.

The backward compatibile module `pmxbot.botbase` has been removed.

1102
====

Build 1102 of `pmxbot` involves some major refactoring to normalize the
codebase and improve stability.

With version 1102, much of the backward compatibility around quotes and karma
has been removed::

 - The Karma store must now be referenced as `pmxbot.karma:Karma.store` (a
   class attribute). It is no longer available as `pmxbot.pmxbot:karma` nor
   `pmxbot.util:karma` nor `pmxbot.karma.karma`.
 - Similarly, the Quotes store must now be referenced as
   `pmxbot.quotes:Quotes.store` (a class attribute).
 - Similarly, the Logger store must now be referenced as
   `pmxbot.logging:Logger.store` instead of `pmxbot.botbase.logger`.

Other backward-incompatible changes::

 - The `config` object has been moved into the parent `pmxbot` package.
 - A sqlite db URI must always specify the full path to the database file;
   pmxbot will no longer accept just the directory name.

Other changes::

 - Renamed `pmxbot.botbase` to `pmxbot.core`. A backward-compatibility
   `botbase` module is temporarily available to provide access to the public
   `command`, `execdelay`, and similar decorators.

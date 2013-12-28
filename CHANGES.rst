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

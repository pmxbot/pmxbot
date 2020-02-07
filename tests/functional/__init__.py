import subprocess
import os
import sys
import time
import sqlite3
import datetime
import urllib.parse

import irc.client
import pytest
import tempora.timing

import pmxbot.dictlib


class TestingClient:
    """
    A simple client simulating a user other than the pmxbot
    """

    def __init__(self, server, port, nickname):
        self.reactor = irc.client.Reactor()
        self.c = self.reactor.server()
        self.c.connect(server, port, nickname)
        self.reactor.process_once(0.1)
        self.channels = set()

    def join(self, channel):
        self.c.join(channel)
        self.channels.add(channel)

    def send_message(self, channel, message):
        if channel not in self.channels:
            self.join(channel)
        self.c.privmsg(channel, message)
        time.sleep(0.05)


class PmxbotHarness:
    config = pmxbot.dictlib.ConfigDict(
        server_port=6668,
        bot_nickname='pmxbotTest',
        log_channels=['#logged'],
        other_channels=['#inane'],
        database="sqlite:tests/functional/pmxbot.sqlite",
    )

    @classmethod
    def setup_class(cls):
        """Start an IRC server, launch the bot, and ask it to do stuff"""
        path = os.path.dirname(os.path.abspath(__file__))
        cls.config_fn = os.path.join(path, 'testconf.yaml')
        cls.config.to_yaml(cls.config_fn)
        cls.dbfile = urllib.parse.urlparse(cls.config['database']).path
        cls.db = sqlite3.connect(cls.dbfile)
        env = os.environ.copy()
        # copy the current sys.path to PYTHONPATH so subprocesses have access
        #  to libs pulled by tests_require
        env['PYTHONPATH'] = os.pathsep.join(sys.path)
        try:
            cmd = [sys.executable, '-m', 'irc.server', '-p', '6668', '-l', 'debug']
            cls.server = subprocess.Popen(cmd, env=env)
        except OSError:
            pytest.skip("Unable to launch irc server.")
        time.sleep(0.5)
        # add './plugins' to the path so we get some pmxbot commands specific
        #  for testing.
        plugins = os.path.join(path, 'plugins')
        env['PYTHONPATH'] = os.pathsep.join([plugins, env['PYTHONPATH']])
        try:
            # Launch pmxbot using Python directly (rather than through
            #  the console entry point, which can't be properly
            #  .terminate()d on Windows.
            cmd = [sys.executable, '-m', 'pmxbot', cls.config_fn]
            cls.bot = subprocess.Popen(cmd, env=env)
        except OSError:
            pytest.skip("Unable to launch pmxbot (pmxbot must be installed)")
        cls.wait_for_tables()
        cls.wait_for_output()
        if cls.bot.poll() is not None:
            pytest.skip("Bot did not start up properly")
        cls.client = TestingClient('localhost', 6668, 'testingbot')

    @classmethod
    def wait_for_output(cls):
        """
        Wait for 'Running with config' in cls.bot.output
        """
        if cls.bot.poll() is not None:
            return
        # stubbed
        time.sleep(5)

    @classmethod
    def wait_for_tables(cls, timeout=30):
        watch = tempora.timing.Stopwatch()
        while watch.split() < datetime.timedelta(seconds=timeout):
            try:
                cls.check_logs('#check')
                return
            except Exception:
                # short-circuit if the bot has stopped
                if cls.bot.poll() is not None:
                    return
                time.sleep(0.2)

    @classmethod
    def check_logs(cls, channel='', nick='', message=''):
        if channel.startswith('#'):
            channel = channel[1:]
        time.sleep(0.1)
        cursor = cls.db.cursor()
        query = "select * from logs where 1=1"
        if channel:
            query += " and channel = :channel"
        if nick:
            query += " and nick = :nick"
        if message:
            query += " and message = :message"
        cursor.execute(query, dict(channel=channel, nick=nick, message=message))
        res = cursor.fetchall()
        print(res)
        return len(res) >= 1

    @classmethod
    def teardown_class(cls):
        os.remove(cls.config_fn)
        if hasattr(cls, 'bot') and not cls.bot.poll():
            cls.bot.terminate()
            cls.bot.wait()
        if hasattr(cls, 'server') and cls.server.poll() is None:
            cls.server.terminate()
            cls.server.wait()
        if hasattr(cls, 'db'):
            cls.db.rollback()
            cls.db.close()
            del cls.db
        if hasattr(cls, 'client'):
            del cls.client
        # wait up to 10 seconds for the file to be removable
        for x in range(100):
            try:
                if os.path.isfile(cls.dbfile):
                    os.remove(cls.dbfile)
                break
            except OSError:
                time.sleep(0.1)
        else:
            raise RuntimeError('Could not remove log db', cls.dbfile)

"""
Support for rolls, quit and join events (i.e. Roll Call).
"""

import datetime

import pmxbot
from pmxbot.core import on_join, on_leave

from . import logging, storage


class ParticipantLogger(storage.SelectableStorage):
    "Base class for logging participants"

    @classmethod
    def initialize(cls):
        cls.store = cls.from_URI()
        cls._finalizers.append(cls.finalize)

    @classmethod
    def finalize(cls):
        cls.store.close()
        del cls.store

    def list_channels(self):
        return self._list_channels()

    def log_join(self, nick, channel):
        self.log(nick, channel, 'join')

    def log_quit(self, nick, channel):
        self.log(nick, channel, 'quit')


@on_join()
def log_join(nick, channel):
    if channel not in pmxbot.config.log_channels:
        return
    ParticipantLogger.store.log_join(nick, channel)


@on_leave()
def log_leave(event, nick, channel):
    """
    Log a quit or part event.
    """
    if channel not in pmxbot.config.log_channels:
        return
    ParticipantLogger.store.log(nick, channel, event.type)


class SQLiteLogger(ParticipantLogger, storage.SQLiteStorage):
    def init_tables(self):
        LOG_CREATE_SQL = '''
        CREATE TABLE IF NOT EXISTS rolls (
            id INTEGER NOT NULL,
            datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            channel VARCHAR NOT NULL,
            nick VARCHAR NOT NULL,
            change TEXT,
            PRIMARY KEY (id) )
        '''
        INDEX_DTC_CREATE_SQL = """
            CREATE INDEX IF NOT EXISTS ix_rolls_datetime_channel
            ON rolls (datetime, channel)
            """
        INDEX_DT_CREATE_SQL = """
            CREATE INDEX IF NOT EXISTS ix_rolls_datetime
            ON rolls (datetime desc)
            """
        self.db.execute(LOG_CREATE_SQL)
        self.db.execute(INDEX_DTC_CREATE_SQL)
        self.db.execute(INDEX_DT_CREATE_SQL)
        self.db.commit()

    def log(self, nick, channel, change):
        INSERT_LOG_SQL = """
            INSERT INTO rolls
            (datetime, channel, nick, change)
            VALUES (?, ?, ?, ?)
            """
        # store naive UTC, as before
        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        self.db.execute(INSERT_LOG_SQL, [now, channel, nick, change])
        self.db.commit()


class MongoDBLogger(ParticipantLogger, storage.MongoDBStorage):
    collection_name = 'rolls'

    def log(self, nick, channel, change):
        self.db.ensure_index([
            ('datetime.d', storage.pymongo.DESCENDING),
            ('channel', storage.pymongo.ASCENDING),
        ])
        now = datetime.datetime.now(datetime.timezone.utc)
        doc = dict(
            channel=channel,
            nick=nick,
            change=change,
            datetime=logging.MongoDBLogger._fmt_date(now),
        )
        self.db.insert(doc)

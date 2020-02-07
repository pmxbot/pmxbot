import re
import random
import datetime
import itertools
import struct
import traceback
import urllib.parse
import socket
import operator
import logging

import pytz
from jaraco.context import ExceptionTrap
from more_itertools import chunked

import pmxbot
from . import storage
from . import core
from pmxbot.core import command, NoLog


first = operator.itemgetter(0)


_log = logging.getLogger(__name__)


class Logger(storage.SelectableStorage):
    "Base Logger class"

    @classmethod
    def initialize(cls):
        cls.store = cls.from_URI()
        tmpl = "Logging with {cls.store.__class__.__name__}"
        _log.info(tmpl.format_map(locals()))
        cls._finalizers.append(cls.finalize)

    @classmethod
    def finalize(cls):
        del cls.store

    def message(self, channel, nick, msg):
        channel = channel.replace('#', '').lower()
        self._message(channel, nick, msg)

    def list_channels(self):
        return self._list_channels()

    def clear(self):
        """
        Remove all messages from the database.
        """


class SQLiteLogger(Logger, storage.SQLiteStorage):
    def init_tables(self):
        LOG_CREATE_SQL = '''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER NOT NULL,
            datetime DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            channel VARCHAR NOT NULL,
            nick VARCHAR NOT NULL,
            message TEXT,
            PRIMARY KEY (id) )
        '''
        INDEX_DTC_CREATE_SQL = """
            CREATE INDEX
            IF NOT EXISTS ix_logs_datetime_channel
            ON logs (datetime, channel)
            """
        INDEX_DT_CREATE_SQL = """
            CREATE INDEX IF NOT EXISTS ix_logs_datetime
            ON logs (datetime desc)
            """
        self.db.execute(LOG_CREATE_SQL)
        self.db.execute(INDEX_DTC_CREATE_SQL)
        self.db.execute(INDEX_DT_CREATE_SQL)
        self.db.commit()

    def _message(self, channel, nick, msg):
        INSERT_LOG_SQL = """
            INSERT INTO logs
            (datetime, channel, nick, message)
            VALUES (?, ?, ?, ?)
            """
        now = datetime.datetime.now()
        self.db.execute(INSERT_LOG_SQL, [now, channel, nick, msg])
        self.db.commit()

    def last_seen(self, nick):
        FIND_LAST_SQL = """
            SELECT datetime, channel
            FROM logs
            WHERE nick = ?
            ORDER BY datetime DESC LIMIT 1
            """
        res = list(self.db.execute(FIND_LAST_SQL, [nick]))
        self.db.commit()
        if not res:
            return None
        else:
            return res[0]

    def strike(self, channel, nick, count):
        count += 1  # let's get rid of 'the last !strike' too!
        if count > 20:
            count = 20
        LAST_N_IDS_SQL = """
            select channel, nick, id
            from logs
            where channel = ? and nick = ?
            and date(datetime) = date('now','localtime')
            order by datetime desc limit ?
            """
        DELETE_LINE_SQL = """
            delete from logs
            where channel = ? and nick = ? and id = ?
            """
        channel = channel.replace('#', '')

        cur = self.db.execute(LAST_N_IDS_SQL, [channel.lower(), nick, count])
        ids_to_delete = cur.fetchall()
        if ids_to_delete:
            deleted = self.db.executemany(DELETE_LINE_SQL, ids_to_delete)
            self.db.commit()
            rows_deleted = deleted.rowcount - 1
        else:
            rows_deleted = 0
        rows_deleted = deleted.rowcount - 1
        self.db.commit()
        return rows_deleted

    def get_random_logs(self, limit):
        query = "SELECT message FROM logs order by random() limit %(limit)s" % vars()
        return map(first, self.db.execute(query))

    def get_channel_days(self, channel):
        query = 'select distinct date(datetime) from logs where channel = ?'
        return [x[0] for x in self.db.execute(query, [channel])]

    def get_day_logs(self, channel, day):
        query = """
            SELECT time(datetime), nick, message from logs
            where channel = ? and date(datetime) = ? order by datetime
            """
        return self.db.execute(query, [channel, day])

    def search(self, *terms):
        SEARCH_SQL = (
            'SELECT id, date(datetime), time(datetime), datetime, '
            'channel, nick, message FROM logs WHERE %s'
            % (' AND '.join(["message like '%%%s%%'" % x for x in terms]))
        )

        matches = []
        alllines = []
        search_res = self.db.execute(SEARCH_SQL).fetchall()
        for id, date, time, dt, channel, nick, message in search_res:
            line = (time, nick, message)
            if line in alllines:
                continue
            prev_q = """
                SELECT time(datetime), nick, message
                from logs
                where channel = ?
                    and datetime < ?
                order by datetime desc
                limit 2
                """
            prev2 = self.db.execute(prev_q, [channel, dt])
            next_q = prev_q.replace('<', '>').replace('desc', 'asc')
            next2 = self.db.execute(next_q, [channel, dt])
            lines = prev2.fetchall() + [line] + next2.fetchall()
            marker = self.make_anchor(line[:2])
            matches.append((channel, date, marker, lines))
            alllines.extend(lines)
        return matches

    def _list_channels(self):
        query = "SELECT distinct channel from logs"
        return (chan[0] for chan in self.db.execute(query).fetchall())

    def last_message(self, channel):
        query = """
            SELECT datetime, nick, message
            from logs
            where channel = ?
            order by datetime desc
            limit 1
        """
        time, nick, message = self.db.execute(query, [channel]).fetchone()
        result = dict(datetime=time, nick=nick, message=message)
        parse_date(result)
        return result

    def export_all(self):
        query = 'SELECT id, datetime, nick, message, channel from logs'

        def robust_text(text):
            for encoding in 'utf-8', 'latin-1':
                try:
                    return text.decode(encoding)
                except UnicodeDecodeError:
                    pass
            raise

        self.db.text_factory = robust_text
        cursor = self.db.execute(query)
        fields = 'id', 'datetime', 'nick', 'message', 'channel'
        results = (dict(zip(fields, record)) for record in cursor)
        return itertools.imap(parse_date, results)

    def clear(self):
        query = 'DELETE from logs'
        self.db.execute(query)


def parse_date(record):
    "Parse a date from sqlite. Assumes the date is in US/Pacific time zone."
    dt = record.pop('datetime')
    fmts = ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']
    for fmt in fmts:
        try:
            dt = datetime.datetime.strptime(dt, fmt)
            break
        except ValueError:
            pass
    else:
        raise
    tz = pytz.timezone('US/Pacific')
    loc_dt = tz.localize(dt)
    record['datetime'] = loc_dt
    return record


class MongoDBLogger(Logger, storage.MongoDBStorage):
    collection_name = 'logs'

    def _message(self, channel, nick, msg):
        self.db.create_index('datetime.d')
        self.db.create_index('channel')
        now = datetime.datetime.utcnow()
        doc = dict(
            channel=channel, nick=nick, message=msg, datetime=self._fmt_date(now)
        )
        res = self.db.insert_one(doc)
        self._add_recent(doc, res.inserted_id)

    def _add_recent(self, doc, logged_id):
        "Keep a tab on the most recent message for each channel"
        spec = dict(channel=doc['channel'])
        doc['ref'] = logged_id
        doc.pop('_id')
        self._recent.replace_one(spec, doc, upsert=True)

    @property
    def _recent(self):
        "roundabout way to get the 'recent' collection"
        return self.db.database.recent

    @staticmethod
    def _fmt_date(datetime):
        return dict(d=str(datetime.date()), t=str(datetime.time()))

    def last_seen(self, nick):
        fields = ('channel',)
        query = dict(nick=nick)
        cursor = self.db.find(query, projection=fields)
        cursor = cursor.sort('_id', storage.pymongo.DESCENDING)
        res = next(cursor, None)
        return res and [res['_id'].generation_time, res['channel']]

    def strike(self, channel, nick, count):
        channel = channel.replace('#', '')
        # cap at 19 messages
        count = min(count, 19)
        # get rid of 'the last !strike' too!
        limit = count + 1
        # don't delete anything beyond the past 18 hours
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=18)
        date_limit = storage.bson.objectid.ObjectId.from_datetime(cutoff)
        query = dict(channel=channel, nick=nick, _id={'$gt': date_limit})
        cursor = self.db.find(query).sort('_id', storage.pymongo.DESCENDING)
        cursor = cursor.limit(limit)
        ids_to_delete = [row['_id'] for row in cursor]
        if ids_to_delete:
            self.db.remove({'_id': {'$in': ids_to_delete}})
        rows_deleted = max(len(ids_to_delete) - 1, 0)
        return rows_deleted

    def get_random_logs(self, limit):
        count = min(limit, self.db.count_documents({}))
        ids = self.db.find({}, {'_id': 1})
        rand_ids = [r['_id'] for r in random.sample(list(ids), count)]
        for rand_ids_chunk in chunked(rand_ids, 100):
            query = {'_id': {'$in': rand_ids_chunk}}
            for doc in self.db.find(query, {'message': 1}):
                yield doc['message']

    def get_channel_days(self, channel):
        query = dict(channel=channel)
        return self.db.find(query, projection=['datetime.d']).distinct('datetime.d')

    def get_day_logs(self, channel, day):
        query = {'channel': channel, 'datetime.d': day}
        cur = self.db.find(query).sort('_id')
        return (
            (rec['_id'].generation_time.time(), rec['nick'], rec['message'])
            for rec in cur
        )

    def search(self, *terms):
        patterns = [re.compile('.*' + term + '.*') for term in terms]
        query = dict(message={'$all': patterns})

        return self._generate_search_results(self.db.find(query))

    def _generate_search_results(self, matched_entries):
        matches = []
        alllines = []
        for match in matched_entries:
            channel = match['channel']

            def row_date(row):
                return row['_id'].generation_time.date()

            def to_line(row):
                return (row['_id'].generation_time.time(), row['nick'], row['message'])

            line = to_line(match)
            if line in alllines:
                # we've seen this line in the context of a previous hit
                continue
            # get the context for this line
            prev2 = (
                self.db.find(dict(channel=match['channel'], _id={'$lt': match['_id']}))
                .sort('_id', storage.pymongo.DESCENDING)
                .limit(2)
            )
            prev2 = map(to_line, prev2)
            next2 = (
                self.db.find(dict(channel=match['channel'], _id={'$gt': match['_id']}))
                .sort('_id', storage.pymongo.ASCENDING)
                .limit(2)
            )
            next2 = map(to_line, next2)
            context = list(itertools.chain(prev2, [line], next2))
            marker = self.make_anchor(line[:2])
            matches.append((channel, row_date(match), marker, context))
            alllines.extend(context)
        return matches

    def list_channels(self):
        return [doc['channel'] for doc in self._recent.find()]

    def last_message(self, channel):
        rec = self._recent.find_one(dict(channel=channel))
        return dict(
            datetime=rec['ref'].generation_time,
            nick=rec['nick'],
            message=rec['message'],
        )

    def all_messages(self):
        return self.db.find()

    @staticmethod
    def extract_legacy_id(oid):
        """
        Given a special OID which includes the legacy sqlite ID, extract
        the sqlite ID.
        """
        return struct.unpack('L', oid.binary[-4:])[0]

    def import_(self, message):
        # construct a unique objectid with the correct datetime.
        dt = message['datetime']
        oid_time = storage.bson.objectid.ObjectId.from_datetime(dt)
        # store the original sqlite object ID in the
        orig_id = message.pop('id')
        orig_id_packed = struct.pack('>Q', orig_id)
        oid_new = oid_time.binary[:4] + orig_id_packed
        oid = storage.bson.objectid.ObjectId(oid_new)
        if not hasattr(Logger, 'log_id_map'):
            Logger.log_id_map = dict()
        Logger.log_id_map[orig_id] = oid
        message['_id'] = oid
        message['datetime'] = self._fmt_date(dt)
        self.db.insert(message)

    def clear(self):
        self.db.delete_many({})


class FullTextMongoDBLogger(MongoDBLogger):
    @classmethod
    def uri_matches(cls, uri):
        """
        override 'uri_matches' to disallow this logger if full text searching
        is not available.
        """
        return super().uri_matches(uri) and cls._has_fulltext(uri)

    @classmethod
    def _has_fulltext(cls, uri):
        """
        Enable full text search on the messages if possible and return True.
        If the full text search cannot be enabled, then return False.
        """
        coll = cls._get_collection(uri)
        with ExceptionTrap(storage.pymongo.errors.OperationFailure) as trap:
            coll.create_index([('message', 'text')], background=True)
        return not trap

    def search(self, *terms):
        query = ' '.join(terms)
        filter = {'$text': {'$search': query}}
        score = dict(score={'$meta': 'textScore'})
        cur = self.db.find(filter, projection=score)
        resp = cur.sort('score', score['score']).limit(200)
        return self._generate_search_results(resp)


class LegacyFullTextMongoDBLogger(FullTextMongoDBLogger):
    @classmethod
    def uri_matches(cls, uri):
        """
        override 'uri_matches' to prefer this logger when the server
        version doesn't support $text (MongoDB 2.4 only).
        """
        return super().uri_matches(uri) and cls._is_mongodb_24(uri)

    @classmethod
    def _is_mongodb_24(cls, uri):
        client = cls._get_collection(uri).database.client
        return client.server_info()['version'].startswith('2.4.')

    def search(self, *terms):
        query = ' '.join(terms)
        db = self.db.database
        collection_name = self.db.name
        resp = db.command('text', collection_name, search=query)
        docs = (res['obj'] for res in resp['results'])
        return self._generate_search_results(docs)


@command()
def strike(channel, nick, rest):
    "Strike last <n> statements from the record"
    yield NoLog
    rest = rest.strip()
    if not rest:
        count = 1
    else:
        if not rest.isdigit():
            yield "Strike how many?  Argument must be a positive integer."
            raise StopIteration
        count = int(rest)
    try:
        struck = Logger.store.strike(channel, nick, count)
        tmpl = (
            "Isn't undo great?  Last %d statement%s "
            "by %s were stricken from the record."
        )
        yield tmpl % (struck, 's' if struck > 1 else '', nick)
    except Exception:
        traceback.print_exc()
        yield "Hmm.. I didn't find anything of yours to strike!"


@command(aliases=('last', 'seen', 'lastseen'))
def where(channel, nick, rest):
    "When did pmxbot last see <nick> speak?"
    onick = rest.strip()
    last = Logger.store.last_seen(onick)
    if last:
        tm, chan = last
        tmpl = "I last saw {onick} speak at {tm} in channel #{chan}"
        return tmpl.format(tm=tm, chan=chan, onick=onick)
    else:
        return "Sorry!  I don't have any record of %s speaking" % onick


class LoggedChannels:
    def __contains__(self, channel):
        return channel in pmxbot.config.log_channels


class UnloggedChannels:
    def __contains__(self, channel):
        return channel not in pmxbot.config.log_channels


# Create a content handler for capturing logged channels
logging_handler = core.ContentHandler(channels=LoggedChannels())


@logging_handler.decorate
def log_message(channel, nick, rest):
    Logger.store.message(channel, nick, rest)


@command()
def logs(channel):
    "Where can one find the logs?"
    default_url = 'http://' + socket.getfqdn()
    base = pmxbot.config.get('logs URL', default_url)
    logged_channel = channel in pmxbot.config.log_channels
    path = '/channel/' + channel.lstrip('#') if logged_channel else '/'
    return urllib.parse.urljoin(base, path)


@command()
def log(channel, rest):
    """
    Enable or disable logging for a channel;
    use 'please' to start logging and 'stop please' to stop.
    """
    words = [s.lower() for s in rest.split()]
    if 'please' not in words:
        return
    include = 'stop' not in rest
    existing = set(pmxbot.config.log_channels)
    # add the channel if include, otherwise remove the channel
    op = existing.union if include else existing.difference
    pmxbot.config.log_channels = list(op([channel]))

import random
import operator

from . import storage
from .core import command


class Quotes(storage.SelectableStorage):
    lib = 'pmx'

    @classmethod
    def initialize(cls):
        cls.store = cls.from_URI()
        cls._finalizers.append(cls.finalize)

    @classmethod
    def finalize(cls):
        del cls.store

    @staticmethod
    def split_num(lookup):
        prefix, sep, num = lookup.rpartition(' ')
        if not prefix or not num.isdigit():
            return lookup, 0
        return prefix, int(num)

    def lookup(self, rest=''):
        rest = rest.strip()
        return self.lookup_with_num(*self.split_num(rest))


class SQLiteQuotes(Quotes, storage.SQLiteStorage):
    def init_tables(self):
        CREATE_QUOTES_TABLE = '''
            CREATE TABLE
            IF NOT EXISTS quotes (
                quoteid INTEGER NOT NULL,
                library VARCHAR NOT NULL,
                quote TEXT NOT NULL,
                PRIMARY KEY (quoteid)
            )
            '''
        CREATE_QUOTES_INDEX = '''
            CREATE INDEX
            IF NOT EXISTS ix_quotes_library
            on quotes(library)
            '''
        CREATE_QUOTE_LOG_TABLE = '''
            CREATE TABLE IF NOT EXISTS quote_log (quoteid varchar, logid INTEGER)
            '''
        self.db.execute(CREATE_QUOTES_TABLE)
        self.db.execute(CREATE_QUOTES_INDEX)
        self.db.execute(CREATE_QUOTE_LOG_TABLE)
        self.db.commit()

    def lookup_with_num(self, thing='', num=0):
        lib = self.lib
        BASE_SEARCH_SQL = """
            SELECT quoteid, quote
            FROM quotes
            WHERE library = ? %s order by quoteid
            """
        thing = thing.strip().lower()
        num = int(num)
        if thing:
            wtf = ' AND %s' % (
                ' AND '.join(["quote like '%%%s%%'" % x for x in thing.split()])
            )
            SEARCH_SQL = BASE_SEARCH_SQL % wtf
        else:
            SEARCH_SQL = BASE_SEARCH_SQL % ''
        results = [x[1] for x in self.db.execute(SEARCH_SQL, (lib,)).fetchall()]
        n = len(results)
        if n > 0:
            if num:
                i = num - 1
            else:
                i = random.randrange(n)
            quote = results[i]
        else:
            i = 0
            quote = ''
        return (quote, i + 1, n)

    def add(self, quote):
        lib = self.lib
        quote = quote.strip()
        if not quote:
            # Do not add empty quotes
            return
        ADD_QUOTE_SQL = 'INSERT INTO quotes (library, quote) VALUES (?, ?)'
        res = self.db.execute(ADD_QUOTE_SQL, (lib, quote))
        quoteid = res.lastrowid
        query = 'SELECT id, message FROM LOGS order by datetime desc limit 1'
        log_id, log_message = self.db.execute(query).fetchone()
        if quote in log_message:
            query = 'INSERT INTO quote_log (quoteid, logid) VALUES (?, ?)'
            self.db.execute(query, (quoteid, log_id))
        self.db.commit()

    def __iter__(self):
        # Note: also filter on quote not null, for backward compatibility
        query = "SELECT quote FROM quotes WHERE library = ? and quote is not null"
        for row in self.db.execute(query, [self.lib]):
            yield {'text': row[0]}

    def export_all(self):
        query = """
            SELECT quote, library, logid
            from quotes
            left outer join quote_log on quotes.quoteid = quote_log.quoteid
            """
        fields = 'text', 'library', 'log_id'
        return (dict(zip(fields, res)) for res in self.db.execute(query))


class MongoDBQuotes(Quotes, storage.MongoDBStorage):
    collection_name = 'quotes'

    def find_matches(self, thing):
        thing = thing.strip().lower()
        words = thing.split()

        def matches(quote):
            quote = quote.lower()
            return all(word in quote for word in words)

        return [
            row
            for row in self.db.find(dict(library=self.lib)).sort('_id')
            if matches(row['text'])
        ]

    def lookup_with_num(self, thing='', num=0):
        by_text = operator.itemgetter('text')
        results = list(map(by_text, self.find_matches(thing)))

        n = len(results)
        if n > 0:
            if num:
                i = num - 1
            else:
                i = random.randrange(n)
            quote = results[i]
        else:
            i = 0
            quote = ''
        return (quote, i + 1, n)

    def delete(self, lookup):
        """
        If exactly one quote matches, delete it. Otherwise,
        raise a ValueError.
        """
        lookup, num = self.split_num(lookup)
        if num:
            result = self.find_matches(lookup)[num - 1]
        else:
            (result,) = self.find_matches(lookup)
        self.db.delete_one(result)

    def add(self, quote):
        quote = quote.strip()
        quote_id = self.db.insert_one(dict(library=self.lib, text=quote))
        # see if the quote added is in the last IRC message logged
        newest_first = [('_id', storage.pymongo.DESCENDING)]
        last_message = self.db.database.logs.find_one(sort=newest_first)
        if last_message and quote in last_message['message']:
            self.db.update_one(
                {'_id': quote_id}, {'$set': dict(log_id=last_message['_id'])}
            )

    def __iter__(self):
        return self.db.find(dict(library=self.lib))

    def _build_log_id_map(self):
        from . import logging

        if not hasattr(logging.Logger, 'log_id_map'):
            log_db = self.db.database.logs
            logging.Logger.log_id_map = dict(
                (logging.MongoDBLogger.extract_legacy_id(rec['_id']), rec['_id'])
                for rec in log_db.find(projection=[])
            )
        return logging.Logger.log_id_map

    def import_(self, quote):
        log_id_map = self._build_log_id_map()
        log_id = quote.pop('log_id', None)
        log_id = log_id_map.get(log_id, log_id)
        if log_id is not None:
            quote['log_id'] = log_id
        self.db.insert_one(quote)


@command(aliases='q')
def quote(rest):
    """
    If passed with nothing then get a random quote. If passed with some
    string then search for that. If prepended with "add:" then add it to the
    db, eg "!quote add: drivers: I only work here because of pmxbot!".
    Delete an individual quote by prepending "del:" and passing a search
    matching exactly one query.
    """
    rest = rest.strip()
    if rest.startswith('add: ') or rest.startswith('add '):
        quote_to_add = rest.split(' ', 1)[1]
        Quotes.store.add(quote_to_add)
        qt = False
        return 'Quote added!'
    if rest.startswith('del: ') or rest.startswith('del '):
        cmd, sep, lookup = rest.partition(' ')
        Quotes.store.delete(lookup)
        return 'Deleted the sole quote that matched'
    qt, i, n = Quotes.store.lookup(rest)
    if not qt:
        return
    return '(%s/%s): %s' % (i, n, qt)

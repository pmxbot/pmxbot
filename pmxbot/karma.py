import itertools
import re
import random

from . import storage
from .core import command


class SameName(ValueError):
    pass


class AlreadyLinked(ValueError):
    pass


class Karma(storage.SelectableStorage):
    @classmethod
    def initialize(cls):
        cls.store = cls.from_URI()
        cls._finalizers.append(cls.finalize)

    @classmethod
    def finalize(cls):
        del cls.store

    def link(self, thing1, thing2):
        """
        Link thing1 and thing2, adding the karma of each into
        a single entry.
        If any thing does not exist, it is created.
        """
        thing1 = thing1.strip().lower()
        thing2 = thing2.strip().lower()
        if thing1 == thing2:
            raise SameName("Attempted to link two of the same name")
        self.change(thing1, 0)
        self.change(thing2, 0)
        return self._link(thing1, thing2)


class SQLiteKarma(Karma, storage.SQLiteStorage):
    def init_tables(self):
        CREATE_KARMA_VALUES_TABLE = '''
            CREATE TABLE IF NOT EXISTS karma_values (
                karmaid INTEGER NOT NULL,
                karmavalue INTEGER,
                primary key (karmaid)
            )
        '''
        CREATE_KARMA_KEYS_TABLE = '''
            CREATE TABLE IF NOT EXISTS karma_keys (
                karmakey varchar,
                karmaid INTEGER,
                primary key (karmakey)
            )
        '''
        CREATE_KARMA_LOG_TABLE = '''
            CREATE TABLE IF NOT EXISTS karma_log (
                karmakey varchar,
                logid INTEGER,
                change INTEGER
            )
        '''
        self.db.execute(CREATE_KARMA_VALUES_TABLE)
        self.db.execute(CREATE_KARMA_KEYS_TABLE)
        self.db.execute(CREATE_KARMA_LOG_TABLE)
        self.db.commit()

    def lookup(self, thing):
        thing = thing.strip().lower()
        LOOKUP_SQL = """
            SELECT karmavalue
            from karma_keys k
            join karma_values v on k.karmaid = v.karmaid where k.karmakey = ?
            """
        try:
            karma = self.db.execute(LOOKUP_SQL, [thing]).fetchone()[0]
        except Exception:
            karma = 0
        if karma is None:
            karma = 0
        return karma

    def set(self, thing, value):
        thing = thing.strip().lower()
        value = int(value)
        UPDATE_SQL = """
            UPDATE karma_values SET karmavalue = ?
            where karmaid = (
                select karmaid from karma_keys where karmakey = ?
            )
            """
        res = self.db.execute(UPDATE_SQL, (value, thing))
        if res.rowcount == 0:
            INSERT_VALUE_SQL = 'INSERT INTO karma_values (karmavalue) VALUES (?)'
            INSERT_KEY_SQL = 'INSERT INTO karma_keys (karmakey, karmaid) VALUES (?, ?)'
            ins = self.db.execute(INSERT_VALUE_SQL, [value])
            self.db.execute(INSERT_KEY_SQL, (thing, ins.lastrowid))
        self.db.commit()

    def change(self, thing, change):
        thing = thing.strip().lower()
        value = int(self.lookup(thing)) + int(change)
        UPDATE_SQL = """
            UPDATE karma_values SET karmavalue = ?
            where karmaid = (
                select karmaid from karma_keys where karmakey = ?
            )
            """
        res = self.db.execute(UPDATE_SQL, (value, thing))
        if res.rowcount == 0:
            INSERT_VALUE_SQL = 'INSERT INTO karma_values (karmavalue) VALUES (?)'
            INSERT_KEY_SQL = 'INSERT INTO karma_keys (karmakey, karmaid) VALUES (?, ?)'
            ins = self.db.execute(INSERT_VALUE_SQL, [value])
            self.db.execute(INSERT_KEY_SQL, (thing, ins.lastrowid))
        self.db.commit()

    def list(self, select=0):
        KARMIC_VALUES_SQL = """
            SELECT karmaid, karmavalue
            from karma_values order by karmavalue desc
            """
        KARMA_KEYS_SQL = """
            SELECT karmakey from karma_keys where karmaid = ?
            """

        karmalist = self.db.execute(KARMIC_VALUES_SQL).fetchall()
        karmalist.sort(key=lambda x: int(x[1]), reverse=True)
        if select > 0:
            selected = karmalist[:select]
        elif select < 0:
            selected = karmalist[select:]
        else:
            selected = karmalist
        keysandkarma = []
        for karmaid, value in selected:
            keys = [x[0] for x in self.db.execute(KARMA_KEYS_SQL, [karmaid])]
            keysandkarma.append((keys, value))
        return keysandkarma

    def _link(self, thing1, thing2):
        GET_KARMAID_SQL = 'SELECT karmaid FROM karma_keys WHERE karmakey = ?'
        t1id = self.db.execute(GET_KARMAID_SQL, [thing1]).fetchone()[0]
        t1value = self.lookup(thing1)
        t2id = self.db.execute(GET_KARMAID_SQL, [thing2]).fetchone()[0]
        if t1id == t2id:
            raise AlreadyLinked("Those two are already linked")
        t2value = self.lookup(thing2)

        newvalue = t1value + t2value
        # update the keys so t2 points to t1s value
        query = 'UPDATE karma_keys SET karmaid = ? where karmaid = ?'
        self.db.execute(query, (t1id, t2id))
        # drop the old value row for neatness
        self.db.execute('DELETE FROM karma_values WHERE karmaid = ?', (t2id,))
        # set the new combined value
        query = 'UPDATE karma_values SET karmavalue = ? where karmaid = ?'
        self.db.execute(query, (newvalue, t1id))
        self.db.commit()

    def _get(self, id):
        "Return keys and value for karma id"
        VALUE_SQL = "SELECT karmavalue from karma_values where karmaid = ?"
        KEYS_SQL = "SELECT karmakey from karma_keys where karmaid = ?"
        value = self.db.execute(VALUE_SQL, [id]).fetchall()[0][0]
        keys_cur = self.db.execute(KEYS_SQL, [id]).fetchall()
        keys = sorted(x[0] for x in keys_cur)
        return keys, value

    def search(self, term):
        query = "SELECT distinct karmaid from karma_keys where karmakey like ?"
        matches = (id for (id,) in self.db.execute(query, '%%' + term + '%%'))
        return (self._lookup(id) for id in matches)

    def export_all(self):
        return self.list()


class MongoDBKarma(Karma, storage.MongoDBStorage):
    collection_name = 'karma'

    def lookup(self, thing):
        thing = thing.strip().lower()
        res = self.db.find_one({'names': thing})
        return res['value'] if res else 0

    def set(self, thing, value):
        thing = thing.strip().lower()
        value = int(value)
        query = {'names': {'$elemMatch': {'$in': [thing]}}}
        oper = {'$set': {'value': value}, '$addToSet': {'names': thing}}
        self.db.update_one(query, oper, upsert=True)

    def change(self, thing, change):
        thing = thing.strip().lower()
        change = int(change)
        query = {'names': {'$elemMatch': {'$in': [thing]}}}
        oper = {'$inc': {'value': change}, '$addToSet': {'names': thing}}
        self.db.update_one(query, oper, upsert=True)

    def list(self, select=0):
        res = list(self.db.find().sort('value', storage.pymongo.DESCENDING))

        if select > 0:
            selected = res[:select]
        elif select < 0:
            selected = res[select:]
        else:
            selected = res

        def as_list(val):
            return val if isinstance(val, list) else [val]

        return [(as_list(rec['names']), rec['value']) for rec in selected]

    def _link(self, thing1, thing2):
        rec = self.db.find_one({'names': thing2})
        if thing1 in rec['names']:
            raise AlreadyLinked("Those two are already linked")
        query = {'names': thing1}
        update = {
            '$inc': {'value': rec['value']},
            '$push': {'names': {'$each': rec['names']}},
        }
        self.db.update_one(query, update)
        self.db.delete_one(rec)

    def search(self, term):
        pattern = re.compile('.*' + re.escape(term) + '.*')
        return (
            (rec['names'], rec['value']) for rec in self.db.find({'names': pattern})
        )

    def import_(self, item):
        names, value = item
        self.db.insert(dict(names=names, value=value))

    def _all_names(self):
        return set(
            itertools.chain.from_iterable(names for names, value in self.search(''))
        )

    def repair_duplicate_names(self):
        """
        Prior to 1101.1.1, pmxbot would incorrectly create new karma records
        for individuals with multiple names.
        This routine corrects those records.
        """
        for name in self._all_names():
            cur = self.db.find({'names': name})
            main_doc = next(cur)
            for duplicate in cur:
                query = {'_id': main_doc['_id']}
                update = {
                    '$inc': {'value': duplicate['value']},
                    '$push': {'names': {'$each': duplicate['names']}},
                }
                self.db.update(query, update)
                self.db.remove(duplicate)


def _twiddle_karma(karmee):
    change = random.choice(range(-1, 2))
    Karma.store.change(karmee, change)
    return {
        1: f"{karmee} karma++",
        0: f"{karmee} karma shall remain the same",
        -1: f"{karmee} karma--",
    }[change]


def _link_karma(actor, *nicks):
    try:
        Karma.store.link(*nicks)
    except SameName:
        Karma.store.change(actor, -1)
        return "Don't try to link a name to itself!"
    except AlreadyLinked:
        return "Those names were previously linked."
    score = Karma.store.lookup(nicks[0])
    return f"{' and '.join(nicks)} are now linked and have a score of {score}"


@command(aliases="k")
def karma(nick, rest):
    "Return or change the karma value for some(one|thing)"
    karmee = rest.strip('++').strip('--').strip('~~')
    if '++' in rest:
        Karma.store.change(karmee, 1)
    elif '--' in rest:
        Karma.store.change(karmee, -1)
    elif '~~' in rest:
        return _twiddle_karma(karmee)
    elif '==' in rest:
        return _link_karma(rest.split('=='))
    else:
        karmee = rest or nick
        score = Karma.store.lookup(karmee)
        return f"{karmee} has {score} karmas"


@command("top10", aliases=("top",))
def top10(rest):
    """
    Return the top n (default 10) highest entities by Karmic value.
    Use negative numbers for the bottom N.
    """
    if rest:
        topn = int(rest)
    else:
        topn = 10
    selection = Karma.store.list(topn)
    res = ' '.join('(%s: %s)' % (', '.join(n), k) for n, k in selection)
    return res


@command(aliases=("bottom",))
def bottom10(rest):
    """
    Return the bottom n (default 10) lowest entities by Karmic value.
    Use negative numbers for the bottom N.
    """
    if rest:
        topn = -int(rest)
    else:
        topn = -10
    selection = Karma.store.list(topn)
    res = ' '.join('(%s: %s)' % (', '.join(n), k) for n, k in selection)
    return res

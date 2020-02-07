import time

from . import storage
from .core import command, on_join


class Notify(storage.SelectableStorage):
    @classmethod
    def init(cls):
        cls.store = cls.from_URI()
        cls._finalizers.append(cls.finalize)

    @classmethod
    def finalize(cls):
        del cls.store


class SQLiteNotify(Notify, storage.SQLiteStorage):
    def init_tables(self):
        CREATE_NOTIFY_TABLE = '''
            CREATE TABLE
            IF NOT EXISTS notify
            (
                notifyid INTEGER NOT NULL,
                tonick VARCHAR NOT NULL,
                fromnick VARCHAR NOT NULL,
                message VARCHAR NOT NULL,
                notifytime TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                primary key(notifyid)
            )
        '''

        self.db.execute(CREATE_NOTIFY_TABLE)
        self.db.commit()

    def lookup(self, nick):
        query = """
            SELECT fromnick, message, notifytime, notifyid
            FROM notify WHERE tonick = ?
        """
        ''' Ugly, but will work with sqlite3 or pysqlite2 '''
        messages = [
            {'fromnick': x[0], 'message': x[1], 'notifytime': x[2], 'notifyid': x[3]}
            for x in self.db.execute(query, [nick])
        ]
        ids = [x['notifyid'] for x in messages]
        query = """
            DELETE FROM notify
            WHERE notifyid IN (%s)
            """ % ','.join(
            '?' for x in ids
        )
        self.db.execute(query, ids)

        return messages

    def notify(self, fromnick, tonick, message):
        query = "INSERT INTO notify (fromnick, tonick, message) values (?,?,?)"
        return self.db.execute(query, (fromnick, tonick, message))


class MongoDBNotify(Notify, storage.MongoDBStorage):
    collection_name = 'notify'

    def lookup(self, nick):
        nick = nick.strip().lower()
        messages = []
        res = self.db.find({'tonick': nick}).sort('notifications')
        for msg in res:
            messages.append(msg)
            self.db.remove(msg)

        return messages

    def notify(self, fromnick, tonick, message):
        fromnick = fromnick.strip().lower()
        tonick = tonick.strip().lower()
        notification = {
            'tonick': tonick,
            'fromnick': fromnick,
            'message': message,
            'notifytime': time.time(),
        }
        query = notification
        oper = {'$set': {'value': notification}, '$addToSet': notification}
        self.db.insert(query, oper)


@command("notify")
def donotify(nick, rest):
    "notify <nick> <message>"
    opts = rest.split(' ')
    to = opts[0]
    Notify.store.notify(nick, to, ' '.join(opts[1:]))
    return "Will do!"


@on_join()
def notifier(client, nick):
    for msg in Notify.store.lookup(nick):
        out = '%s wanted to say %s' % (msg['fromnick'], msg['message'])
        client.notice(nick, out)

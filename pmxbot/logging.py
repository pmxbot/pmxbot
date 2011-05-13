import re
import datetime

from . import storage

def init_logger(uri):
	class_ = MongoDBLogger if uri.startswith('mongodb://') else Logger
	return class_(uri)

class Logger(storage.SQLiteStorage):

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
		INDEX_DTC_CREATE_SQL = 'CREATE INDEX IF NOT EXISTS ix_logs_datetime_channel ON logs (datetime, channel)'
		INDEX_DT_CREATE_SQL = 'CREATE INDEX IF NOT EXISTS ix_logs_datetime ON logs (datetime desc)'
		self.db.execute(LOG_CREATE_SQL)
		self.db.execute(INDEX_DTC_CREATE_SQL)
		self.db.execute(INDEX_DT_CREATE_SQL)
		self.db.commit()
		
	def message(self, channel, nick, msg):
		INSERT_LOG_SQL = 'INSERT INTO logs (datetime, channel, nick, message) VALUES (?, ?, ?, ?)'
		now = datetime.datetime.now()
		channel = channel.replace('#', '')
		self.db.execute(INSERT_LOG_SQL, [now, channel.lower(), nick, msg])
		self.db.commit()

	def last_seen(self, nick):
		FIND_LAST_SQL = 'SELECT datetime, channel FROM logs WHERE nick = ? ORDER BY datetime DESC LIMIT 1'
		res = list(self.db.execute(FIND_LAST_SQL, [nick]))
		self.db.commit()
		if not res:
			return None
		else:
			return res[0]

	def strike(self, channel, nick, count):
		count += 1 # let's get rid of 'the last !strike' too!
		if count > 20:
			count = 20
		LAST_N_IDS_SQL = '''select channel, nick, id from logs where channel = ? and nick = ? and date(datetime) = date('now','localtime') order by datetime desc limit ?'''
		DELETE_LINE_SQL = '''delete from logs where channel = ? and nick = ? and id = ?'''
		channel = channel.replace('#', '')
		
		ids_to_delete = self.db.execute(LAST_N_IDS_SQL, [channel.lower(), nick, count]).fetchall()
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
		return self.db.execute(query)

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
			'channel, nick, message FROM logs WHERE %s' % (
				' AND '.join(["message like '%%%s%%'" % x for x in terms])
			)
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
			marker = self.make_anchor(line)
			matches.append((channel, date, marker, lines))
			alllines.extend(lines)
		return matches

	def list_channels(self):
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
		return dict(time=time, nick=nick, message=message)

	def all_messages(self):
		query = 'SELECT datetime, nick, message, channel from logs'
		cursor = self.db.execute(query).fetchall()
		fields = 'datetime', 'nick', 'message', 'channel'
		return (dict(zip(fields, record) for record in cursor))

class MongoDBLogger(storage.MongoDBStorage):
	collection_name = 'logs'

	def message(self, channel, nick, msg):
		channel = channel.replace('#', '')
		self.db.insert(dict(channel=channel, nick=nick, message=msg))

	def last_seen(self, nick):
		fields = 'channel',
		query = dict(nick=nick)
		cursor = self.db.find(query, fields=fields)
		cursor = cursor.sort('_id', pymongo.DESCENDING)
		res = first(cursor)
		if not res:
			return None
		return [res['_id'].generation_time, res['channel']]

	def strike(self, channel, nick, count):
		channel = channel.replace('#', '')
		# cap at 19 messages
		count = min(count, 19)
		# get rid of 'the last !strike' too!
		limit = count+1
		# don't delete anything before the current date
		date_limit = pymongo.ObjectId.from_datetime(datetime.date.today())
		query = dict(channel=channel, nick=nick)
		query['$gt'] = dict(_id=date_limit)
		cursor = self.db.find(query).sort('_id', pymongo.DESCENDING)
		cursor = cursor.limit(limit)
		ids_to_delete = [row['_id'] for row in cursor]
		if ids_to_delete:
			self.db.remove({'_id': {'$in': ids_to_delete}}, safe=True)
		rows_deleted = max(len(ids_to_delete) - 1, 0)
		return rows_deleted

	def get_random_logs(self, limit):
		cur = self.db.find()
		limit = max(limit, cur.count())
		return (item['message'] for item in random.sample(cur, limit))

	def get_channel_days(self, channel):
		cur = self.db.find(fields=['_id'])
		timestamps = (row['_id'].generation_time.date() for row in cur)
		return unique_justseen(timestamps)

	def get_day_logs(self, channel, day):
		start = pymongo.ObjectID.from_datetime(day)
		one_day = datetime.timedelta(days=1)
		end = pymongo.ObjectID.from_datetime(day + one_day)
		query = dict(_id = {'$gte': start, '$lt': end}, channel=channel)
		cur = self.db.find(query).sort('_id')
		return (
			(rec['_id'].generation_time.time(), rec['nick'], rec['message'])
			for rec in cur
		)

	def search(self, *terms):
		patterns = [re.compile('.*' + term + '.*') for term in terms]
		query = dict(message = {'$all': patterns})

		matches = []
		alllines = []
		for match in self.db.find(query):
			channel = match['channel']
			row_date = lambda row: row['_id'].generation_time.date()
			to_line = lambda row: (row['_id'].generation_time.time(),
				row['nick'], row['message'])
			line = to_line(match)
			if line in alllines:
				# we've seen this line in the context of a previous hit
				continue
			# get the context for this line
			prev2 = self.db.find(dict(
				channel=match['channel'],
				_id={'$lt': match['_id']}
				)).sort('_id', pymongo.DESCENDING).limit(2)
			prev2 = map(to_line, prev2)
			next2 = self.db.find(dict(
				channel=match['channel'],
				_id={'$gt': match['_id']}
				)).sort('_id', pymongo.ASCENDING).limit(2)
			next2 = map(to_line, prev2)
			context = prev2 + [line] + next2
			marker = self.make_anchor(line)
			matches.append((channel, date, marker, context))
			alllines.extend(context)
		return matches

	def list_channels(self):
		return self.db.distinct('channel')

	def last_message(self, channel):
		rec = next(
			self.db.find(
				dict(channel=channel)
			).sort('_id', pymongo.DESCENDING).limit(1)
		)
		return dict(
			time=rec['_id'].generation_time,
			nick=rec['nick'],
			message=rec['message']
		)

	def all_messages(self):
		cursor = self.db.find()
		def fix_time(rec):
			rec['datetime'] = rec.pop('_id').generation_time
			return rec
		return itertools.imap(fix_time, cursor)

	def import_message(self, message):
		# construct a unique objectid with the correct datetime.
		oid_time = pymongo.objectid.ObjectId.from_datetime(message.pop['datetime'])
		oid_rest = pymongo.objectid.ObjectId()
		oid_new = str(oid_time)[:8] + str(oid_rest)[8:]
		oid = pymongo.objectid.ObjectId(oid_new)
		message['_id'] = oid
		self.db.insert(message)


# from Python 3.1 documentation
def unique_justseen(iterable, key=None):
	"""
	List unique elements, preserving order. Remember only the element just seen.

	>>> ' '.join(unique_justseen('AAAABBBCCDAABBB'))
	'A B C D A B'
	
	>>> ' '.join(unique_justseen('ABBCcAD', str.lower))
	'A B C A D'
	"""
	return itertools.imap(
		next, itertools.imap(
			operator.itemgetter(1),
			itertools.groupby(iterable, key)
		))

def migrate_logs(source, dest):
	source_db = init_logger(source)
	dest_db = init_logger(dest)
	for msg in source_db.all_messages():
		dest_db.import_message(msg)

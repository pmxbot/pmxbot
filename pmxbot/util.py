# vim:ts=4:sw=4:noexpandtab
import os
import random
import re
import urllib
import itertools

import httplib2
import wordnik

from . import storage

ball8_opts = {
"Signs point to yes." : 21,
"Yes." : 21,
"Most likely." : 21,
"Without a doubt." : 21,
"Yes - definitely." : 21,
"As I see it, yes." : 21,
"You may rely on it." : 18,
"Outlook good." : 18,
"It is certain." : 18,
"It is decidedly so." : 18,
"Reply hazy, try again." : 1,
"Better not tell you now." : 1,
"Ask again later." : 1,
"Concentrate and ask again." : 1,
"Cannot predict now." : 1,
"Six of one, half-dozen of another." : 1,
"Hold on, let me check the latest polls." : 1,
"Would you like fries with that?" : 1,
"Will you go to lunch? Go to lunch. Will you go to lunch?" : 1,
"I grow weary of your questions." : 1,
"Get away from me, kid, you bother me." : 1,
"Go, and never darken my towels again." : 1,
"Your question fills a much-needed gap." : 1,
"I have heard your question and much like it." : 1,
"Only reading entrails can answer that." : 1,
"That is alas a mystery.  Unless you ask again." : 1,
"Your question makes my circuits hurt." : 1,
"You say 'tom ay to,' I say 'no way, Joe.'" : 1,
"Doubt it." : 10,
"No." : 10,
"Indeed." : 10,
"Yes, please." : 10,
"Inevitably." : 10,
"Probably." : 10,
"Unquestionably." : 10,
"Nay." : 1,
"When pigs fly." : 1,
"Whatever happened to crossing my palms with silver?" : 1,
"Ask the NSA." : 1,
"Not likely before the heat death of the universe." : 1,
"Not if wishes were horses.  Neigh." : 1,
"A little birdie told me no." : 1,
"Pipe down in the peanut gallery, willya?" : 1,
"My sources say no." : 18,
"Very doubtful." : 18,
"My reply is no." : 18,
"Outlook not so good." : 18,
"Don't count on it." : 18,
"Not a chance." : 18,
"Highly unlikely." : 18,
"NFW." : 25,
"You're more likely to get rich off you.l." : 18,
"Not a chance, buddy." : 18,
"p < .05" : 18,
"Sample size too small." : 18,
"Tentatively confirmed.": 18,
}

certainty_opts = [
"definitely",
"probably",
"maybe",
"possibly",
"perhaps",
"certainly",
"questionably",
"unquestionably",
"without doubt",
"absolutely",
]

weapon_opts = [
'shiv',
'shank',
'knife',
'spork',
'razor',
'cocktail sword',
'spatula',
'scimitar',
'pipe',
'bat',
'stickbat',
'wooden pallet',
]

weapon_adjs = [
'rusty',
'dirty',
'broken',
'gleaming',
'serrated',
'dull',
'sharp',
'bent',
'flaming',
]

violent_acts = [
'stabs',
'cuts',
'maims',
'sticks',
'shivs',
'shanks',
'disembowels',
'minces',
'perforates',
'lobotomizes',
'slashes',
'furiously pokes',
]

fight_victories = [
'defeats',
'destroys',
'dominates',
'edges',
'pwns',
'crushes',
'obliviates',
'trounces',
'sneaks by',
'hires a hitman to take care of',
]

fight_descriptions = [
'a barroom brawl',
'a cagematch',
'a fight in the octagon',
'a fight to the death',
'a fight to the pain',
'a slapfest',
'a thumbwrestling match',
'a battle with dull, flaming scimitars',
'a gentlemanly game of chess',
'a bat fight',
'a stickbat fight',
'with a crowbar to the kneee.'
]

dowski_praises = [
"and I defer to your distinguished discernment",
"and I honor your legacy",
"and I'm always astounded by your acumen",
"cursing those who would deny you deference",
"greeting your grand gloriousness with groveling",
"humbled by your unbelievable understanding",
"long live your long-leggedness",
"may all respect you and your recognized renowned remarkableness",
"may all of your successes be glorious",
"may your burdens be light upon your back",
"may the road rise up to meet you",
"may the wind be always at your back",
"may the sun shine warm upon your face",
"may all of your enemies be !shivved",
"oh great ruler of all things IS",
"oh wondrous wonderboy of the midwest",
"oh phenomenal prodigy of python programming",
"oh loquacious liege",
"oh happy harbinger of happiness",
"saluting your supreme superiority",
"with my obeisance to your ohioness",
"viva la dowski",
"(everyone knows you're the best)",
"you're much more splendorous than windowsill to me",
"chowski or dowski, your prowess is unparalleled",
"dowski manor may be in canton, but it must be heavenly",
]

holger_dawg = [
"WAZZUP DAWG?",
"wassup, my dawg brotha?",
"you be trippin', my homey dawg",
"you be comin' to liberate, holger the dane dawg?",
"you can put my dawg holger into da hood, but you'll never put da hood into my dawg holger",
]

yuckvl = ['grinds teeth', 'shudders', 'gags', 'blinks away tears', 'coughs', 'stares', 'drops to the ground curled in the fetal position', 'spits', 'wards off the evil eye', 'dies a little more inside', 'contemplates suicide', 'cackles maniacally and slowly goes mad', 'starts to reread Ecclesiastes', 'blames this fiasco on Carl Friedrich Gauss', 'ponders a career change', 'twitches', 'considers alcoholism', 'remains very, very still', 'hisses', 'groans']

clapvl = ['slowly', 'sadly', 'quietly', 'briefly', 'halfheartedly']

advl = ['clearly', 'likely', 'utterly', 'deeply', 'profoundly']

adjl = ['unimpressed', 'overwhelmed', 'verklemmt', 'distracted', 'awed']

fcverbs = ['aggregate', 'architect', 'benchmark', 'brand', 'cultivate', 'deliver', 'deploy', 'disintermediate', 'drive', 'e-enable', 'embrace', 'empower', 'enable', 'engage', 'engineer', 'enhance', 'envisioneer', 'evolve', 'expedite', 'exploit', 'extend', 'facilitate', 'generate', 'grow', 'harness', 'implement', 'incentivize', 'incubate', 'innovate', 'integrate', 'iterate', 'leverage', 'matrix', 'maximize', 'mesh', 'monetize', 'morph', 'optimize', 'orchestrate', 'productize', 'recontextualize', 'redefine', 'reintermediate', 'reinvent', 'repurpose', 'revolutionize', 'scale', 'seize', 'strategize', 'streamline', 'syndicate', 'synergize', 'synthesize', 'target', 'transform', 'transition', 'unleash', 'utilize', 'visualize', 'whiteboard']

fcadjectives = ['24/365', '24/7', 'B2B', 'B2C', 'back-end', 'best-of-breed', 'bleeding-edge', 'bricks-and-clicks', 'clicks-and-mortar', 'collaborative', 'compelling', 'cross-platform', 'cross-media', 'customized', 'cutting-edge', 'distributed', 'dot-com', 'dynamic', 'e-business', 'efficient', 'end-to-end', 'enterprise', 'extensible', 'frictionless', 'front-end', 'global', 'granular', 'holistic', 'impactful', 'innovative', 'integrated', 'interactive', 'intuitive', 'killer', 'leading-edge', 'magnetic', 'mission-critical', 'next-generation', 'one-to-one', 'open-source', 'out-of-the-box', 'plug-and-play', 'proactive', 'real-time', 'revolutionary', 'rich', 'robust', 'scalable', 'seamless', 'sexy', 'sticky', 'strategic', 'synergistic', 'transparent', 'turn-key', 'ubiquitous', 'user-centric', 'value-added', 'vertical', 'viral', 'virtual', 'visionary', 'web-enabled', 'wireless', 'world-class']

fcnouns = ['action-items', 'applications', 'architectures', 'bandwidth', 'channels', 'communities', 'content', 'convergence', 'deliverables', 'e-business', 'e-commerce', 'e-markets', 'e-services', 'e-tailers', 'experiences', 'eyeballs', 'functionalities', 'infomediaries', 'infrastructures', 'initiatives', 'interfaces', 'markets', 'methodologies', 'metrics', 'mindshare', 'models', 'networks', 'niches', 'paradigms', 'partnerships', 'platforms', 'portals', 'relationships', 'ROI', 'synergies', 'web-readiness', 'schemas', 'solutions', 'supply-chains', 'systems', 'technologies', 'users', 'portals', 'web services']

jobs1 = ["Assistant", "Internal", "External", "Foreign", "Domestic", "Deputy", "Junior", "Senior", "Regional", "Level B", "Level C", "Inter", "Intra", "YouGov", "Executive", "Special", "Polimetrix", "Primary", "Lead", "Backup", "Chief"]

jobs2 = ["Project", "Systems", "Marketing", "Purchasing", "Communications", "Sales", "Financial", "Accounting", "Personnel", "Engineering", "Information", "Customer Service", "Operations", "Development", "Surveys", "Panel", "Database", "Projects", "Analytics"]

jobs3 = ["Manager", "Specialist", "Coordinator", "Administrator", "Analyst", "Planner", "Processor", "Consultant", "Clerk", "Officer", "Monitor", "Associate", "Trainee", "I", "II", "III", "IV", "V", "VP", "EVP", "SVP", "Director", "Developer", "Trainer", "Contractor", "Consultant", "Executive"]

otrail_actions = ['has']*6 + ['has died from'] * 6 + ['lost the trail. Lose 3 days.', 'took the ferry across the river safely.', 'forded the river safely.', 'capsized while floating across the river.', 'drowned.', 'killed a bear.', 'killed a buffalo.', 'lost an ox.', 'made it to oregon. Time to party with schmichael.', 'finds wild fruit.', 'traded with Indians.', 'passes a gravesite.', 'had no trouble floating the wagon across.', 'is taking the rapids.', 'is attacked by ninjas. Lose 8 days.', 'is attacked by reavers and dies.']

otrail_issues = ['a fever', 'dysentery', 'measles', 'cholera', 'typhoid', 'exhaustion', 'a snake bite', 'a broken leg', 'a broken arm', 'swine flu']

klingonisms = [
	"I have challenged the entire ISO-9000 review team to a round of Bat-Leth practice on the holodeck. They will not concern us again.",
	"A TRUE Klingon warrior does not comment his code!",
	"Behold, the keyboard of Kalis! The greatest Klingon code warrior that ever lived!",
	"By filing this bug report you have challenged the honour of my family. Prepare to die! ",
	"C++? That is for children. A Klingon Warrior uses only machine code, keyed in on the front panel switches in raw binary.",
	"Debugging? Klingons do not debug. Bugs are good for building character in the user.",
	"Debugging? Klingons do not debug. Our software does not coddle the weak.",
	"Defensive programming? Never! Klingon programs are always on the offense. Yes, Offensive programming is what we do best.",
	"I am without honor...my children are without honor... My father coded at the Battle of Kittimer...and...and...he... HE ALLOWED HIMSELF TO BE MICROMANAGED. <shudder>",
	"I have challenged the entire testing team to a Bat-Leth contest. They will not concern us again.",
	"Indentation?! - I will show you how to indent when I indent your skull!",
	"Klingon function calls do not have 'parameters' - they have 'arguments' - and they ALWAYS WIN THEM.",
	"Klingon multitasking systems do not support 'time-sharing'. When a Klingon program wants to run, it challenges the scheduler in hand-to-hand combat and owns the machine.",
	"Klingon programs don't do accountancy. For that, you need a Farengi programmer.",
	"Klingon software does NOT have BUGS. It has FEATURES, and those features are too sophisticated for a Romulan pig like you to understand.",
	"Klingons do not believe in indentation - except perhaps in the skulls of their project managers.",
	"Klingons do not make software 'releases'. Our software 'escapes'. Typically leaving a trail of wounded programmers in it's wake.",
	"Microsoft is actually a secret Farengi-Klingon alliance designed to cripple the Federation. The Farengi are doing the marketing and the Klingons are writing the code.",
	"My program has just dumped Stova Core!",
	"Our competitors are without honor!",
	"Our users will know fear and cower before our software! Ship it! Ship it and let them flee like the dogs they are! ",
	"Perhaps it IS a good day to Die! I say we ship it!",
	"Python? That is for children. A Klingon Warrior uses only machine code, keyed in on the front panel switches in raw binary. ",
	"Specs are for the weak and timid!",
	"This code is a piece of crap! You have no honor!",
	"This machine is a piece of GAGH! I need dual Pentium processors if I am to do battle with this code!",
	"What is this talk of 'release'? Klingons do not make software 'releases'. Our software 'escapes' leaving a bloody trail of designers and quality assurance people in its wake.",
	"You cannot truly appreciate Dilbert unless you've read it in the original Klingon.",
	"You humans call this thing a 'cursor' and you move it with 'mouse'! Bah! A Klingon would not use such a device. We have a Karaghht-Gnot - which is best translated as 'An Aiming Daggar of 16x16 pixels' and we move it using a Gshnarrrf which is a creature from the Klingon homeworld which posesses just one, (disproportionately large) testicle...which it rubs along the ground.....uh do we really need to talk about this?",
	"You question the worthiness of my code? I should kill you where you stand!",
]

murphys_laws = [
	"In any field of scientific endeavor, anything that can go wrong, will.",
	"If the possibility exists of several things going wrong, the one that will go wrong is the one that will do the most damage.",
	"Everything will go wrong at one time - That time is always when you least expect it.",
	"If nothing can go wrong, something will.",
	"Nothing is as easy as it looks.",
	"Everything takes longer than you think.",
	"Left to themselves, things always go from bad to worse.",
	"Nature always sides with the hidden flaw.",
	"Given the most inappropriate time for something to go wrong, that's when it will occur.",
	"Mother Nature is a bitch.",
	"The universe is not indifferent to intelligence, it is actively hostile to it.",
	"If everything seems to be going well, you have obviously overlooked something.",
	"If in any problem you find yourself doing an immense amount of work, the answer can be obtained by simple inspection.",
	"Never make anything simple and efficient when a way can be found to make it complex and wonderful.",
	"If it doesn't fit, use a bigger hammer.",
	"In an instrument or device characterized by a number of plus-or-minus errors, the total error will be the sum of all the errors adding in the same direction.",
	"In any given calculation, the fault will never be placed if more than one person is involved.",
	"In any given discovery, the credit will never be properly placed if more than one person is involved.",
	"All warranty and guarantee clauses become invalid upon payment of the final invoice.",
	"If there are two or more ways to do something, and one of those ways can result in a catastrophe, then someone will do it.",
	"Never attribute to malice that which can be adequately explained by stupidity.",
	"Sufficiently advanced incompetence is indistinguishable from malice.",
	"Hofstadter's Law: It always takes longer than you expect, even when you take into account Hofstadter's Law.",
	"Ninety percent of everything is crap",
]

socialstrategies = [
	"Facilitate audience conversations and drive engagement with social currency",
	"Maximise breakthrough by leveraging influencers",
	"Amplify word of mouth by motivating influencers",
	"Humanise the brand by driving the audience conversations",
	"Harness social currency to drive buzz",
	"Drive break through conversations with an engaging viral",
	"Utilise social currency to amplify experiences and drive conversations",
	"Maximise buzz by driving word of mouth from relevant influencers",
	"Increase organic growth by exposing audiences to the brand through breakthrough viral communications",
	"Encourage positive conversations to drive advocacy",
	"Target influencers with engaging assets to act as platforms for conversation",
	"Provide brand ambassadors with compelling conversation hooks to enter into communities and fuel advocacy",
	"Expose new and relevant communities to the brand by providing assets to encourage brand evangelism",
	"Enhance the customer experience by facilitating authentic conversations",
	"Expose new users to the brand through organic conversations",
	"Build loyalty & increased engagement through ongoing conversation and brand experience",
	"Strengthen the emotional connection with the brand by building relationship",
	"Maximise the customer experience, driving engagement and bringing the brand alive",
	"Ignite the existing community and attract new members by amplifying the experience with relevant and engaging content",
	"Identify relevant and compelling hooks for the audience, create content around the hooks and integrate it into their social repertoires",
	"Activate audience by giving them compelling social experiences, encouraging advocacy",]


def wchoice(d):
	l = []
	for item, num in d.iteritems():
		l.extend([item] * (num*100))
	return random.choice(l)

def splitem(s):
	s = s.rstrip('?.!')
	if ':' in s:
		question, choices = s.rsplit(':', 1)
	else:
		choices = s

	c = choices.split(',')
	if ' or ' in c[-1]:
		c = c[:-1] + c[-1].split(' or ')

	c = [x.strip() for x in c]
	c = filter(None, c)
	return c

class Karma(storage.SelectableStorage):
	pass

class SQLiteKarma(Karma, storage.SQLiteStorage):
	def init_tables(self):
		CREATE_KARMA_VALUES_TABLE = '''
			CREATE TABLE IF NOT EXISTS karma_values (karmaid INTEGER NOT NULL, karmavalue INTEGER, primary key (karmaid))
		'''
		CREATE_KARMA_KEYS_TABLE = '''
			CREATE TABLE IF NOT EXISTS karma_keys (karmakey varchar, karmaid INTEGER, primary key (karmakey))
		'''
		CREATE_KARMA_LOG_TABLE = '''
			CREATE TABLE IF NOT EXISTS karma_log (karmakey varchar, logid INTEGER, change INTEGER)
		'''
		self.db.execute(CREATE_KARMA_VALUES_TABLE)
		self.db.execute(CREATE_KARMA_KEYS_TABLE)
		self.db.execute(CREATE_KARMA_LOG_TABLE)
		self.db.commit()

	def lookup(self, thing):
		thing = thing.strip().lower()
		LOOKUP_SQL = 'SELECT karmavalue from karma_keys k join karma_values v on k.karmaid = v.karmaid where k.karmakey = ?'
		try:
			karma = self.db.execute(LOOKUP_SQL, [thing]).fetchone()[0]
		except:
			karma = 0
		if karma == None:
			karma = 0
		return karma

	def set(self, thing, value):
		thing = thing.strip().lower()
		value = int(value)
		UPDATE_SQL = 'UPDATE karma_values SET karmavalue = ? where karmaid = (select karmaid from karma_keys where karmakey = ?)'
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
		UPDATE_SQL = 'UPDATE karma_values SET karmavalue = ? where karmaid = (select karmaid from karma_keys where karmakey = ?)'
		res = self.db.execute(UPDATE_SQL, (value, thing))
		if res.rowcount == 0:
			INSERT_VALUE_SQL = 'INSERT INTO karma_values (karmavalue) VALUES (?)'
			INSERT_KEY_SQL = 'INSERT INTO karma_keys (karmakey, karmaid) VALUES (?, ?)'
			ins = self.db.execute(INSERT_VALUE_SQL, [value])
			self.db.execute(INSERT_KEY_SQL, (thing, ins.lastrowid))
		self.db.commit()

	def list(self, select=0):
		KARMIC_VALUES_SQL = 'SELECT karmaid, karmavalue from karma_values order by karmavalue desc'
		KARMA_KEYS_SQL= 'SELECT karmakey from karma_keys where karmaid = ?'

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

	def link(self, thing1, thing2):
		t1 = thing1.strip().lower()
		t2 = thing2.strip().lower()
		GET_KARMAID_SQL = 'SELECT karmaid FROM karma_keys WHERE karmakey = ?'
		try:
			t1id = self.db.execute(GET_KARMAID_SQL, [t1]).fetchone()[0]
		except TypeError:
			raise KeyError
		t1value = self.lookup(t1)
		try:
			t2id = self.db.execute(GET_KARMAID_SQL, [t2]).fetchone()[0]
		except TypeError:
			raise KeyError
		t2value = self.lookup(t2)

		newvalue = t1value + t2value
		self.db.execute('UPDATE karma_keys SET karmaid = ? where karmaid = ?', (t1id, t2id)) #update the keys so t2 points to t1s value
		self.db.execute('DELETE FROM karma_values WHERE karmaid = ?', (t2id,)) #drop the old value row for neatness
		self.db.execute('UPDATE karma_values SET karmavalue = ? where karmaid = ?', (newvalue, t1id)) #set the new combined value
		self.db.commit()

	def _get(self, id):
		"""
		Return keys and value for karma id
		"""
		VALUE_SQL = "SELECT karmavalue from karma_values where karmaid = ?"
		KEYS_SQL = "SELECT karmakey from karma_keys where karmaid = ?"
		value = db.execute(VALUE_SQL, [id]).fetchall()[0][0]
		keys_cur = db.execute(KEYS_SQL, [id]).fetchall()
		keys = sorted(x[0] for x in key_cur)
		return keys, value

	def search(self, term):
		query = "SELECT distinct karmaid from karma_keys where karmakey like ?"
		matches = (id for (id,) in self.db.execute(query, '%%'+term+'%%'))
		return (self._lookup(id) for id in matches)

	def export_all(self):
		return self.list()


class MongoDBKarma(Karma, storage.MongoDBStorage):
	collection_name = 'karma'
	def lookup(self, thing):
		thing = thing.strip().lower()
		res = self.db.find_one({'names':thing})
		return res['value'] if res else 0

	def set(self, thing, value):
		thing = thing.strip().lower()
		value = int(value)
		query = {'names': {'$in': [thing]}}
		oper = {'$set': {'value': value}, '$addToSet': {'names': thing}}
		self.db.update(query, oper, upsert=True)

	def change(self, thing, change):
		thing = thing.strip().lower()
		change = int(change)
		query = {'names': {'$in': [thing]}}
		oper = {'$inc': {'value': change}, '$addToSet': {'names': thing}}
		self.db.update(query, oper, upsert=True)

	def list(self, select=0):
		res = list(self.db.find().sort('value', storage.pymongo.DESCENDING))

		if select > 0:
			selected = res[:select]
		elif select < 0:
			selected = res[select:]
		else:
			selected = res
		aslist = lambda val: val if isinstance(val, list) else [val]
		return [
			(aslist(rec['names']), rec['value'])
			for rec in selected
		]

	def link(self, thing1, thing2):
		thing1 = thing1.strip().lower()
		thing2 = thing2.strip().lower()
		rec = self.db.find_one({'names': thing2})
		if not rec: raise KeyError(thing2)
		try:
			query = {'names': thing1}
			update = {
				'$inc': {'value': rec['value']},
				'$pushAll': {'names': rec['names']},
			}
			self.db.update(query, update, safe=True)
		except Exception:
			raise KeyError(thing1)
		self.db.remove(rec)

	def search(self, term):
		pattern = re.compile('.*' + re.escape(term) + '.*')
		return (
			(rec['names'], rec['value'])
			for rec in self.db.find({'names': pattern})
		)

	def import_(self, item):
		names, value = item
		self.db.insert(dict(
			names = names,
			value = value,
			))

	def _all_names(self):
		return set(itertools.chain.from_iterable(
			names
			for names, value in self.search('')
		))

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
					'$pushAll': {'names': duplicate['names']},
				}
				self.db.update(query, update, safe=True)
				self.db.remove(duplicate)

def init_karma(uri):
	globals().update(
		karma = Karma.from_URI(uri)
	)

# for backward compatibility:
def karmaChange(db, *args, **kwargs):
	return karma.change(*args, **kwargs)

def init_quotes(uri):
	globals().update(quotes = Quotes.from_URI(uri))

class Quotes(storage.SelectableStorage):
	lib = 'pmx'

class SQLiteQuotes(Quotes, storage.SQLiteStorage):
	def init_tables(self):
		CREATE_QUOTES_TABLE = '''
			CREATE TABLE IF NOT EXISTS quotes (quoteid INTEGER NOT NULL, library VARCHAR, quote TEXT, PRIMARY KEY (quoteid))
		'''
		CREATE_QUOTES_INDEX = '''CREATE INDEX IF NOT EXISTS ix_quotes_library on quotes(library)'''
		CREATE_QUOTE_LOG_TABLE = '''
			CREATE TABLE IF NOT EXISTS quote_log (quoteid varchar, logid INTEGER)
		'''
		self.db.execute(CREATE_QUOTES_TABLE)
		self.db.execute(CREATE_QUOTES_INDEX)
		self.db.execute(CREATE_QUOTE_LOG_TABLE)
		self.db.commit()

	def quoteLookupWNum(self, rest=''):
		rest = rest.strip()
		if rest:
			if rest.split()[-1].isdigit():
				num = rest.split()[-1]
				query = ' '.join(rest.split()[:-1])
				qt, i, n = self.quoteLookup(query, num)
			else:
				qt, i, n = self.quoteLookup(rest)
		else:
			qt, i, n = self.quoteLookup()
		return qt, i, n

	def quoteLookup(self, thing='', num=0):
		lib = self.lib
		BASE_SEARCH_SQL = 'SELECT quoteid, quote FROM quotes WHERE library = ? %s order by quoteid'
		thing = thing.strip().lower()
		num = int(num)
		if thing:
			SEARCH_SQL = BASE_SEARCH_SQL % (' AND %s' % (' AND '.join(["quote like '%%%s%%'" % x for x in thing.split()])))
		else:
			SEARCH_SQL = BASE_SEARCH_SQL % ''
		results = [x[1] for x in self.db.execute(SEARCH_SQL, (lib,)).fetchall()]
		n = len(results)
		if n > 0:
			if num:
				i = num-1
			else:
				i = random.randrange(n)
			quote = results[i]
		else:
			i = 0
			quote = ''
		return (quote, i+1, n)

	def quoteAdd(self, quote):
		lib = self.lib
		quote = quote.strip()
		ADD_QUOTE_SQL = 'INSERT INTO quotes (library, quote) VALUES (?, ?)'
		res = self.db.execute(ADD_QUOTE_SQL, (lib, quote,))
		quoteid = res.lastrowid
		log_id, log_message = self.db.execute('SELECT id, message FROM LOGS order by datetime desc limit 1').fetchone()
		if quote in log_message:
			self.db.execute('INSERT INTO quote_log (quoteid, logid) VALUES (?, ?)', (quoteid, log_id))
		self.db.commit()

	def __iter__(self):
		query = "SELECT quote FROM quotes WHERE library = ?"
		return self.db.execute(query, [self.lib])

	def export_all(self):
		query = "SELECT quote, library, logid from quotes left outer join quote_log on quotes.quoteid = quote_log.quoteid"
		fields = 'text', 'library', 'log_id'
		return (dict(zip(fields, res)) for res in self.db.execute(query))

class MongoDBQuotes(Quotes, storage.MongoDBStorage):
	collection_name = 'quotes'

	def quoteLookupWNum(self, rest=''):
		rest = rest.strip()
		if rest:
			if rest.split()[-1].isdigit():
				num = rest.split()[-1]
				query = ' '.join(rest.split()[:-1])
				qt, i, n = self.quoteLookup(query, num)
			else:
				qt, i, n = self.quoteLookup(rest)
		else:
			qt, i, n = self.quoteLookup()
		return qt, i, n

	def quoteLookup(self, thing='', num=0):
		thing = thing.strip().lower()
		num = int(num)
		words = thing.split()
		def matches(quote):
			quote = quote.lower()
			return all(word in quote for word in words)
		results = [
			row['text'] for row in
			self.db.find(dict(library=self.lib)).sort('_id')
			if matches(row['text'])
		]
		n = len(results)
		if n > 0:
			if num:
				i = num-1
			else:
				i = random.randrange(n)
			quote = results[i]
		else:
			i = 0
			quote = ''
		return (quote, i+1, n)

	def quoteAdd(self, quote):
		quote = quote.strip()
		quote_id = self.db.insert(dict(library=self.lib, text=quote))
		# see if the quote added is in the last IRC message logged
		newest_first = [('_id', storage.pymongo.DESCENDING)]
		last_message = self.db.database.logs.find_one(sort=newest_first)
		if last_message and quote in last_message['message']:
			self.db.update({'_id': quote_id},
				{'$set': dict(log_id=last_message['_id'])})

	def __iter__(self):
		return self.db.find(library=self.lib)

	def _build_log_id_map(self):
		from . import logging
		if not hasattr(logging.Logger, 'log_id_map'):
			log_db = self.db.database.logs
			logging.Logger.log_id_map = dict(
				(logging.MongoDBLogger.extract_legacy_id(rec['_id']), rec['_id'])
				for rec in log_db.find(fields=[])
			)
		return logging.Logger.log_id_map

	def import_(self, quote):
		log_id_map = self._build_log_id_map()
		log_id = quote.pop('log_id', None)
		log_id = log_id_map.get(log_id, log_id)
		if log_id is not None:
			quote['log_id'] = log_id
		self.db.insert(quote)

def get_html(url):
	h = httplib2.Http()
	resp, html = h.request(url,
	headers={'User-Agent' : 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2b1) Gecko/20091014 Firefox/3.6b1 GTB5'})
	assert 200 <= resp.status < 300
	return html

def_exp1 = re.compile(r"<div><span class=f>.*?</span>(.+?)</div>", re.MULTILINE)
def_exp2 = re.compile(r"Definition for.*<div class=s><div>(.+?)<", re.MULTILINE)
urbd_exp = re.compile(r"""<td class=['"]word['"]>(.+?)^</td>$(?:.+?)<div class=['"]definition['"]>(.+?)</div>""", re.MULTILINE | re.DOTALL )

def strip_tags(string):
	"""
	Remove HTML tags from a string.

	>>> strip_tags('<div>foo and <b>bar</b></div>')
	'foo and bar'
	"""
	return re.sub('<.*?>', '', string).replace('&nbsp;', ' ')

def lookup(word):
	'''
	Get a definition for a word (uses Wordnik)
	'''
	# Jason's key - do not abuse
	key = 'edc4b9b94b341eeae350e087c2e05d2f5a2a9e0478cefc6dc'
	w = wordnik.Wordnik(key)
	definitions = w.word_get_definitions(word)
	if definitions:
		return unicode(definitions[0]['text'])
lookup.provider = 'Wordnik'

def urbanlookup(word):
	'''Gets a Urban Dictionary summary for a word.
	'''
	word = urllib.quote_plus(word)
	html = get_html('http://urbandictionary.com/define.php?term=%s' % word)
	match = urbd_exp.search(html)
	if not match:
		return None, None
	word, definition = match.groups()
	definition = ' '.join(definition.replace('<br/>', '').splitlines())
	return word.strip(), definition.strip()

html_strip = re.compile(r'<[^>]+?>')
NUM_ACS = 3

def lookup_acronym(acronym):
	acronym = acronym.strip().upper()
	html = get_html('http://www.acronymfinder.com/%s.html' % acronym)
	idx = html.find('<th>Meaning</th>')
	if idx == -1:
		return None
	all = []
	for x in xrange(NUM_ACS):
		idx = html.find('%s</a>' % acronym, idx)
		idx = html.find('<td>', idx)
		edx = html.find('</td>', idx)
		ans = html[idx+4:edx]
		ans = html_strip.sub('', ans)
		all.append(ans)

	return all

# passive-aggresive statement generator
adj_intros = [
	'your %s is legendary',
	'I love how your %s shows up in your work',
	'dream big, because %s is going to pay off for you big-time',
	'somehow your %s always manages to shine through',
	'if only we all possessed your %s',
	'you have rare %s',
	'even if I tried, I couldn\'t replicate your %s',
	'few can compete with your epic %s',
	'I always stop and smile at the telltale %s when correcting your mistakes',
]

adjs = [
	'incompetence',
	'laziness',
	'ignorance',
	'frailty',
	'lack of attention to detail',
	'BO',
	'stupidity',
	'lack of personality',
	'clever decision',
	'ability to "introcude a failure"',
]

farewells = [
	'Hugs and kisses',
	'Keep up the good work',
	'Chin up',
	'I hope you rot',
	'Have a great day',
	'Must get back to work',
	'Thanks for everything',
	'Your BFF',
	'Don\'t ever change',
	'Have a nice life',
	'Don\' stop bragplaining',
]

direct_apologies = [
	"%(a)s profusely apologizes to %(b)s",
	"%(a)s sincerely apologizes to %(b)s",
	"%(a)s would like to apologize to %(b)s for any physical, emotional, or mental anguish %(a)s's action, justified as they may have been, caused.",
	"%(a)s would like to apologize to %(b)s for any physical, emotional, or mental anguish %(a)s's action, caused.",
	"%(b)s: %(a)s is like sorry or something.",
]

apologies = [
	"%(a)s is sorry.",
	"%(a)s would like to tearfully apologize to everyone in a widely publicized press conference.",
	"%(a)s profusely apologizes.",
	"%(a)s sincerely apologizes.",
	"%(a)s would like to apologize for any physical, emotional, or mental anguish that %(a)s's actions may have caused.",
	"%(a)s apologizes and would like to point out there is no reason legal action to be taken.",
	"%(a)s is sorry or something.",
]

interview_excuses = [
	"I need to go to the Dentist",
	"I have a Doctor's appointment",
	"my little brother got his arm stuck in the microwave, and my mom had to take him to the hospital and my grandma freaked out and dropped acid and hijacked a busload of penguins, so it's kind of a family crisis.",
	"I need to go car shopping",
	"I have an appointment with an attorney to make a will",
	"my grandmother's funeral is today",
	"I need to go to the DMV",
	"I have a terrible case of diarrhea",
	"I need to get some allergy shots",
	"the power went out in Tennessee",
	"um, a huge snowpocalypse hit DC",
	'''I'm getting lunch with a "friend"''',
	"I'm heading off to a concert",
	'''It looks like I'll be "working" from "home" today''',
	"I've been maliciously sunburned, and need to stay home and get jumped by my chihuahuas",
	"I need to go get a haircut",
	"I stepped out to get my marriage license",
	"I, um...",
	"I, um... won't be in...",
	'my VPN connectiond dropped, so I took the opportunity to grab some food.',
	'sorry, I ran over a beer bottle on the way in and flatted',
	'I exceeded my internet quota, so I needed to find another connection',
	'I took the wrong bus this morning. Again.',
	'I was held up by CalTrain delays',
	'CalTrain decided to help our overpopulation problem this morning',
]

def passagg(recipient='', sender=''):
	adj = random.choice(adjs)
	if random.randint(0,1):
		lead = ""
		trail=recipient if not recipient else ", %s" % recipient
	else:
		lead=recipient if not recipient else "%s, " % recipient
		trail=""
	start = "%s%s%s." % (lead, random.choice(adj_intros) % adj, trail)
	if not lead and not start[0].isupper():
		start = "%s%s" % (start[0].upper(), start[1:])
	end = random.choice(farewells)
	if sender:
		end = "%s, %s" % (end, sender)
	end = "%s." % end
	final = " ".join([start, end])
	return final

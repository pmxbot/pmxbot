import sys
import re
import random
import string
import csv
import urllib.parse

import dateutil.parser
import pkg_resources
from bs4 import BeautifulSoup
import requests
import pytz

import pmxbot
from .core import command, contains, attach
from . import util
from . import karma
from . import logging
from . import phrases


def plaintext(html):
	"Extract the text from HTML."
	return BeautifulSoup(html, 'html.parser').text


def suppress_exceptions(callables, exceptions=Exception):
	"""
	Suppress supplied exceptions (tuple or single exception)
	encountered when a callable is invoked.
	>>> five_over_n = lambda n: 5//n
	>>> import functools
	>>> callables = (functools.partial(five_over_n, n) for n in range(-3,3))
	>>> safe_results = suppress_exceptions(callables, ZeroDivisionError)
	>>> tuple(safe_results)
	(-2, -3, -5, 5, 2)
	"""
	for callable in callables:
		try:
			yield callable()
		except exceptions:
			pass


@command()
def boo(rest):
	"Boo someone"
	slapee = rest
	karma.Karma.store.change(slapee, -1)
	return "/me BOOO %s!!! BOOO!!!" % slapee


@command(aliases=("slap", "ts"))
def troutslap(rest):
	"Slap some(one|thing) with a fish"
	slapee = rest
	karma.Karma.store.change(slapee, -1)
	return "/me slaps %s around a bit with a large trout" % slapee


@command(aliases="kh")
def keelhaul(rest):
	"Inflict great pain and embarassment on some(one|thing)"
	keelee = rest
	karma.Karma.store.change(keelee, -1)
	return (
		"/me straps %s to a dirty rope, tosses 'em overboard and pulls "
		"with great speed. Yarrr!" % keelee)


@command(aliases="d")
def dance():
	"Do a little dance"
	yield 'O-\-<'
	yield 'O-|-<'
	yield 'O-/-<'


@command(aliases="pc")
def panic():
	"Panic!"
	yield 'O-|-<'
	yield 'O-<-<'
	yield 'O->-<'
	yield 'AAAAAAAHHHH!!!  HEAD FOR THE HILLS!'


@command(aliases="ducky")
def duck():
	"Display a helpful duck"
	yield '__("<'
	yield '\__/'
	yield ' ^^'


@command(aliases='approve')
def rubberstamp(rest):
	"Approve something"
	parts = ["Bad credit? No credit? Slow credit?"]
	rest = rest.strip()
	if rest:
		parts.append("%s is" % rest)
		karma.Karma.store.change(rest, 1)
	parts.append("APPROVED!")
	return " ".join(parts)


@command(aliases="c")
def cheer(rest):
	"Cheer for something"
	if rest:
		karma.Karma.store.change(rest, 1)
		return "/me cheers for %s!" % rest
	karma.Karma.store.change('the day', 1)
	return "/me cheers!"


@command(aliases="clap")
def golfclap(rest):
	"Clap for something"
	clapv = random.choice(phrases.clapvl)
	adv = random.choice(phrases.advl)
	adj = random.choice(phrases.adjl)
	if rest:
		clapee = rest.strip()
		karma.Karma.store.change(clapee, 1)
		return "/me claps %s for %s, %s %s." % (clapv, rest, adv, adj)
	return "/me claps %s, %s %s." % (clapv, adv, adj)


@command(aliases='fc')
def featurecreep():
	"Generate feature creep (P+C http://www.dack.com/web/bullshit.html)"
	verb = random.choice(phrases.fcverbs).capitalize()
	adjective = random.choice(phrases.fcadjectives)
	noun = random.choice(phrases.fcnouns)
	return '%s %s %s!' % (verb, adjective, noun)


@command()
def strategy():
	"""
	Social Media Strategy, courtsey of
	http://whatthefuckismysocialmediastrategy.com/
	"""
	return random.choice(phrases.socialstrategies)


@command(aliases='otrail')
def oregontrail(channel, nick, rest):
	"It's edutainment!"
	rest = rest.strip()
	if rest:
		who = rest.strip()
	else:
		who = random.choice([nick, channel, 'pmxbot'])
	action = random.choice(phrases.otrail_actions)
	if action in ('has', 'has died from'):
		issue = random.choice(phrases.otrail_issues)
		text = '%s %s %s.' % (who, action, issue)
	else:
		text = '%s %s' % (who, action)
	return text


@command(aliases='zing')
def zinger(rest):
	"ZING!"
	name = 'you'
	if rest:
		name = rest.strip()
		karma.Karma.store.change(name, -1)
	return "OH MAN!!! %s TOTALLY GOT ZING'D!" % (name.upper())


@command(aliases=("m", "appreciate", "thanks", "thank", "gracias", "grazie"))
def motivate(channel, rest):
	"Motivate someone"
	if rest:
		r = rest.strip()
		m = re.match(r'^(.+)\s*\bfor\b\s*(.+)$', r)
		if m:
			r = m.groups()[0].strip()
	else:
		r = channel
	karma.Karma.store.change(r, 1)
	return "you're doing good work, %s!" % r


@command(aliases=("im", 'ironicmotivate',))
def imotivate(channel, rest):
	'Ironically "Motivate" someone'
	if rest:
		r = rest.strip()
		karma.Karma.store.change(r, -1)
	else:
		r = channel
	return '''you're "doing" "good" "work", %s!''' % r


@command(aliases=("nail", "n"))
def nailedit(rest):
	"Nail that interview"
	random.shuffle(phrases.interview_excuses)
	yield "Sorry, but " + phrases.interview_excuses[0]
	yield("/me Nailed it!")


@command(aliases="dm")
def demotivate(channel, rest):
	"Demotivate someone"
	if rest:
		r = rest.strip()
	else:
		r = channel
	karma.Karma.store.change(r, -1)
	return "you're doing horrible work, %s!" % r


@command(name="8ball", aliases="8")
def eball(rest):
	"Ask the magic 8ball a question"
	try:
		url = 'https://8ball.delegator.com/magic/JSON/'
		url += rest
		result = requests.get(url).json()['magic']['answer']
	except Exception:
		result = util.wchoice(phrases.ball8_opts)
	return result


@command()
def roll(rest, nick):
	"Roll a die, default = 100."
	if rest:
		rest = rest.strip()
		die = int(rest)
	else:
		die = 100
	myroll = random.randint(1, die)
	return "%s rolls %s" % (nick, myroll)


@command()
def flip(nick):
	"Flip a coin"
	myflip = random.choice(('Heads', 'Tails'))
	return "%s gets %s" % (nick, myflip)


@command()
def deal(nick):
	"Deal or No Deal?"
	mydeal = random.choice(('Deal!', 'No Deal!'))
	return "%s gets %s" % (nick, mydeal)


@command(aliases="t")
def ticker(rest):
	"Look up a ticker symbol's current trading value"
	ticker = rest.upper()
	# let's use Yahoo's nifty csv facility, and pull last time/price both
	symbol = 's'
	last_trade_price = 'l1'
	last_trade_time = 't1'
	change_percent = 'p2'
	format = ''.join((symbol, last_trade_time, last_trade_price, change_percent))
	url = (
		'http://finance.yahoo.com/d/quotes.csv?s=%(ticker)s&f=%(format)s'
		% locals())
	stock_info = csv.reader(util.open_url(url).text.splitlines())
	last_trade, = stock_info
	ticker_given, time, price, diff = last_trade
	if ticker_given != ticker:
		return "d'oh... could not find information for symbol %s" % ticker
	return '%(ticker)s at %(time)s (ET): %(price)s (%(diff)s)' % locals()


@command(aliases=("p", 'p:', "pick:"))
def pick(rest):
	"Pick between a few options"
	question = rest.strip()
	choices = util.splitem(question)
	if len(choices) == 1:
		return "I can't pick if you give me only one choice!"
	else:
		pick = random.choice(choices)
		certainty = random.sample(phrases.certainty_opts, 1)[0]
		return "%s... %s %s" % (pick, certainty, pick)


@command(aliases=("lunchpick", "lunchpicker"))
def lunch(rest):
	"Pick where to go to lunch"
	rs = rest.strip()
	if not rs:
		return "Give me an area and I'll pick a place: (%s)" % (
			', '.join(list(pmxbot.config.lunch_choices)))
	if rs not in pmxbot.config.lunch_choices:
		return "I didn't recognize that area; here's what i have: (%s)" % (
			', '.join(list(pmxbot.config.lunch_choices)))
	choices = pmxbot.config.lunch_choices[rs]
	return random.choice(choices)


@command(aliases=("pw", "passwd",))
def password(rest):
	"""
	Generate a random password, similar to
	http://www.pctools.com/guides/password
	"""
	charsets = [
		string.ascii_lowercase,
		string.ascii_uppercase,
		string.digits,
		string.punctuation,
	]
	passwd = []

	try:
		length = rest.strip() or 12
		length = int(length)
	except ValueError:
		return 'need an integer password length!'

	for i in range(length):
		passwd.append(random.choice(''.join(charsets)))

	if length >= len(charsets):
		# Ensure we have at least one character from each charset
		replacement_indices = random.sample(range(length), len(charsets))
		for i, charset in zip(replacement_indices, charsets):
			passwd[i] = random.choice(charset)

	return ''.join(passwd)


@command()
def insult(rest):
	"Generate a random insult from datahamster"
	# not supplying any style will automatically redirect to a random
	url = 'http://autoinsult.datahamster.com/'
	ins_type = random.randrange(4)
	ins_url = url + "?style={ins_type}".format(**locals())
	insre = re.compile('<div class="insult" id="insult">(.*?)</div>')
	resp = requests.get(ins_url)
	resp.raise_for_status()
	insult = insre.search(resp.text).group(1)
	if not insult:
		return
	if rest:
		insultee = rest.strip()
		karma.Karma.store.change(insultee, -1)
		if ins_type in (0, 2):
			cinsre = re.compile(r'\b(your)\b', re.IGNORECASE)
			insult = cinsre.sub("%s's" % insultee, insult)
		elif ins_type in (1, 3):
			cinsre = re.compile(r'^([TY])')
			insult = cinsre.sub(
				lambda m: "%s, %s" % (
					insultee, m.group(1).lower()), insult)
	return insult


@command(aliases='surreal')
def compliment(rest):
	"""
	Generate a random compliment from
	http://www.madsci.org/cgi-bin/cgiwrap/~lynn/jardin/SCG
	"""
	compurl = 'http://www.madsci.org/cgi-bin/cgiwrap/~lynn/jardin/SCG'
	comphtml = ''.join([i.decode() for i in urllib.request.urlopen(compurl)])
	compmark1 = '<h2>\n\n'
	compmark2 = '\n</h2>'
	compliment = comphtml[
		comphtml.find(compmark1) + len(compmark1):comphtml.find(compmark2)]
	if compliment:
		compliment = re.compile(r'\n').sub('%s' % ' ', compliment)
		compliment = re.compile(r'  ').sub('%s' % ' ', compliment)
		if rest:
			complimentee = rest.strip()
			karma.Karma.store.change(complimentee, 1)
			compliment = re.compile(r'\b(your)\b', re.IGNORECASE).sub(
				'%s\'s' % complimentee, compliment)
			compliment = re.compile(r'\b(you are)\b', re.IGNORECASE).sub(
				'%s is' % complimentee, compliment)
			compliment = re.compile(r'\b(you have)\b', re.IGNORECASE).sub(
				'%s has' % complimentee, compliment)
		return compliment


@command(name='emergencycompliment', aliases=('ec', 'emercomp'))
def emer_comp(rest):
	"Return a random compliment from http://emergencycompliment.com/"
	comps = util.load_emergency_compliments()
	compliment = random.choice(comps)
	if rest:
		complimentee = rest.strip()
		karma.Karma.store.change(complimentee, 1)
		return "%s: %s" % (complimentee, compliment)
	return compliment


@command()
def curse(rest):
	"Curse the day!"
	if rest:
		cursee = rest
	else:
		cursee = 'the day'
	karma.Karma.store.change(cursee, -1)
	return "/me curses %s!" % cursee


@command(aliases=('tt', 'tear', 'cry'))
def tinytear(rest):
	"I cry a tiny tear for you."
	if rest:
		return "/me sheds a single tear for %s" % rest
	else:
		return (
			"/me sits and cries as a single tear slowly trickles down "
			"its cheek")


@command(aliases=("shank", "shiv",))
def stab(nick, rest):
	"Stab, shank or shiv some(one|thing)!"
	if rest:
		stabee = rest
	else:
		stabee = 'wildly at anything'
	if random.random() < 0.9:
		karma.Karma.store.change(stabee, -1)
		weapon = random.choice(phrases.weapon_opts)
		weaponadj = random.choice(phrases.weapon_adjs)
		violentact = random.choice(phrases.violent_acts)
		return "/me grabs a %s %s and %s %s!" % (
			weaponadj, weapon, violentact, stabee)
	elif random.random() < 0.6:
		karma.Karma.store.change(stabee, -1)
		return (
			"/me is going to become rich and famous after i invent a "
			"device that allows you to stab people in the face over the "
			"internet")
	else:
		karma.Karma.store.change(nick, -1)
		return (
			"/me turns on its master and shivs %s. This is reality man, "
			"and you never know what you're going to get!" % nick)


@command()
def chain(rest, nick):
	"Chain some(one|thing) down."
	chainee = rest or "someone nearby"
	if chainee == 'cperry':
		tmpl = "/me ties the chains extra tight around {chainee}"
	elif random.random() < .9:
		tmpl = (
			"/me chains {chainee} to the nearest desk. "
			"you ain't going home, buddy."
		)
	else:
		karma.Karma.store.change(nick, -1)
		tmpl = (
			"/me spins violently around and chains {nick} to the nearest "
			"desk.  your days of chaining people down and stomping on their "
			"dreams are over!  get a life, you miserable beast."
		)
	return tmpl.format_map(locals())


@command()
def blame(channel, rest, nick):
	"Pass the buck!"
	if rest:
		blamee = rest
	else:
		blamee = channel
	karma.Karma.store.change(nick, -1)
	if random.randint(1, 10) == 1:
		yield "/me jumps atop the chair and points back at %s." % nick
		yield (
			"stop blaming the world for your problems, you bitter, "
			"two-faced sissified monkey!"
		)
	else:
		yield (
			"I blame %s for everything!  it's your fault!  "
			"it's all your fault!!" % blamee
		)
		yield "/me cries and weeps in despair"


@contains('pmxbot', channels=logging.UnloggedChannels(), rate=.3)
def rand_bot(channel, nick, rest):
	default_commands = [
		'featurecreep', 'insult', 'motivate', 'compliment', 'cheer',
		'golfclap', 'nastygram', 'curse', 'bless', 'job', 'hire',
		'oregontrail',
		'chain', 'tinytear', 'blame', 'panic', 'rubberstamp', 'dance',
		'annoy', 'klingon',
		'storytime', 'murphy', 'quote',
	]

	def lookup_command(cmd_name):
		msg = '!' + cmd_name + ' '
		res = pmxbot.core.CommandHandler.find_matching(msg, channel=None)
		return next(res).func

	functions = pmxbot.config.get('random commands', default_commands)
	exclude_nick_functions = 'quote',
	chosen = random.choice(functions)
	func = lookup_command(chosen)

	# Only use the relevant nick as the target in some cases
	rest = nick if chosen not in exclude_nick_functions else ''
	nick = 'pmxbot'

	# save the func for troubleshooting
	rand_bot.last_func = func

	return attach(func, locals())()


@contains("sqlonrails")
@contains("sql on rails")
def yay_sor(rest):
	karma.Karma.store.change('sql on rails', 1)
	return "Only 76,417 lines..."


calc_exp = re.compile(r"^[0-9 \*/\-\+\)\(\.]+$")


@command()
def calc(rest):
	"Perform a basic calculation"
	mo = calc_exp.match(rest)
	if mo:
		try:
			return str(eval(rest))
		except:
			return "eval failed... check your syntax"
	else:
		return "misformatted arithmetic!"


@command("acronym", aliases=("ac",))
def acit(rest):
	"Look up an acronym"
	word = rest.strip()
	res = util.lookup_acronym(word)
	if res is None:
		return "Arg!  I couldn't expand that..."
	else:
		return ' | '.join(res)


@command()
def fight(nick, rest):
	"Pit two sworn enemies against each other (separate with 'vs.')"
	if rest:
		vtype = random.choice(phrases.fight_victories)
		fdesc = random.choice(phrases.fight_descriptions)
		# valid separators are vs., v., and vs
		pattern = re.compile('(.*) (?:vs[.]?|v[.]) (.*)')
		matcher = pattern.match(rest)
		if not matcher:
			karma.Karma.store.change(nick.lower(), -1)
			args = (vtype, nick, fdesc)
			return "/me %s %s in %s for bad protocol." % args
		contenders = [c.strip() for c in matcher.groups()]
		random.shuffle(contenders)
		winner, loser = contenders
		karma.Karma.store.change(winner, 1)
		karma.Karma.store.change(loser, -1)
		return "%s %s %s in %s." % (winner, vtype, loser, fdesc)


@command()
def progress(rest):
	"Display the progress of something: start|end|percent"
	if rest:
		left, right, amount = [piece.strip() for piece in rest.split('|')]
		ticks = min(int(round(float(amount) / 10)), 10)
		bar = "=" * ticks
		return "%s [%-10s] %s" % (left, bar, right)


@command(aliases=('nerf', 'passive', 'bcc'))
def nastygram(nick, rest):
	"""
	A random passive-agressive comment, optionally directed toward
	some(one|thing).
	"""
	recipient = ""
	if rest:
		recipient = rest.strip()
		karma.Karma.store.change(recipient, -1)
	return util.passagg(recipient, nick.lower())


@command(aliases=('poor', 'comfort'))
def therethere(rest):
	"Sympathy for you."
	if rest:
		karma.Karma.store.change(rest, 1)
		return "There there %s... There there." % rest
	else:
		return "/me shares its sympathy."


@command()
def fml(rest):
	"A SFW version of fml."
	return "indeed"


@command(aliases=('story',))
def storytime(rest):
	"A story is about to be told."
	gather = "Come everyone, gather around the fire. "
	add = (
		"{rest} is about to tell us a story!"
		if rest else "A story is about to be told!")
	return (gather + add).format(**locals())


@command(aliases=('apology', 'apologize',))
def meaculpa(nick, rest):
	"Sincerely apologize"
	if rest:
		rest = rest.strip()

	if rest:
		return random.choice(phrases.direct_apologies) % dict(a=nick, b=rest)
	else:
		return random.choice(phrases.apologies) % dict(a=nick)


@command(aliases=('ver'))
def version(rest):
	"Get the version of pmxbot or one of its plugins"
	pkg = rest.strip() or 'pmxbot'
	if pkg.lower() == 'python':
		return sys.version.split()[0]
	return pkg_resources.require(pkg)[0].version


_TIMEZONES = (pytz.timezone(name) for name in pytz.all_timezones)
TZINFOS = {}
for tz in _TIMEZONES:
	# Add entry for long and short tz names
	# E.g. Europe/Rome and RMT
	TZINFOS[tz._tzname] = TZINFOS[tz.zone] = tz
# Add tzones not defined in pytz mainly from
# http://users.telenet.be/mm011/time%20zone%20abbreviations.html
TZINFOS.update({
	# Europe
	'BST': pytz.FixedOffset(60),
	'IST': pytz.FixedOffset(60),
	'WEST': pytz.FixedOffset(60),
	'CEST': pytz.FixedOffset(60),
	'EEST': pytz.FixedOffset(180),
	'MSK': pytz.FixedOffset(180),
	'MSD': pytz.FixedOffset(240),
	'LDN': pytz.timezone('Europe/London'),
	# America
	'CT': pytz.timezone('US/Central'),
	'ET': pytz.timezone('US/Eastern'),
	'MT': pytz.timezone('US/Mountain'),
	'PT': pytz.timezone('US/Pacific'),
	'AST': pytz.FixedOffset(-240),
	'ADT': pytz.FixedOffset(-180),
	'EDT': pytz.FixedOffset(-240),
	'CST': pytz.FixedOffset(-360),
	'CDT': pytz.FixedOffset(-300),
	'MDT': pytz.FixedOffset(-360),
	'PST': pytz.FixedOffset(-480),
	'PDT': pytz.FixedOffset(-420),
	'AKST': pytz.FixedOffset(-540),
	'AKDT': pytz.FixedOffset(-480),
	# Australia
	'AEST': pytz.FixedOffset(600),
	'AEDT': pytz.FixedOffset(660),
	'ACST': pytz.FixedOffset(570),
	'ACDT': pytz.FixedOffset(630),
	'AWST': pytz.FixedOffset(480),
})


@command(aliases=('tz'))
def timezone(rest):
	"""Convert date between timezones.

	Example:
	> !tz 11:00am UTC in PDT
	11:00 UTC -> 4:00 PDT

	UTC is implicit

	> !tz 11:00am in PDT
	11:00 UTC -> 4:00 PDT

	> !tz 11:00am PDT
	11:00 PDT -> 18:00 UTC

	"""

	if ' in ' in rest:
		dstr, tzname = rest.split(' in ', 1)
	else:
		dstr, tzname = rest, 'UTC'

	tzobj = TZINFOS[tzname.strip()]
	dt = dateutil.parser.parse(dstr, tzinfos=TZINFOS)
	if dt.tzinfo is None:
		dt = pytz.UTC.localize(dt)
	res = dt.astimezone(tzobj)
	return '{} {} -> {} {}'.format(
		dt.strftime('%H:%M'), dt.tzname() or dt.strftime('%z'),
		res.strftime('%H:%M'), tzname)

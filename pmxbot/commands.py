# vim:ts=4:sw=4:noexpandtab

import sys
import re
import random
import csv
import urllib.parse

import pkg_resources
from bs4 import BeautifulSoup
import requests

import pmxbot
from .core import command, contains
from . import util
from . import karma
from . import quotes
from . import phrases


def plaintext(html):
	"Extract the text from HTML."
	return BeautifulSoup(html).text


@command(aliases='g')
def google(client, event, channel, nick, rest):
	"Look up a phrase on google"
	BASE_URL = 'http://ajax.googleapis.com/ajax/services/search/web?'
	params = dict(
		v='1.0',
		q=rest.strip(),
	)
	url = BASE_URL + urllib.parse.urlencode(params)
	resp = requests.get(url)
	resp.raise_for_status()
	results = resp.json()
	if not results['responseData']:
		raise RuntimeError(results['responseDetails'])
	hit1 = results['responseData']['results'][0]
	return ' - '.join((
		urllib.parse.unquote(hit1['url']),
		hit1['titleNoFormatting'],
	))


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
def boo(client, event, channel, nick, rest):
	"Boo someone"
	slapee = rest
	karma.Karma.store.change(slapee, -1)
	return "/me BOOO %s!!! BOOO!!!" % slapee


@command(aliases=("slap", "ts"))
def troutslap(client, event, channel, nick, rest):
	"Slap some(one|thing) with a fish"
	slapee = rest
	karma.Karma.store.change(slapee, -1)
	return "/me slaps %s around a bit with a large trout" % slapee


@command(aliases="kh")
def keelhaul(client, event, channel, nick, rest):
	"Inflict great pain and embarassment on some(one|thing)"
	keelee = rest
	karma.Karma.store.change(keelee, -1)
	return (
		"/me straps %s to a dirty rope, tosses 'em overboard and pulls "
		"with great speed. Yarrr!" % keelee)


@command(aliases=("a", "bother"))
def annoy(client, event, channel, nick, rest):
	"Annoy everyone with meaningless banter"
	def a1():
		yield 'OOOOOOOHHH, WHAT DO YOU DO WITH A DRUNKEN SAILOR'
		yield 'WHAT DO YOU DO WITH A DRUNKEN SAILOR'
		yield "WHAT DO YOU DO WITH A DRUNKEN SAILOR, EARLY IN THE MORNIN'?"

	def a2():
		yield "I'M HENRY THE EIGHTH I AM"
		yield "HENRY THE EIGHTH I AM I AM"
		yield (
			"I GOT MARRIED TO THE GIRL NEXT DOOR; SHE'S BEEN MARRIED "
			"SEVEN TIMES BEFORE")

	def a3():
		yield "BOTHER!"
		yield "BOTHER BOTHER BOTHER!"
		yield "BOTHER BOTHER BOTHER BOTHER!"

	def a4():
		yield "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
		yield "EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE"
		yield "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

	def a5():
		yield "YOUR MOTHER WAS A HAMSTER!"
		yield "AND YOUR FATHER SMELLED OF ELDERBERRIES!"

	def a6():
		yield(
			"My Tallest! My Tallest! Hey! Hey My Tallest! My Tallest? My "
			"Tallest! Hey! Hey! Hey! My Taaaaaaallist! My Tallest? My "
			"Tallest! Hey! Hey My Tallest! My Tallest? It's me! My Tallest? "
			"My Tallest!")
	return random.choice([a1, a2, a3, a4, a5, a6])()


@command(aliases="d")
def dance(client, event, channel, nick, rest):
	"Do a little dance"
	yield 'O-\-<'
	yield 'O-|-<'
	yield 'O-/-<'


@command(aliases="pc")
def panic(client, event, channel, nick, rest):
	"Panic!"
	yield 'O-|-<'
	yield 'O-<-<'
	yield 'O->-<'
	yield 'AAAAAAAHHHH!!!  HEAD FOR THE HILLS!'


@command(aliases="ducky")
def duck(client, event, channel, nick, rest):
	"Display a helpful duck"
	yield '__("<'
	yield '\__/'
	yield ' ^^'


@command(aliases='approve')
def rubberstamp(client, event, channel, nick, rest):
	"Approve something"
	parts = ["Bad credit? No credit? Slow credit?"]
	rest = rest.strip()
	if rest:
		parts.append("%s is" % rest)
		karma.Karma.store.change(rest, 1)
	parts.append("APPROVED!")
	return " ".join(parts)


@command(aliases="c")
def cheer(client, event, channel, nick, rest):
	"Cheer for something"
	if rest:
		karma.Karma.store.change(rest, 1)
		return "/me cheers for %s!" % rest
	karma.Karma.store.change('the day', 1)
	return "/me cheers!"


@command(aliases="clap")
def golfclap(client, event, channel, nick, rest):
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
def featurecreep(client, event, channel, nick, rest):
	"Generate feature creep (P+C http://www.dack.com/web/bullshit.html)"
	verb = random.choice(phrases.fcverbs).capitalize()
	adjective = random.choice(phrases.fcadjectives)
	noun = random.choice(phrases.fcnouns)
	return '%s %s %s!' % (verb, adjective, noun)


@command(aliases='card')
def job(client, event, channel, nick, rest):
	"Generate a job title, http://www.cubefigures.com/job.html"
	j1 = random.choice(phrases.jobs1)
	j2 = random.choice(phrases.jobs2)
	j3 = random.choice(phrases.jobs3)
	return '%s %s %s' % (j1, j2, j3)


@command()
def hire(client, event, channel, nick, rest):
	"When all else fails, pmxbot delivers the perfect employee."
	title = job(client, event, channel, nick, rest)
	task = featurecreep(client, event, channel, nick, rest)
	return "/me finds a new %s to %s" % (title, task.lower())


@command()
def strategy(client, event, channel, nick, rest):
	"""
	Social Media Strategy, courtsey of
	http://whatthefuckismysocialmediastrategy.com/
	"""
	return random.choice(phrases.socialstrategies)


@command(aliases='otrail')
def oregontrail(client, event, channel, nick, rest):
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
def zinger(client, event, channel, nick, rest):
	"ZING!"
	name = 'you'
	if rest:
		name = rest.strip()
		karma.Karma.store.change(name, -1)
	return "OH MAN!!! %s TOTALLY GOT ZING'D!" % (name.upper())


@command(aliases=("m", "appreciate", "thanks", "thank", "gracias"))
def motivate(client, event, channel, nick, rest):
	"Motivate someone"
	if rest:
		r = rest.strip()
	else:
		r = channel
	karma.Karma.store.change(r, 1)
	return "you're doing good work, %s!" % r


@command(aliases=("im", 'ironicmotivate',))
def imotivate(client, event, channel, nick, rest):
	'Ironically "Motivate" someone'
	if rest:
		r = rest.strip()
		karma.Karma.store.change(r, -1)
	else:
		r = channel
	return '''you're "doing" "good" "work", %s!''' % r


@command(aliases=("nail", "n"))
def nailedit(client, event, channel, nick, rest):
	"Nail that interview"
	random.shuffle(phrases.interview_excuses)
	yield "Sorry, but " + phrases.interview_excuses[0]
	yield("/me Nailed it!")


@command(aliases="dm")
def demotivate(client, event, channel, nick, rest):
	"Demotivate someone"
	if rest:
		r = rest.strip()
	else:
		r = channel
	karma.Karma.store.change(r, -1)
	return "you're doing horrible work, %s!" % r


@command(name="8ball", aliases="8")
def eball(client, event, channel, nick, rest):
	"Ask the magic 8ball a question"
	return util.wchoice(phrases.ball8_opts)


@command(aliases='klingonism')
def klingon(client, event, channel, nick, rest):
	"Ask the magic klingon a question"
	return random.choice(phrases.klingonisms)


@command()
def roll(client, event, channel, nick, rest):
	"Roll a die, default = 100."
	if rest:
		rest = rest.strip()
		die = int(rest)
	else:
		die = 100
	myroll = random.randint(1, die)
	return "%s rolls %s" % (nick, myroll)


@command()
def flip(client, event, channel, nick, rest):
	"Flip a coin"
	myflip = random.choice(('Heads', 'Tails'))
	return "%s gets %s" % (nick, myflip)


@command()
def deal(client, event, channel, nick, rest):
	"Deal or No Deal?"
	mydeal = random.choice(('Deal!', 'No Deal!'))
	return "%s gets %s" % (nick, mydeal)


@command(aliases="t")
def ticker(client, event, channel, nick, rest):
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
		% vars())
	stock_info = csv.reader(util.open_url(url).text.splitlines())
	last_trade, = stock_info
	ticker_given, time, price, diff = last_trade
	if ticker_given != ticker:
		return "d'oh... could not find information for symbol %s" % ticker
	return '%(ticker)s at %(time)s (ET): %(price)s (%(diff)s)' % locals()


@command(aliases=("p", 'p:', "pick:"))
def pick(client, event, channel, nick, rest):
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
def lunch(client, event, channel, nick, rest):
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
def password(client, event, channel, nick, rest):
	"""
	Generate a random password, similar to
	http://www.pctools.com/guides/password
	"""
	chars = '32547698ACBEDGFHKJMNQPSRUTWVYXZacbedgfhkjmnqpsrutwvyxz'
	passwd = []
	for i in range(8):
		passwd.append(random.choice(chars))
	return ''.join(passwd)


@command()
def insult(client, event, channel, nick, rest):
	"Generate a random insult from http://autoinsult.com/"
	instype = random.randrange(4)
	insurl = "http://autoinsult.com/webinsult.php?style=%s&r=0&sc=1" % instype
	insre = re.compile('<div class="insult" id="insult">(.*?)</div>')
	html = util.get_html(insurl)
	insult = insre.search(html).group(1)
	if not insult:
		return
	if rest:
		insultee = rest.strip()
		karma.Karma.store.change(insultee, -1)
		if instype in (0, 2):
			cinsre = re.compile(r'\b(your)\b', re.IGNORECASE)
			insult = cinsre.sub("%s's" % insultee, insult)
		elif instype in (1, 3):
			cinsre = re.compile(r'^([TY])')
			insult = cinsre.sub(
				lambda m: "%s, %s" % (
					insultee, m.group(1).lower()), insult)
	return insult


@command(aliases='surreal')
def compliment(client, event, channel, nick, rest):
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
def emer_comp(client, event, channel, nick, rest):
	"Return a random compliment from http://emergencycompliment.com/"
	comps = util.load_emergency_compliments()
	compliment = random.choice(comps)
	if rest:
		complimentee = rest.strip()
		karma.Karma.store.change(complimentee, 1)
		return "%s: %s" % (complimentee, compliment)
	return compliment


@command(aliases="gtw")
def gettowork(client, event, channel, nick, rest):
	"You really ought to, ya know..."
	suggestions = [
		"Um, might I suggest working now",
		"Get to work",
		"Between the coffee break, the smoking break, the lunch break, "
			"the tea break, the bagel break, and the water cooler break, "
			"may I suggest a work break.  It’s when you do some work",
		"Work faster",
		"I didn’t realize we paid people for doing that",
		"You aren't being paid to believe in the power of your dreams",
	]
	suggestion = random.choice(suggestions)
	rest = rest.strip()
	if rest:
		karma.Karma.store.change(rest, -1)
		suggestion = suggestion + ', %s' % rest
	else:
		karma.Karma.store.change(channel, -1)
	karma.Karma.store.change(nick, -1)
	return suggestion


@command(aliases="qbiu")
def bitchingisuseless(client, event, channel, nick, rest):
	"It really is, ya know..."
	rest = rest.strip()
	if rest:
		karma.Karma.store.change(rest, -1)
	else:
		karma.Karma.store.change(channel, -1)
		rest = "foo'"
	advice = 'Quiet bitching is useless, %s. Do something about it.' % rest
	return advice


@command()
def curse(client, event, channel, nick, rest):
	"Curse the day!"
	if rest:
		cursee = rest
	else:
		cursee = 'the day'
	karma.Karma.store.change(cursee, -1)
	return "/me curses %s!" % cursee


@command(aliases=('tt', 'tear', 'cry'))
def tinytear(client, event, channel, nick, rest):
	"I cry a tiny tear for you."
	if rest:
		return "/me sheds a single tear for %s" % rest
	else:
		return (
			"/me sits and cries as a single tear slowly trickles down "
			"its cheek")


@command(aliases=("shank", "shiv",))
def stab(client, event, channel, nick, rest):
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


@command(aliases=("dis", "eviscerate"))
def disembowel(client, event, channel, nick, rest):
	"Disembowel some(one|thing)!"
	if rest:
		stabee = rest
		karma.Karma.store.change(stabee, -1)
	else:
		stabee = "someone nearby"
	return (
		"/me takes %s, brings them down to the basement, ties them to a "
		"leaky pipe, and once bored of playing with them mercifully "
		"ritually disembowels them..." % stabee)


@command(aliases="reembowel")
def embowel(client, event, channel, nick, rest):
	"Embowel some(one|thing)!"
	if rest:
		stabee = rest
		karma.Karma.store.change(stabee, 1)
	else:
		stabee = "someone nearby"
	return (
		"/me (wearing a bright pink cape and yellow tights) swoops in "
		"through an open window, snatches %s, races out of the basement, "
		"takes them to the hospital with entrails on ice, and mercifully "
		"embowels them, saving the day..." % stabee)


@command()
def chain(client, event, channel, nick, rest):
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
def bless(client, event, channel, nick, rest):
	"Bless the day!"
	if rest:
		blesse = rest
	else:
		blesse = 'the day'
	karma.Karma.store.change(blesse, 1)
	return "/me blesses %s!" % blesse


@command()
def blame(client, event, channel, nick, rest):
	"Pass the buck!"
	if rest:
		blamee = rest
	else:
		blamee = channel
	karma.Karma.store.change(nick, -1)
	if random.randint(1, 10) == 1:
		yield "/me jumps atop the chair and points back at %s." % nick
		yield ("stop blaming the world for your problems, you bitter, two-faced sissified monkey!")
	else:
		yield ("I blame %s for everything!  it's your fault!  it's all your fault!!" % blamee)
		yield "/me cries and weeps in despair"


def _request_friendly(auth):
	"""
	Requests does strict type checking on the auth. If it's not a tuple, it
	tries to call it.
	"""
	if auth is not None:
		return tuple(auth)


@command()
def paste(client, event, channel, nick, rest):
	"Drop a link to your latest paste"
	path = '/last/{nick}'.format(**vars())
	url = urllib.parse.urljoin(pmxbot.config.librarypaste, path)
	auth = pmxbot.config.get('librarypaste auth')
	resp = requests.head(url, auth=_request_friendly(auth))
	if not resp.ok:
		return "I couldn't resolve a recent paste of yours. Maybe try " + url
	return resp.headers['location']


@contains('pmxbot', channels='unlogged', rate=.3)
def rand_bot(client, event, channel, nick, rest):
	normal_functions = [
		featurecreep, insult, motivate, compliment, cheer,
		golfclap, nastygram, curse, bless, job, hire, oregontrail,
		chain, tinytear, blame, panic, rubberstamp, dance, annoy, klingon,
		storytime, murphy]
	quote_functions = [quotes.quote]
	func = random.choice(normal_functions + quote_functions)
	nick = nick if func in normal_functions else ''
	# save the func for troubleshooting
	rand_bot.last_func = func
	return func(client, event, channel, 'pmxbot', nick)


@contains("sqlonrails")
def yay_sor(client, event, channel, nick, rest):
	karma.Karma.store.change('sql on rails', 1)
	return "Only 76,417 lines..."


@contains("sql on rails")
def other_sor(*args):
	return yay_sor(*args)

calc_exp = re.compile("^[0-9 \*/\-\+\)\(\.]+$")


@command()
def calc(client, event, channel, nick, rest):
	"Perform a basic calculation"
	mo = calc_exp.match(rest)
	if mo:
		try:
			return str(eval(rest))
		except:
			return "eval failed... check your syntax"
	else:
		return "misformatted arithmetic!"


@command(aliases="def")
def define(client, event, channel, nick, rest):
	"Define a word"
	word = rest.strip()
	res = util.lookup(word)
	fmt = (
		'{lookup.provider} says: {res}' if res else
		"{lookup.provider} does not have a definition for that.")
	return fmt.format(**dict(vars(), lookup=util.lookup))


@command(aliases=("urb", 'ud', 'urbandictionary', 'urbandefine', 'urbandef', 'urbdef'))
def urbandict(client, event, channel, nick, rest):
	"Define a word with Urban Dictionary"
	word = rest.strip()
	definition = util.urban_lookup(word)
	if not definition:
		return "Arg!  I didn't find a definition for that."
	return 'Urban Dictionary says {word}: {definition}'.format(**vars())


@command("acronym", aliases=("ac",))
def acit(client, event, channel, nick, rest):
	"Look up an acronym"
	word = rest.strip()
	res = util.lookup_acronym(word)
	if res is None:
		return "Arg!  I couldn't expand that..."
	else:
		return ' | '.join(res)


@command()
def fight(client, event, channel, nick, rest):
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
def progress(client, event, channel, nick, rest):
	"Display the progress of something: start|end|percent"
	if rest:
		left, right, amount = [piece.strip() for piece in rest.split('|')]
		ticks = min(int(round(float(amount) / 10)), 10)
		bar = "=" * ticks
		return "%s [%-10s] %s" % (left, bar, right)


@command(aliases=('nerf', 'passive', 'bcc'))
def nastygram(client, event, channel, nick, rest):
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
def therethere(client, event, channel, nick, rest):
	"Sympathy for you."
	if rest:
		karma.Karma.store.change(rest, 1)
		return "There there %s... There there." % rest
	else:
		return "/me shares its sympathy."


@command()
def tgif(client, event, channel, nick, rest):
	"Thanks for the words of wisdow, Mike."
	return "Hey, it's Friday! Only two more days left in the work week!"


@command()
def fml(client, event, channel, nick, rest):
	"A SFW version of fml."
	return "indeed"


@command(aliases=('story',))
def storytime(client, event, channel, nick, rest):
	"A story is about to be told."
	gather = "Come everyone, gather around the fire. "
	add = (
		"{rest} is about to tell us a story!"
		if rest else "A story is about to be told!")
	return (gather + add).format(**vars())


@command(aliases=('law',))
def murphy(client, event, channel, nick, rest):
	"Look up one of Murphy's laws"
	return random.choice(phrases.murphys_laws)


@command(aliases=('apology', 'apologize',))
def meaculpa(client, event, channel, nick, rest):
	"Sincerely apologize"
	if rest:
		rest = rest.strip()

	if rest:
		return random.choice(phrases.direct_apologies) % dict(a=nick, b=rest)
	else:
		return random.choice(phrases.apologies) % dict(a=nick)


@command(aliases=('ver'))
def version(client, event, channel, nick, rest):
	"Get the version of pmxbot or one of its plugins"
	pkg = rest.strip() or 'pmxbot'
	if pkg.lower() == 'python':
		return sys.version.split()[0]
	return pkg_resources.require(pkg)[0].version

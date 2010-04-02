# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:noexpandtab
from botbase import command, contains,  _handler_registry, NoLog, LoggingCommandBot
import botbase
import time
import sys, re, urllib, random,  csv
from datetime import date, timedelta
from util import *
from cStringIO import StringIO
try:
	import simplejson as json
except ImportError:
	import json # one last try-- python 2.6?
from saysomething import FastSayer
from cleanhtml import plaintext
from xml.etree import ElementTree
from sqlite3 import dbapi2 as sqlite

QUOTE_PATH = os.path.join(os.path.dirname(__file__), "popquotes.sqlite")
popular_quote_db = sqlite.connect(QUOTE_PATH)

sayer = FastSayer()

@command("google", aliases=('g',), doc="Look a phrase up on google")
def google(client, event, channel, nick, rest):
	BASE_URL = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&'
	url = BASE_URL + urllib.urlencode({'q' : rest.strip()})
	raw_res = urllib.urlopen(url).read()
	results = json.loads(raw_res)
	hit1 = results['responseData']['results'][0]
	return ' - '.join((urllib.unquote(hit1['url']), hit1['titleNoFormatting']))

@command("googlecalc", aliases=('gc',), doc="Calculate something using google")
def googlecalc(client, event, channel, nick, rest):
	query = rest
	gcre = re.compile('<h2 class=r style="font-size:138%"><b>(.+?)</b>')
	html = get_html('http://www.google.com/search?%s' % urllib.urlencode({'q' : query}))
	return plaintext(gcre.search(html).group(1))

@command("time", doc="What time is it in.... Similar to !weather")
def googletime(client, event, channel, nick, rest):
	rest = rest.strip()
	if rest == 'all':
		places = config.places
	elif '|' in rest:
		places = [x.strip() for x in rest.split('|')]
	else:
		places = [rest]
	for place in places:
		if not place.startswith('time'):
			query = 'time ' + place
		else:
			query = place
		timere = re.compile('<td valign=[a-z]+><em>(.+?)(?=<br>|</table>)')
		html = get_html('http://www.google.com/search?%s' % urllib.urlencode({'q' : query}))
		try:
			time = plaintext(timere.search(html).group(1))
			yield time
		except AttributeError:
			continue

@command('weather', aliases=('w'), doc='Get weather for a place. All offices with "all", or a list of places separated by pipes.')
def weather(client, event, channel, nick, rest):
	rest = rest.strip()
	if rest == 'all':
		places = config.places
	elif '|' in rest:
		places = [x.strip() for x in rest.split('|')]
	else:
		places = [rest]
	for place in places:
		try:
			url = "http://www.google.com/ig/api?" + urllib.urlencode({'weather' : place})
			wdata = ElementTree.parse(urllib.urlopen(url))
			city = wdata.find('weather/forecast_information/city').get('data')
			tempf = wdata.find('weather/current_conditions/temp_f').get('data')
			tempc = wdata.find('weather/current_conditions/temp_c').get('data')
			conds = wdata.find('weather/current_conditions/condition').get('data')
			conds = conds.replace('Snow Showers', '\xe2\x98\x83')
			conds = conds.replace('Snow', '\xe2\x98\x83') # Fix snow description
			future_day = wdata.find('weather/forecast_conditions/day_of_week').get('data')
			future_highf = wdata.find('weather/forecast_conditions/high').get('data')
			future_highc = int((int(future_highf) - 32) / 1.8)
			future_conds = wdata.find('weather/forecast_conditions/condition').get('data')
			future_conds = conds.replace('Snow Showers', '\xe2\x98\x83')
			future_conds = conds.replace('Snow', '\xe2\x98\x83') # Fix snow description
			weather = u"%s. Currently: %sF/%sC, %s.	%s: %sF/%sC, %s" % (city, tempf, tempc, conds, future_day, future_highf, future_highc, future_conds)
			yield weather
		except:
			pass

@command("translate", aliases=('trans', 'googletrans', 'googletranslate'), doc="Translate a phrase using Google Translate. First argument should be the language[s]. It is a 2 letter abbreviation. It will auto detect the orig lang if you only give one; or two languages joined by a |, for example 'en|de' to trans from English to German. Follow this by the phrase you want to translate.")
def translate(client, event, channel, nick, rest):
	rest = rest.strip()
	langpair, meh, rest = rest.partition(' ')
	if '|' not in langpair:
		langpair = '|' + langpair
	BASE_URL = 'http://ajax.googleapis.com/ajax/services/language/translate?v=1.0&format=text&'
	url = BASE_URL + urllib.urlencode({'q' : rest, 'langpair' : langpair})
	raw_res = urllib.urlopen(url).read()
	results = json.loads(raw_res)
	translation = results['responseData']['translatedText']
	return translation


@command("boo", aliases=("b"), doc="Boo someone")
def boo(client, event, channel, nick, rest):
	slapee = rest
	karmaChange(botbase.logger.db, slapee, -1)
	return "/me BOOO %s!!! BOOO!!!" % slapee
		
@command("troutslap", aliases=("slap", "ts"), doc="Slap some(one|thing) with a fish")
def troutslap(client, event, channel, nick, rest):
	slapee = rest
	karmaChange(botbase.logger.db, slapee, -1)
	return "/me slaps %s around a bit with a large trout" % slapee

@command("keelhaul", aliases=("kh",), doc="Inflict great pain and embarassment on some(one|thing)")
def keelhaul(client, event, channel, nick, rest):
	keelee = rest
	karmaChange(botbase.logger.db, keelee, -1)
	return "/me straps %s to a dirty rope, tosses 'em overboard and pulls with great speed. Yarrr!" % keelee

@command("annoy", aliases=("a",), doc="Annoy everyone with meaningless banter")
def annoy(client, event, channel, nick, rest):
	def a1():
		yield 'OOOOOOOHHH, WHAT DO YOU DO WITH A DRUNKEN SAILOR'
		yield 'WHAT DO YOU DO WITH A DRUNKEN SAILOR'
		yield "WHAT DO YOU DO WITH A DRUNKEN SAILOR, EARLY IN THE MORNIN'?"
	def a2():
		yield "I'M HENRY THE EIGHTH I AM"
		yield "HENRY THE EIGHTH I AM I AM"
		yield "I GOT MARRIED TO THE GIRL NEXT DOOR; SHE'S BEEN MARRIED SEVEN TIMES BEFORE"
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
		yield "My Tallest! My Tallest! Hey! Hey My Tallest! My Tallest? My Tallest! Hey! Hey! Hey! My Taaaaaaallist! My Tallest? My Tallest! Hey! Hey My Tallest! My Tallest? It's me! My Tallest? My Tallest!"
	return random.choice([a1, a2, a3, a4, a5, a6])()

@command("dance", aliases=("d",), doc="Do a little dance")
def dance(client, event, channel, nick, rest):
	yield 'O-\-<'
	yield 'O-|-<'
	yield 'O-/-<'

@command("panic", aliases=("pc",), doc="Panic!")
def panic(client, event, channel, nick, rest):
	yield 'O-|-<'
	yield 'O-<-<'
	yield 'O->-<'
	yield 'AAAAAAAHHHH!!!  HEAD FOR THE HILLS!'

@command("rubberstamp",  aliases=('approve',), doc="Approve something")
def rubberstamp(client, event, channel, nick, rest):
	parts = ["Bad credit? No credit? Slow credit?"]
	rest = rest.strip()
	if rest:
		parts.append("%s is" % rest)
		karmaChange(botbase.logger.db, rest, 1)
	parts.append("APPROVED!")
	return " ".join(parts)

@command("cheer", aliases=("c",), doc="Cheer for something")
def cheer(client, event, channel, nick, rest):
	if rest:
		karmaChange(botbase.logger.db, rest, 1)
		return "/me cheers for %s!" % rest
	karmaChange(botbase.logger.db, 'the day', 1)
	return "/me cheers!"

@command("golfclap", aliases=("clap",), doc="Clap for something")
def golfclap(client, event, channel, nick, rest):
	clapv = random.choice(clapvl)
	adv = random.choice(advl)
	adj = random.choice(adjl)
	if rest:
		clapee = rest.strip()
		karmaChange(botbase.logger.db, clapee, 1)
		return "/me claps %s for %s, %s %s." % (clapv, rest, adv, adj)
	return "/me claps %s, %s %s." % (clapv, adv, adj)

@command('featurecreep', aliases=('fc',), doc='Generate feature creep (P+C http://www.dack.com/web/bullshit.html)')
def featurecreep(client, event, channel, nick, rest):
	verb = random.choice(fcverbs).capitalize()
	adjective = random.choice(fcadjectives)
	noun = random.choice(fcnouns)
	return '%s %s %s!' % (verb, adjective, noun)

@command('job', aliases=('card',), doc='Generate a job title, http://www.cubefigures.com/job.html')
def job(client, event, channel, nick, rest):
	j1 = random.choice(jobs1)
	j2 = random.choice(jobs2)
	j3 = random.choice(jobs3)
	return '%s %s %s' % (j1, j2, j3)

@command('hire', doc="When all else fails, pmxbot delivers the perfect employee.")
def hire(client, event, channel, nick, rest):
	title = job(client, event, channel, nick, rest)
	task = featurecreep(client, event, channel, nick, rest)
	return "/me finds a new %s to %s" % (title, task.lower())

@command('oregontrail', aliases=('otrail',), doc='It\'s edutainment!')
def oregontrail(client, event, channel, nick, rest):
	rest = rest.strip()
	if rest:
		who = rest.strip()
	else:
		who = random.choice([nick, channel, 'pmxbot'])
	action = random.choice(otrail_actions)
	if action in ('has', 'has died from'):
		issue = random.choice(otrail_issues)
		text = '%s %s %s.' % (who, action, issue)
	else:
		text = '%s %s' % (who, action)
	return text

#popquotes
@command('bender', aliases=('bend',), doc='Quote Bender, a la http://en.wikiquote.org/wiki/Futurama')
def bender(client, event, channel, nick, rest):
	qt = bartletts(popular_quote_db, 'bender', nick, rest)
	if qt:	return qt

@command('zoidberg', aliases=('zoid',), doc='Quote Zoidberg, a la http://en.wikiquote.org/wiki/Futurama')
def zoidberg(client, event, channel, nick, rest):
	qt = bartletts(popular_quote_db, 'zoid', nick, rest)
	if qt:	return qt

@command('simpsons', aliases=('simp',), doc='Quote the Simpsons, a la http://snpp.com/')
def simpsons(client, event, channel, nick, rest):
	qt = bartletts(popular_quote_db, 'simpsons', nick, rest)
	if qt:	return qt

@command('hal', aliases=('2001',), doc='HAL 9000')
def hal(client, event, channel, nick, rest):
	qt = bartletts(popular_quote_db, 'hal', nick, rest)
	if qt:	return qt

@command('grail', aliases=(), doc='I'' questing baby')
def grail(client, event, channel, nick, rest):
	qt = bartletts(popular_quote_db, 'grail', nick, rest)
	if qt:	return qt

@command('anchorman', aliases=(), doc='Quote Anchorman.')
def anchorman(client, event, channel, nick, rest):
	qt = bartletts(popular_quote_db, 'anchorman', nick, rest)
	if qt:	return qt

#Added quotes
@command('quote', aliases=('q',), doc='If passed with nothing then get a random quote. If passed with some string then search for that. If prepended with "add:" then add it to the db, eg "!quote add: drivers: I only work here because of pmxbot!"')
def quote(client, event, channel, nick, rest):
	qs = Quotes(botbase.logger.db, 'pmx')
	rest = rest.strip()
	if rest.startswith('add: ') or rest.startswith('add '):
		quoteToAdd = rest.split(' ', 1)[1]
		qs.quoteAdd(quoteToAdd)
		qt = False
		return 'Quote added!'
	else:
		qt, i, n = qs.quoteLookupWNum(rest)
		if qt:
			return '(%s/%s): %s' % (i, n, qt)

@command('zinger', aliases=('zing',), doc='ZING!')
def zinger(client, event, channel, nick, rest):
	name = 'you'
	if rest:
		name = rest.strip()
		karmaChange(botbase.logger.db, name, -1)
	#qt = bartletts(botbase.logger.db, 'simpsons', nick, 'pardon my zinger')
	#if qt:	return qt
	return "OH MAN!!! %s TOTALLY GOT ZING'D!" % (name.upper())

@command("motivate", aliases=("m", "appreciate", "thanks", "thank"), doc="Motivate someone")
def motivate(client, event, channel, nick, rest):
	if rest:
		r = rest.strip()
		karmaChange(botbase.logger.db, r, 1)
	else:
		r = channel
	return "you're doing good work, %s!" % r

@command("imotivate", aliases=("im", 'ironicmotivate',), doc='''Ironically "Motivate" someone''')
def imotivate(client, event, channel, nick, rest):
	if rest:
		r = rest.strip()
		karmaChange(botbase.logger.db, r, -1)
	else:
		r = channel
	return '''you're "doing" "good" "work", %s!''' % r

@command("demotivate", aliases=("dm",), doc="Demotivate someone")
def demotivate(client, event, channel, nick, rest):
	if rest:
		r = rest.strip()
		karmaChange(botbase.logger.db, r, -1)
	else:
		r = channel
	return "you're doing horrible work, %s!" % r

@command("8ball", aliases=("8",), doc="Ask the magic 8ball a question")
def eball(client, event, channel, nick, rest):
	return wchoice(ball8_opts)

@command("klingon", aliases=('klingonism',), doc="Ask the magic klingon a question")
def klingon(client, event, channel, nick, rest):
	return random.choice(klingonisms)

@command("roll", aliases=(), doc="Roll a die, default = 100.")
def roll(client, event, channel, nick, rest):
	if rest:
		rest = rest.strip()
		die = int(rest)
	else:
		die = 100
	myroll = random.randint(1, die)
	return "%s rolls %s" % (nick, myroll)
		
@command("flip", aliases=(), doc="Flip a coin")
def flip(client, event, channel, nick, rest):
	myflip = random.choice(('Heads', 'Tails'))
	return "%s gets %s" % (nick, myflip)

@command("deal", aliases=(), doc="Deal or No Deal?")
def deal(client, event, channel, nick, rest):
	mydeal = random.choice(('Deal!', 'No Deal!'))
	return "%s gets %s" % (nick, mydeal)

@command("ticker", aliases=("t",), doc="Look up a ticker symbol's current trading value")
def ticker(client, event, channel, nick, rest):
	ticker = rest.upper()
	# let's use Yahoo's nifty csv facility, and pull last time/price both
	stockInfo = csv.reader(urllib.urlopen('http://finance.yahoo.com/d/quotes.csv?s=%s&f=sl' % ticker))
	lastTrade = stockInfo.next() 
	if lastTrade[2] == 'N/A':
		return "d'oh... could not find information for symbol %s" % ticker
	else:
		change = str(round((float(lastTrade[4]) / (float(lastTrade[1]) - float(lastTrade[4]))) * 100, 1))
		return '%s at %s (ET): %s (%s%%)' % (ticker, lastTrade[3], lastTrade[1], change) 

@command("pick", aliases=("p", 'p:', "pick:"), doc="Pick between a few options")
def pick(client, event, channel, nick, rest):
	question = rest.strip()
	choices = splitem(question)
	if len(choices) == 1:
		return "I can't pick if you give me only one choice!"
	else:
		pick = random.choice(choices)
		certainty = random.sample(certainty_opts, 1)[0]
		return "%s... %s %s" % (pick, certainty, pick)

@command("lunch", aliases=("lunchpick", "lunchpicker"), doc="Pick where to go to lunch")
def lunch(client, event, channel, nick, rest):
	rs = rest.strip()
	if not rs:
		return "Give me an area and I'll pick a place: (%s)" % (', '.join(list(config.lunch_choices)))
	if rs not in config.lunch_choices:
		return "I didn't recognize that area; here's what i have: (%s)" % (', '.join(list(config.lunch_choices)))
	choices = config.lunch_choices[rs]
	return random.choice(choices)

@command("password", aliases=("pw", "passwd",), doc="Generate a random password, similar to http://www.pctools.com/guides/password")
def password(client, event, channel, nick, rest):
	chars = '32547698ACBEDGFHKJMNQPSRUTWVYXZacbedgfhkjmnqpsrutwvyxz'
	passwd = []
	for i in range(8):
		passwd.append(random.choice(chars))
	return ''.join(passwd)

@command("insult", aliases=(), doc="Generate a random insult from http://www.webinsult.com/index.php")
def insult(client, event, channel, nick, rest):
	instype = random.randrange(4)
	insurl = "http://www.webinsult.com/index.php?style=%s&r=0&sc=1" % instype
	insre = re.compile('<div class="insult" id="insult">(.*?)</div>')
	html = get_html(insurl)
	insult = insre.search(html).group(1)
	if insult:
		if rest:
			insultee = rest.strip()
			karmaChange(botbase.logger.db, insultee, -1)
			if instype in (0, 2):
				cinsre = re.compile(r'\b(your)\b', re.IGNORECASE)
				insult = cinsre.sub("%s's" % insultee, insult)
			elif instype in (1, 3):
				cinsre = re.compile(r'^([TY])')
				insult = cinsre.sub(lambda m: "%s, %s" % (insultee, m.group(1).lower()), insult)
		return insult

@command("compliment", aliases=('surreal',), doc="Generate a random compliment from http://www.madsci.org/cgi-bin/cgiwrap/~lynn/jardin/SCG")
def compliment(client, event, channel, nick, rest):
	compurl = 'http://www.madsci.org/cgi-bin/cgiwrap/~lynn/jardin/SCG'
	comphtml = ''.join([i for i in urllib.urlopen(compurl)])
	compmark1 = '<h2>\n\n'
	compmark2 = '\n</h2>'
	compliment = comphtml[comphtml.find(compmark1) + len(compmark1):comphtml.find(compmark2)]
	if compliment:
		compliment = re.compile(r'\n').sub('%s' % ' ', compliment)
		compliment = re.compile(r'  ').sub('%s' % ' ', compliment)
		if rest:
			complimentee = rest.strip()
			karmaChange(botbase.logger.db, complimentee, 1)
			compliment = re.compile(r'\b(your)\b', re.IGNORECASE).sub('%s\'s' % complimentee, compliment)
			compliment = re.compile(r'\b(you are)\b', re.IGNORECASE).sub('%s is' % complimentee, compliment)
			compliment = re.compile(r'\b(you have)\b', re.IGNORECASE).sub('%s has' % complimentee, compliment)
		return compliment
 

@command("karma", aliases=("k",), doc="Return or change the karma value for some(one|thing)")
def karma(client, event, channel, nick, rest):
	karmee = rest.strip('++').strip('--').strip('~~')
	if '++' in rest: 
		karmaChange(botbase.logger.db, karmee, 1)
	elif '--' in rest: 
		karmaChange(botbase.logger.db, karmee, -1)
	elif '~~' in rest:
		change = random.choice([-1, 0, 1])
		karmaChange(botbase.logger.db, karmee, change)
		if change == 1:
			return "%s karma++" % karmee
		elif change == 0:
			return "%s karma shall remain the same" % karmee
		elif change == -1:
			return "%s karma--" % karmee
	elif '==' in rest:
		t1, t2 = rest.split('==')
		karmaLink(botbase.logger.db, t1, t2)
		score = karmaLookup(botbase.logger.db, t1)
		return "%s and %s are now linked and have a score of %s" % (t1, t2, score)
	else:
		karmee = rest or nick
		score = karmaLookup(botbase.logger.db, karmee)
		return "%s has %s karmas" % (karmee, score)

@command("top10", aliases=("top",), doc="Return the top n (default 10) highest entities by Karmic value. Use negative numbers for the bottom N.")
def top10(client, event, channel, nick, rest):
	if rest:
		topn = int(rest)
	else:
		topn = 10
	selection = karmaList(botbase.logger.db, topn)
	res = ' '.join('(%s: %s)' % (', '.join(n), k) for n, k in selection)
	return res

@command("bottom10", aliases=("bottom",), doc="Return the bottom n (default 10) lowest entities by Karmic value. Use negative numbers for the bottom N.")
def top10(client, event, channel, nick, rest):
	if rest:
		topn = -int(rest)
	else:
		topn = -10
	selection = karmaList(botbase.logger.db, topn)
	res = ' '.join('(%s: %s)' % (', '.join(n), k) for n, k in selection)
	return res


@command("excuse", aliases=("e ",), doc="Provide a convenient excuse")
def excuse(client, event, channel, nick, rest):
	args = "/".join(rest.split(' ')[:2])
	if args:
		args = "/" + args
		url = 'http://www.dowski.com/excuses/new%s' % args
	else:
		url = 'http://www.dowski.com/excuses/new'
	excuse = get_html(url)
	return excuse

@command("curse", doc="Curse the day!")
def curse(client, event, channel, nick, rest):
	if rest:
		cursee = rest
	else:
		cursee = 'the day'
	karmaChange(botbase.logger.db, cursee, -1)
	return "/me curses %s!" % cursee

@command("tinytear", aliases=('tt', 'tear', 'cry'), doc="I cry a tiny tear for you.")
def tinytear(client, event, channel, nick, rest):
	if rest:
		return "/me sheds a single tear for %s" % rest
	else:
		return "/me sits and cries as a single tear slowly trickles down its cheek"

@command("stab", aliases=("shank", "shiv",),doc="Stab, shank or shiv some(one|thing)!")
def stab(client, event, channel, nick, rest):
	if rest:
		stabee = rest
	else:
		stabee = 'wildly at anything'
	if random.random() < 0.9:
		karmaChange(botbase.logger.db, stabee, -1)
		weapon = random.choice(weapon_opts)
		weaponadj = random.choice(weapon_adjs)
		violentact = random.choice(violent_acts)
		return "/me grabs a %s %s and %s %s!" % (weaponadj, weapon, violentact, stabee)
	elif random.random() < 0.6:
		karmaChange(botbase.logger.db, stabee, -1)
		return "/me is going to become rich and famous after i invent a device that allows you to stab people in the face over the internet"
	else:
		karmaChange(botbase.logger.db, nick, -1)
		return "/me turns on its master and shivs %s. This is reality man, and you never know what you're going to get!" % nick

@command("disembowel", aliases=("dis", "eviscerate"),doc="Disembowel some(one|thing)!")
def disembowel(client, event, channel, nick, rest):
	if rest:
		stabee = rest
		karmaChange(botbase.logger.db, stabee, -1)
	else:
		stabee = "someone nearby"
	return "/me takes %s, brings them down to the basement, ties them to a leaky pipe, and once bored of playing with them mercifully ritually disembowels them..." % stabee

@command("embowel", aliases=("reembowel",), doc="Embowel some(one|thing)!")
def embowel(client, event, channel, nick, rest):
	if rest:
		stabee = rest
		karmaChange(botbase.logger.db, stabee, 1)
	else:
		stabee = "someone nearby"
	return "/me (wearing a bright pink cape and yellow tights) swoops in through an open window, snatches %s, races out of the basement, takes them to the hospital with entrails on ice, and mercifully embowels them, saving the day..." % stabee

@command("chain", aliases=(),doc="Chain some(one|thing)down.")
def chain(client, event, channel, nick, rest):
	if rest:
		chainee = rest
	else:
		chainee = "someone nearby"
	if chainee == 'cperry':
		return "/me ties the chains extra tight around %s" % chainee
	elif random.randint(1,10) != 1:
		return "/me chains %s to the nearest desk.  you ain't going home, buddy." % chainee
	else:
		karmaChange(botbase.logger.db, nick, -1)
		return "/me spins violently around and chains %s to the nearest desk.  your days of chaining people down and stomping on their dreams are over!  get a life, you miserable beast." % nick

@command("bless", doc="Bless the day!")
def bless(client, event, channel, nick, rest):
	if rest:
		blesse = rest
	else:
		blesse = 'the day'
	karmaChange(botbase.logger.db, blesse, 1)
	return "/me blesses %s!" % blesse

@command("blame", doc="Pass the buck!")
def blame(client, event, channel, nick, rest):
	if rest:
		blamee = rest
	else:
		blamee = channel
	karmaChange(botbase.logger.db, nick, -1)
	if random.randint(1,10) == 1:
		yield "/me jumps atop the chair and points back at %s." % nick
		yield "stop blaming the world for your problems, you bitter, two-faced sissified monkey!"
	else:
		yield "I blame %s for everything!  it's your fault!  it's all your fault!!" % blamee
		yield "/me cries and weeps in despair"

@contains('pmxbot')
def rand_bot(client, event, channel, nick, rest):
	if (channel == config.inane_channel and random.random() < .2):
		normal_functions = [featurecreep, insult, motivate, compliment, cheer,
			golfclap, excuse, nastygram, curse, bless, job, hire, 
			bakecake, cutcake, oregontrail, chain, tinytear, blame,
			reweight, panic, rubberstamp, dance, annoy, klingon, 
			storytime, murphy]
		quote_functions = [quote, falconer, gir, zim, zoidberg, simpsons, bender, hal, grail]
		ftype = random.choice('n'*len(normal_functions) + 'q'*len(quote_functions))
		if ftype == 'n':
			func = random.choice(normal_functions)
			res = func(client, event, channel, 'pmxbot', nick)
		elif ftype == 'q':
			func = random.choice(quote_functions)
			res = func(client, event, channel, 'pmxbot', '')
		return res
		
@contains("sqlonrails")
def yay_sor(client, event, channel, nick, rest):
	karmaChange(botbase.logger.db, 'sql on rails', 1)
	return "Only 76,417 lines..."

@contains("sql on rails")
def other_sor(*args):
	return yay_sor(*args)

calc_exp = re.compile("^[0-9 \*/\-\+\)\(\.]+$")
@command("calc", doc="Perform a basic calculation")
def calc(client, event, channel, nick, rest):
	mo = calc_exp.match(rest)
	if mo:
		try:
			return str(eval(rest))
		except:
			return "eval failed... check your syntax"
	else:
		return "misformatted arithmetic!"

@command("define", aliases=("def",), doc="Define a word")
def defit(client, event, channel, nick, rest):
	word = rest.strip()
	res = lookup(word)
	if res is None:
		return "Arg!  I didn't find a definition for that."
	else:
		return 'Wikipedia says: ' + res


@command("acronym", aliases=("ac",), doc="Look up an acronym")
def acit(client, event, channel, nick, rest):
	word = rest.strip()
	res = lookup_acronym(word)
	if res is None:
		return "Arg!  I couldn't expand that..."
	else:
		return ' | '.join(res)

@command("fight", doc="Pit two sworn enemies against each other")
def fight(client, event, channel, nick, rest):
	if rest:
		vtype = random.choice(fight_victories)
		fdesc = random.choice(fight_descriptions)
		bad_protocol = False
		if 'vs.' not in rest:
			bad_protocol = True
		contenders = [c.strip() for c in rest.split('vs.')]
		if len(contenders) > 2:
			bad_protocol = True
		if bad_protocol:
			karmaChange(botbase.logger.db, nick.lower(), -1)
			args = (vtype, nick, fdesc)
			return "/me %s %s in %s for bad protocol." % args
		random.shuffle(contenders)
		winner,loser = contenders
		karmaChange(botbase.logger.db, winner, 1)
		karmaChange(botbase.logger.db, loser, -1)
		return "%s %s %s in %s." % (winner, vtype, loser, fdesc)

@command("progress", doc="Display the progress of something: start|end|percent")
def progress(client, event, channel, nick, rest):
	if rest:
		left, right, amount = [piece.strip() for piece in rest.split('|')]
		ticks = min(int(round(float(amount) / 10)), 10)
		bar = "=" * ticks
		return "%s [%-10s] %s" % (left, bar, right) 

@command("nastygram", aliases=('nerf', 'passive', 'bcc'), doc="A random passive-agressive comment, optionally directed toward some(one|thing).")
def nastygram(client, event, channel, nick, rest):
	recipient = ""
	if rest:
		recipient = rest.strip()
		karmaChange(botbase.logger.db, recipient, -1)
	return passagg(recipient, nick.lower())

@command("therethere", aliases=('poor', 'comfort'), doc="Sympathy for you.")
def therethere(client, event, channel, nick, rest):
	if rest:
		karmaChange(botbase.logger.db, rest, 1)
		return "There there %s... There there." % rest
	else:
		return "/me shares its sympathy."

@command("saysomething", aliases=(), doc="Generate a Markov Chain response based on past logs. Seed it with a starting word by adding that to the end, eg '!saysomething dowski:'")
def saysomething(client, event, channel, nick, rest):
	sayer.startup(botbase.logger.db)
	if rest:
		return sayer.saysomething(rest)
	else:	
		return sayer.saysomething()

@command("tgif", doc="Thanks for the words of wisdow, Mike.")
def tgif(client, event, channel, nick, rest):
	return "Hey, it's Friday! Only two more days left in the work week!"

@command("fml", aliases=(), doc="A SFW version of fml.")
def fml(client, event, channel, nick, rest):
	return "indeed"

@command("storytime", aliases=('story',), doc="A story is about to be told.")
def storytime(client, event, channel, nick, rest):
	if rest:
		return "Come everyone, gather around the fire. %s is about to tell us a story!" % rest.strip()
	else:
		return "Come everyone, gather around the fire. A story is about to be told!"

@command("murphy", aliases=('law',), doc="Look up one of Murphy's laws")
def murphy(client, event, channel, nick, rest):
	return random.choice(murphys_laws)

@command("meaculpa", aliases=('apology', 'apologize',), doc="Sincerely apologize")
def meaculpa(client, event, channel, nick, rest):
	if rest:
		rest = rest.strip()

	if rest:
		return random.choice(direct_apologies) % dict(a=nick, b=rest)
	else:
		return random.choice(apologies) % dict(a=nick)


#Below is system junk
@command("help", aliases=('h',), doc="Help (this command)")
def help(client, event, channel, nick, rest):
	rs = rest.strip()
	if rs:
		for typ, name, f, doc in _handler_registry:
			if name == rs:
				yield '!%s: %s' % (name, doc)
				break
		else:
			yield "command not found"
	else:
		def mk_entries():
			for typ, name, f, doc in sorted(_handler_registry, key=lambda x: x[1]):
				if typ == 'command':
					aliases = sorted([x[1] for x in _handler_registry if x[0] == 'alias' and x[2] == f])
					res =  "!%s" % name
					if aliases:
						res += " (%s)" % ', '.join(aliases)
					yield res
		o = StringIO("|".join(mk_entries()))
		more = o.read(160)
		while more:
			yield more
			time.sleep(0.3)
			more = o.read(160)

@command("ctlaltdel", aliases=('controlaltdelete', 'controlaltdelete', 'cad', 'restart', 'quit',), doc="Quits pmxbot. Daemontools should automatically restart it.")
def ctlaltdel(client, event, channel, nick, rest):
	if 'real' in rest.lower():
		sys.exit()
	else:
		return "Really?"

@command("hgup", aliases=('hg', 'update', 'hgpull'), doc="Update with the latest from mercurial")
def svnup(client, event, channel, nick, rest):
	svnres = os.popen('hg pull -u')
	svnres = svnres.read()
	svnres = svnres.splitlines()
	return svnres

@command("strike", aliases=(), doc="Strike last <n> statements from the record")
def strike(client, event, channel, nick, rest):
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
		struck = botbase.logger.strike(channel, nick, count)
		yield ("Isn't undo great?  Last %d statement%s by %s were stricken from the record." %
		(struck, 's' if struck > 1 else '', nick))
	except:
		yield "Hmm.. I didn't find anything of yours to strike!"

@command("where", aliases=('last', 'seen', 'lastseen'), doc="When did pmxbot last see <nick> speak?")
def where(client, event, channel, nick, rest):
	onick = rest.strip()
	last = botbase.logger.last_seen(onick)
	if last:
		tm, chan = last
		return "I last saw %s speak at %s in channel #%s" % (
		onick, tm, chan)
	else:
		return "Sorry!  I don't have any record of %s speaking" % onick


global config

def run():
	global config
	import sys, yaml
	if len(sys.argv) < 2:
		sys.stderr.write("error: need config file as first argument")
		raise SystemExit(1)
	
	config_file = sys.argv[1]
	class O(object): 
		def __init__(self, d):
			for k, v in d.iteritems(): setattr(self, k, v)
			
	config = O(yaml.load(open(config_file)))

	@contains(config.bot_nickname)
	def rand_bot2(*args):
		return rand_bot(*args)

	bot = LoggingCommandBot(config.database_dir, config.server_host, config.server_port, 
		config.bot_nickname, config.log_channels, config.other_channels,
		config.feed_interval*60, config.feeds)
	bot.start()

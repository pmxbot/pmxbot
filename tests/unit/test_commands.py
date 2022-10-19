import re
import os
import string
import uuid
import urllib.error

import pytest
import requests

import pmxbot.dictlib
import pmxbot.storage
from pmxbot import core
from pmxbot import logging
from pmxbot import commands
from pmxbot import karma
from pmxbot import quotes
from pmxbot import system


def logical_xor(a, b):
    return bool(a) ^ bool(b)


def onetrue(*args):
    truthiness = list(filter(bool, args))
    return len(truthiness) == 1


@pytest.fixture
def google_api_key(monkeypatch):
    key = os.environ.get('GOOGLE_API_KEY')
    if not key:
        pytest.skip("Need GOOGLE_API_KEY environment variable")
    monkeypatch.setitem(pmxbot.config, 'Google API key', key)


class TestCommands:
    @classmethod
    def setup_class(cls):
        path = os.path.dirname(os.path.abspath(__file__))
        configfile = os.path.join(path, 'testconf.yaml')
        config = pmxbot.dictlib.ConfigDict.from_yaml(configfile)
        cls.bot = core.initialize(config)
        logging.Logger.store.message("logged", "testrunner", "some text")

    @classmethod
    def teardown_class(cls):
        pmxbot.storage.SelectableStorage.finalize()
        path = os.path.dirname(os.path.abspath(__file__))
        os.remove(os.path.join(path, 'pmxbot.sqlite'))

    def test_google(self, google_api_key, needs_internet):
        """
        Basic google search for "pmxbot". Result must contain a link.
        """
        res = commands.google("pmxbot")
        print(res)
        assert "http" in res

    def test_boo(self):
        """
        Test "boo foo"
        """
        subject = "foo"
        pre = karma.Karma.store.lookup(subject)
        res = commands.boo(subject)
        assert res == "/me BOOO %s!!! BOOO!!!" % subject
        post = karma.Karma.store.lookup(subject)
        assert post == pre - 1

    def test_troutslap(self):
        """
        Test "troutslap foo"
        """
        subject = "foo"
        pre = karma.Karma.store.lookup(subject)
        res = commands.troutslap(subject)
        assert res == "/me slaps %s around a bit with a large trout" % subject
        post = karma.Karma.store.lookup(subject)
        assert post == pre - 1

    def test_keelhaul(self):
        """
        Test "keelhaul foo"
        """
        subject = "foo"
        pre = karma.Karma.store.lookup(subject)
        res = commands.keelhaul(subject)
        assert res == (
            "/me straps %s to a dirty rope, tosses 'em overboard and "
            "pulls with great speed. Yarrr!" % subject
        )
        post = karma.Karma.store.lookup(subject)
        assert post == pre - 1

    def test_motivate(self):
        """
        Test that motivate actually works.
        """
        subject = "foo"
        pre = karma.Karma.store.lookup(subject)
        res = commands.motivate(channel="#test", rest=subject)
        assert res == "you're doing good work, %s!" % subject
        post = karma.Karma.store.lookup(subject)
        assert post == pre + 1

    def test_motivate_with_reason(self):
        """
        Test that motivate ignores the reason
        """
        subject = "foo"
        pre = karma.Karma.store.lookup(subject)
        res = commands.motivate(
            channel="#test", rest=" %s\tfor some really incredible reason" % subject
        )
        assert res == "you're doing good work, %s!" % subject
        post = karma.Karma.store.lookup(subject)
        assert post == pre + 1

    def test_motivate_with_spaces(self):
        """
        Test that motivate strips beginning and ending whitespace
        """
        subject = "foo"
        pre = karma.Karma.store.lookup(subject)
        res = commands.motivate(channel="#test", rest="   %s \t  " % subject)
        assert res == "you're doing good work, %s!" % subject
        post = karma.Karma.store.lookup(subject)
        assert post == pre + 1

    def test_demotivate(self):
        """
        Test that demotivate actually works.
        """
        subject = "foo"
        pre = karma.Karma.store.lookup(subject)
        res = commands.demotivate(rest=subject, channel="#test")
        assert res == "you're doing horrible work, %s!" % subject
        post = karma.Karma.store.lookup(subject)
        assert post == pre - 1

    def test_imotivate(self):
        """
        Test that ironic/sarcastic motivate actually works.
        """
        subject = "foo"
        pre = karma.Karma.store.lookup(subject)
        res = commands.imotivate(rest=subject, channel="#test")
        assert res == """you're "doing" "good" "work", %s!""" % subject
        post = karma.Karma.store.lookup(subject)
        assert post == pre - 1

    def test_add_quote(self):
        """
        Try adding a quote
        """
        quote = "And then she said %s" % str(uuid.uuid4())
        res = quotes.quote("add %s" % quote)
        assert res == "Quote added!"
        cursor = logging.Logger.store.db.cursor()
        cursor.execute(
            "select count(*) from quotes where library = 'pmx' and quote = ?", (quote,)
        )
        numquotes = cursor.fetchone()[0]
        assert numquotes == 1

    def test_add_and_retreive_quote(self):
        """
        Try adding a quote, then retrieving it
        """
        id = str(uuid.uuid4())
        quote = "So I says to Mabel, I says, %s" % id
        res = quotes.quote("add %s" % quote)
        assert res == "Quote added!"
        cursor = logging.Logger.store.db.cursor()
        cursor.execute(
            "select count(*) from quotes where library = 'pmx' and quote = ?", (quote,)
        )
        numquotes = cursor.fetchone()[0]
        assert numquotes == 1

        res = quotes.quote(id)
        assert res == "(1/1): %s" % quote

    def test_roll(self):
        """
        Roll a die, both with no arguments and with some numbers
        """
        res = int(commands.roll(nick="testrunner", rest="").split()[-1])
        assert res >= 0 and res <= 100
        n = 6668

        res = commands.roll(rest="%s" % n, nick="testrunner").split()[-1]
        res = int(res)
        assert res >= 0 and res <= n

    @staticmethod
    def ticker_pattern(symbol):
        return (
            "^"
            + re.escape(symbol)
            + (
                r" at \d{1,2}:\d{2}(?:am|pm) \([A-z]{1,3}\): "
                r"\d{1,4}.\d{1,4} \([+-]\d{1,3}.\d{1,4}%\)$"
            )
        )

    @pytest.mark.xfail(reason="#71")
    def test_ticker_goog(self, needs_internet):
        """
        Get the current stock price of Google.

        GOOG at 4:00pm (ET): 484.81 (+1.5%)
        """
        res = commands.ticker("goog")
        print(res)
        assert re.match(self.ticker_pattern('GOOG'), res), res

    @pytest.mark.xfail(reason="#71")
    def test_ticker_yougov(self, needs_internet):
        """
        Get the current stock price of YouGov.

        YOU.L at 10:37am (ET): 39.40 (0.4%)
        """
        res = commands.ticker("you.l")
        print(res)
        assert re.match(self.ticker_pattern('YOU.L'), res), res

    @pytest.mark.xfail(reason="#71")
    def test_ticker_nasdaq(self, needs_internet):
        """
        Get the current stock price of the NASDAQ.

        ^IXIC at 10:37am (ET): 3403.247 (0.0%)
        """
        res = commands.ticker("^ixic")
        print(res)
        assert re.match(self.ticker_pattern('^IXIC'), res), res

    def test_pick_or(self):
        """
        Test the pick command with a simple or expression
        """
        res = commands.pick("fire or acid")
        assert logical_xor("fire" in res, "acid" in res)
        assert " or " not in res

    def test_pick_or_intro(self):
        """
        Test the pick command with an intro and a simple "or" expression
        """
        res = commands.pick("how would you like to die, pmxbot: fire or acid")
        assert logical_xor("fire" in res, "acid" in res)
        assert "die" not in res and "pmxbot" not in res and " or " not in res

    def test_pick_comma(self):
        """
        Test the pick command with two options separated by commas
        """
        res = commands.pick("fire, acid")
        assert logical_xor("fire" in res, "acid" in res)

    def test_pick_comma_intro(self):
        """
        Test the pick command with an intro followed by two options separted
        by commas
        """
        res = commands.pick("how would you like to die, pmxbot: fire, acid")
        assert logical_xor("fire" in res, "acid" in res)
        assert "die" not in res and "pmxbot" not in res

    def test_pick_comma_or_intro(self):
        """
        Test the pick command with an intro followed by options with commas
        and ors
        """
        msg = "how would you like to die, pmxbot: gun, fire, acid or defenestration"
        res = commands.pick(msg)
        assert onetrue(
            "gun" in res, "fire" in res, "acid" in res, "defenestration" in res
        )
        assert "die" not in res and "pmxbot" not in res and " or " not in res

    def test_lunch(self):
        """
        Test that the lunch command selects one of the list options
        """
        res = commands.lunch("PA")
        assert res in [
            "Pasta?",
            "Thaiphoon",
            "Pluto's",
            "Penninsula Creamery",
            "Kan Zeman",
        ]

    def test_karma_check_self_blank(self):
        """
        Determine your own, blank, karma.
        """
        id = str(uuid.uuid4())[:15]
        res = karma.karma(nick=id, rest="")
        assert re.match(r"^%s has 0 karmas$" % id, res)

    def test_karma_check_other_blank(self):
        """
        Determine some else's blank/new karma.
        """
        id = str(uuid.uuid4())
        res = karma.karma(nick="testrunner", rest=id)
        assert re.match("^%s has 0 karmas$" % id, res)

    def test_karma_set_and_check(self):
        """
        Take a new entity, give it some karma, check that it has more
        """
        id = str(uuid.uuid4())
        res = karma.karma(nick="testrunner", rest=id)
        assert re.match("^%s has 0 karmas$" % id, res)
        res = karma.karma(nick="testrunner", rest="%s++" % id)
        res = karma.karma(nick="testrunner", rest="%s++" % id)
        res = karma.karma(nick="testrunner", rest="%s++" % id)
        res = karma.karma(nick="testrunner", rest="%s--" % id)
        res = karma.karma(nick="testrunner", rest=id)
        assert re.match(r"^%s has 2 karmas$" % id, res)

    def test_karma_set_and_check_with_space(self):
        """
        Take a new entity that has a space in it's name, give it some karma,
        check that it has more
        """
        id = str(uuid.uuid4()).replace("-", " ")
        res = karma.karma(nick="testrunner", rest=id)
        assert re.match("^%s has 0 karmas$" % id, res)
        res = karma.karma(nick="testrunner", rest="%s++" % id)
        res = karma.karma(nick="testrunner", rest="%s++" % id)
        res = karma.karma(nick="testrunner", rest="%s++" % id)
        res = karma.karma(nick="testrunner", rest="%s--" % id)
        res = karma.karma(nick="testrunner", rest=id)
        assert re.match(r"^%s has 2 karmas$" % id, res)

    def test_karma_randomchange(self):
        """
        Take a new entity that has a space in it's name, give it some karma,
        check that it has more
        """
        id = str(uuid.uuid4())
        flags = {}
        i = 0
        karmafetch = re.compile(r"^%s has (\-?\d+) karmas$" % id)
        while len(flags) < 3 and i <= 30:
            res = karma.karma(nick="testrunner", rest=id)
            prekarma = int(karmafetch.findall(res)[0])
            change = karma.karma(nick="testrunner", rest="%s~~" % id)
            assert change in [
                "%s karma++" % id,
                "%s karma--" % id,
                "%s karma shall remain the same" % id,
            ]
            if change.endswith('karma++'):
                flags['++'] = True
                res = karma.karma(nick="testrunner", rest=id)
                postkarma = int(karmafetch.findall(res)[0])
                assert postkarma == prekarma + 1
            elif change.endswith('karma--'):
                flags['--'] = True
                res = karma.karma(nick="testrunner", rest=id)
                postkarma = int(karmafetch.findall(res)[0])
                assert postkarma == prekarma - 1
            elif change.endswith('karma shall remain the same'):
                flags['same'] = True
                res = karma.karma(nick="testrunner", rest=id)
                postkarma = int(karmafetch.findall(res)[0])
                assert postkarma == prekarma
            i += 1
        assert len(flags) == 3
        assert i < 30

    def test_calc_simple(self):
        """
        Test the built-in python calculator with a simple expression - 2+2
        """
        res = commands.calc("2+2")
        print(res)
        assert res == "4"

    def test_calc_complex(self):
        """
        Test the built-in python calculator with a more complicated formula
        ((((781**2)*5)/92835.3)+4)**0.5
        """
        res = commands.calc("((((781**2)*5)/92835.3)+4)**0.5")
        print(res)
        assert res.startswith("6.070566")

    def test_insult(self, needs_internet):
        commands.insult("")

    def test_targeted_insult(self, needs_internet):
        commands.insult("enemy")

    @pytest.mark.xfail(reason="#94")
    def test_define_keyboard(self, needs_wordnik):
        """
        Test the dictionary with the word keyboard.
        """
        res = commands.define("keyboard")
        assert isinstance(res, str)
        assert res == (
            "Wordnik says: A panel of buttons used for typing and performing "
            "other functions on a computer or typewriter."
        )

    @pytest.mark.xfail(reason="#94")
    def test_define_irc(self, needs_wordnik):
        """
        Test the dictionary with the word IRC.
        """
        res = commands.define("  IRC \t")
        assert isinstance(res, str)
        assert res == (
            "Wordnik says: An international computer network of "
            "Internet servers, using its own protocol through which "
            "individual users can hold real-time online conversations."
        )

    def test_define_notaword(self, needs_wordnik):
        """
        Test the dictionary with a nonsense word.
        """
        res = commands.define("notaword")
        assert isinstance(res, str)
        assert res == "Wordnik does not have a definition for that."

    def test_urb_irc(self, needs_internet):
        """
        Test the urban dictionary with the word IRC.
        """
        res = commands.urbandict("irc")
        assert "It's a place where broken and odd people" in res

    def test_acronym_irc(self, needs_internet):
        """
        Test acronym finder with the word IRC.
        """
        res = commands.acit("irc")
        assert "|" in res

    def test_progress(self):
        """
        Test the progress bar
        """
        res = commands.progress("1|98123|30")
        print(res)
        assert res == "1 [===       ] 98123"

    def test_strategy(self):
        """
        Test the social strategy thingie
        """
        res = commands.strategy()
        print(res)
        assert res != ""

    def test_qbiu_person(self):
        """
        Test the qbiu function with a specified person.
        """
        bitcher = "all y'all"
        res = commands.bitchingisuseless('testrunner', bitcher)
        print(res)
        assert res == ("Quiet bitching is useless, all y'all. Do something about it.")

    def test_qbiu_blank(self):
        """
        Test the qbiu function with a specified person.
        """
        res = commands.bitchingisuseless('testrunner', '')
        print(res)
        assert res == ("Quiet bitching is useless, foo'. Do something about it.")

    @pytest.mark.parametrize(["iter"], [[val] for val in range(100)])
    def test_rand_bot(self, iter):
        network_excs = urllib.error.URLError, requests.exceptions.RequestException
        try:
            res = commands.rand_bot('#test', 'testrunner', '')
        except network_excs:
            pytest.check_internet()
            raise
        if res is None:
            return
        if not isinstance(res, str):
            res = ''.join(res)
        assert len(res)

    @pytest.mark.xfail(
        'sys.version_info < (3, 5)', reason="pkg_resources uses NullLoader for pmxbot"
    )
    def test_logo(self):
        lines = list(system.logo())
        assert len(lines)

    def test_help(self):
        help = system.help(rest='')
        result = ''.join(help)
        assert 'help' in result

    def test_help_specific(self):
        lines = system.help(rest='help')
        result = ''.join(lines)
        assert 'help' in result
        assert result == '!help: Help (this command)'

    def test_password(self):
        """
        Test the default password command.

        Result should include at least one ascii character, digit,
        and punctuation character.
        """
        res = commands.password('')
        assert len(res) == 12
        assert any(char in res for char in string.ascii_letters)
        assert any(char in res for char in string.digits)
        assert any(char in res for char in string.punctuation)

    @pytest.mark.parametrize(["length"], [[val] for val in range(4, 100)])
    def test_password_specific(self, length):
        """
        Test the password command (with a length argument >= 4).
        """
        res = commands.password(str(length))
        assert len(res) == int(length)
        assert any(char in res for char in string.ascii_letters)
        assert any(char in res for char in string.digits)
        assert any(char in res for char in string.punctuation)

    @pytest.mark.parametrize(["length"], [[val] for val in range(1, 4)])
    def test_password_specific_short(self, length):
        """
        Test the password command with a length argument < 4.

        With passwords this short we can't guarantee they'll
        contain one of each character set.
        """
        res = commands.password(str(length))
        assert len(res) == int(length)

    def test_password_nonint(self):
        """
        Test the password command with a non-integer argument.
        """
        res = commands.password('test')
        assert res == 'need an integer password length!'

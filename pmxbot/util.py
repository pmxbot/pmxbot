import random
import warnings
import itertools
import logging

import requests
import bs4
import jaraco.functools

try:
    import wordnik.swagger
    import wordnik.WordApi
except (ImportError, SyntaxError):
    warnings.warn("Wordnik failed to import")

import pmxbot.phrases
from . import http


log = logging.getLogger(__name__)


def splitem(query):
    """
    Split a query into choices

    >>> splitem('dog, cat')
    ['dog', 'cat']

    Disregards trailing punctuation.

    >>> splitem('dogs, cats???')
    ['dogs', 'cats']
    >>> splitem('cats!!!')
    ['cats']

    Allow or
    >>> splitem('dogs, cats or prarie dogs?')
    ['dogs', 'cats', 'prarie dogs']

    Honors serial commas
    >>> splitem('dogs, cats, or prarie dogs?')
    ['dogs', 'cats', 'prarie dogs']

    Allow choices to be prefixed by some ignored prompt.
    >>> splitem('stuff: a, b, c')
    ['a', 'b', 'c']
    """
    prompt, sep, query = query.rstrip('?.!').rpartition(':')

    choices = query.split(',')
    choices[-1:] = choices[-1].split(' or ')

    return [choice.strip() for choice in choices if choice.strip()]


def lookup(word):
    """
    Get a definition for a word (uses Wordnik)
    """
    # Jason's key - do not abuse
    key = 'edc4b9b94b341eeae350e087c2e05d2f5a2a9e0478cefc6dc'
    client = wordnik.swagger.ApiClient(key, 'https://api.wordnik.com/v4')
    words = wordnik.WordApi.WordApi(client)
    try:
        definitions = words.getDefinitions(word, limit=1)
        definition = definitions[0]
    except Exception:
        log.exception(f"Unhandled exception looking up {word}.")
        return
    return str(definition.text)


lookup.provider = 'Wordnik'  # type: ignore


def urban_lookup(word):
    """
    Return a Urban Dictionary definition for a word or None if no result was
    found.
    """
    url = "http://api.urbandictionary.com/v0/define"
    params = dict(term=word)
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    res = resp.json()
    if not res['list']:
        return
    return res['list'][0]['definition']


def lookup_acronym(acronym, limit=3):
    acronym = acronym.strip().upper().replace('.', '')
    html = http.open('http://www.acronymfinder.com/%s.html' % acronym).text
    soup = bs4.BeautifulSoup(html, 'html.parser')
    nodes = soup.findAll(name='td', attrs={'class': 'result-list__body__meaning'})
    return [node.text for node in itertools.islice(nodes, limit)]


@jaraco.functools.once
def load_emergency_compliments():
    compurl = (
        'https://spreadsheets.google.com/feeds/list/'
        '1eEa2ra2yHBXVZ_ctH4J15tFSGEu-VTSunsrvaCAV598/od6/public/values'
        '?alt=json'
    )
    doc = http.open(compurl).json()
    return [entry['title']['$t'] for entry in doc['feed']['entry']]


def passagg(recipient, sender):
    """
    Generate a passive-aggressive statement to recipient from sender.
    """
    adj = random.choice(pmxbot.phrases.adjs)
    if random.choice([False, True]):
        # address the recipient last
        lead = ""
        trail = recipient if not recipient else ", %s" % recipient
    else:
        # address the recipient first
        lead = recipient if not recipient else "%s, " % recipient
        trail = ""
    body = random.choice(pmxbot.phrases.adj_intros) % adj
    if not lead:
        body = body.capitalize()
    msg = f"{lead}{body}{trail}."
    fw = random.choice(pmxbot.phrases.farewells)
    return f"{msg} {fw}, {sender}."

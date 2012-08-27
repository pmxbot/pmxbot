"""
Local pmxbot extensions, incude the path to this file in your config.yaml.
"""

import random
import urllib

from pmxbot.core import command, execdelay

@command("yahoolunch", doc="Find a random neary restaurant for lunch using "
    "Yahoo Local. Defaults to 1 mile radius, but append Xmi to the end to "
    "change the radius.")
def lunch(client, event, channel, nick, rest):
    yahooid = "eeGETYOUROWN.yu"
    from yahoo.search.local import LocalSearch
    location = rest.strip()
    if location.endswith('mi'):
        radius, location = ''.join(reversed(location)).split(' ', 1)
        location = ''.join(reversed(location))
        radius = ''.join(reversed(radius))
        radius = float(radius.replace('mi', ''))
    else:
        radius = 1
    srch = LocalSearch(app_id=yahooid, category=96926236, results=20,
        query="lunch", location=location, radius=radius)
    res = srch.parse_results()
    limit = min(250, res.totalResultsAvailable)
    num = random.randint(1, limit) - 1
    if num < 20:
        selection = res.results[num]
    else:
        srch = LocalSearch(app_id=yahooid, category=96926236, results=20,
            query="lunch", location=location, start=num)
        res = srch.parse_results()
        selection = res.results[0]
    return '{Title} @ {Address} - {Url}'.format(**selection)

@command("paste", aliases=(), doc="Drop a link to your latest paste on "
    "http://libpa.st")
def paste(client, event, channel, nick, rest):
    request = urllib.urlopen("http://libpa.st/last/%s" % nick)
    post_url = request.geturl()
    if post_url and request.getcode() == 200:
        return post_url
    else:
        return ("hmm.. I didn't find a recent paste of yours, %s. Checkout "
            "http://libpa.st" % nick)

@execdelay("hi", channel="#botone", howlong=10)
def howdy(client, event):
    return "Howdy everybody!"

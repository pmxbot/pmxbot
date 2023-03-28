import re

from pmxbot.core import command, contains, regexp
from . import api

@command('pivotal', aliases=('pivot', 'pv'), doc="From an id, show a link to the pivotal issue referenced")
def pivotalissue(client, event, channel, nick, rest):
    url = None
    try:
        rest = rest.strip().lstrip('#')
        id = int(rest)
        url = "https://www.pivotaltracker.com/story/show/%d" % id
    except ValueError:
        yield "Invalid Pivotal ID"
        return

    try:
        data = api.lookupStoryAndUsers(id)
        yield url
        for line in api.formatStory(data['story'], owners=data['owners'], reporter=data['reporter']):
            yield line
    except:
        yield "Sorry, I don't understand that Pivotal ID"

@regexp('pivotaltrackerstory', '((?s)^.*)(https://www.pivotaltracker.com.*?/|#)([0-9]{8,9})((?s).*$)', doc="Look up Pivotal issue(s) and return detail")
def pivotalurl(client, event, channel, nick, match):
    # Reassemble the original message, then we'll regexp over that to find
    # potentially many matches
    rest = ''.join(match.groups())
    for id in get_tracker_ids(rest):
        data = api.lookupStoryAndUsers(id)
        for line in api.formatStory(data['story'], owners=data['owners'], reporter=data['reporter']):
            yield line

def get_tracker_ids(msg):
    # First, strip out Slack-formatted links because they're already pretty
    msg = re.sub(r'<.*?\|.*?>', '', msg)
    # Now find all URLs or ids preceded by #
    pattern = '(https://www.pivotaltracker.com.*?/|#)([0-9]{8,9})'
    reg = re.compile(pattern)
    matches = reg.findall(msg)
    return [m[1] for m in matches]

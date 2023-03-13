import json
import re
import subprocess

import pmxbot
from pmxbot.core import command, contains, regexp
import random

from slackbot.pivotal.api import pivotalAPICall, SLACK_TO_PT_USER

#TODO: move these to their own plugin dirs, maybe?


def _dadun():
    return "da-dun da-dun da-dun da-dun-dah"

def R(cmd):
    ''' Run something in R, print its output as JSON, and read in
        the result.
    '''
    try:
        out = subprocess.check_output(["R", "--slave", "-e", "library(superadmin); crunchbot(%s)" % cmd])
    except:
        return "Oops! Error communicating with R"
    try:
        ret = json.loads(out)
    except:
        return "Oops! Invalid JSON returned from R"
    return ret


@command('rebase', doc="""Call REBASE non-randomly""")
def rebase(client, event, channel, nick, rest):
    return _dadun()

@contains('rebase', doc="""REBASE: the bass line from an old-school hiphop song from 1980 called "White Lines" by Grandmaster Melle Mel""")
def dadun(client, event, channel, nick, rest):
    if random.random() <= 0.20:
        return _dadun()
    else:
        return None

@contains('Ticket marked as SOLVED', doc="""Acknowledge Zendesk heroes""")
def zen(client, event, channel, nick, rest):
    person = re.sub(r'^Ticket marked as SOLVED by (.*?):.*$', r'\1', rest)
    if person == "Crunch Bot":
        # Ignore messages from the pivotal tracker integration
        return

    solver_nick = {
        "Mike Malecki": "malecki",
        "Chris Jones": "chrisj",
        "Chris Ferejohn": "cferejohn",
        "Douglas Rivers": "doug",
        "Newton": "Newton Das",
        "Aayat Farooqui": "Aayat",
        "Matthew Steele": "Matt Steele",
        "Vinit Shah": "Vinit Shah"
    }.get(person)

    if solver_nick:
        pmxbot.karma.Karma.store.change(solver_nick, 1)
        msg = "Thanks for answering that, %s! :heart:" % person.split(" ")[0]
    else:
        msg = "Add %s to the <https://github.com/Crunch-io/slackbot-core/blob/master/slackbot/core/handler.py|crunchbot code> so they can get karma (or fix the regex :)" % person

    try:
        # Look for Zendesk tickets to turn into Pivotal stories
        zd_integration = "projects/2172644/integrations/52139/stories?exclude_linked=true"
        tickets = pivotalAPICall(zd_integration)
        if tickets:
            fields = {"name", "description", "story_type", "requested_by_id",
                      "owner_ids", "external_id", "integration_id"}
            for ticket in tickets:
                # Only send the whitelisted fields, otherwise it errors
                body = {k: v for k, v in ticket.items() if k in fields}
                body['labels'] = ['zendesk', 'user-reported']
                body['requested_by_id'] = SLACK_TO_PT_USER.get(solver_nick,
                    body.get('requested_by_id', None))
                resp = pivotalAPICall("projects/2172644/stories", "POST", data=body)
                if "error" in resp:
                    msg += "\nFailure to add %s: %s" % (ticket['name'], resp['error'])
                # else:
                #     msg += "\nAdding ticket %s" % ticket['name']
        # else:
        #     # For debugging
        #     msg += "\nNo Pivotal tickets to make"
    except Exception as e:
        msg += "\nError with Zendesk-Pivotal integration:" + str(e)
    return msg

@regexp('three_sir', r'\b(five|5)\b', doc="Randomly correct people who say 5 when they mean 3, a la Monty Python")
def three_sir(client, event, channel, nick, rest):
    if channel.lower() == pmxbot.config.inane_channel.lower():
        if random.random() < 0.40:
            return random.choice([
                'Five is right out!',
                'Three sir!',
            ])

@command('debug', doc="Output the parameters sent to a command method")
def debug_out(client, event, channel, nick, rest):
    return "client: %s, event: %s, nick: %s, channel: %s, rest: %s" % tuple([repr(x) for x in (client, event, nick, channel, rest)])


shots = ['Badum tish!', 'Gong!', 'Wah wah wah waaaaah!', 'Chirp chirp chirp chirp...cough']

@command('rimshot', aliases=('sting', 'gong', 'sadtrombone', 'crickets'), doc="For comedic effect")
def rimshot(client, event, channel, nick, rest):
    global shots
    ret = random.choice(shots)
    return ret

@command('echo', doc='Returns what was sent as represented by a python string')
def echo(client, event, channel, nick, rest):
    return rest

def lookup_dataset(id):
    cmd = "getDatasets(dsid='%s')" % id
    # Call R
    info = R(cmd)
    if len(info):
        #return info[0]
        facts = [info[0][i] for i in ['id', 'name', 'project_id', 'project_name']]
        return '"<https://eu.superadmin.crint.net/datasets/%s/|%s>", in project <https://eu.superadmin.crint.net/projects/%s|%s>' % tuple(facts)
    else:
        return None

@command('ds', doc='Look up a dataset in superadmin by id or URL')
def ds(client, event, channel, nick, rest):
    # Extract id from "rest" so that it can be a URL
    dsid = re.sub(r'^.*/datasets?/([0-9a-f]{32})/.*$', r'\1', rest)
    # Validate
    if not re.compile("[0-9a-f]{32}").match(dsid):
        return "Invalid dataset id"
    ds_info = lookup_dataset(dsid)
    if ds_info:
        return ds_info
    else:
        return "No dataset found with id %s" % dsid

@regexp('sentry_ds', r'Dataset:([0-9a-f]{32})', doc="Look for dataset ids in sentry messages")
def sentry_ds(client, event, channel, nick, match):
    dsid = match.groups()[0]
    ds_info = lookup_dataset(dsid)
    if ds_info:
        return ds_info

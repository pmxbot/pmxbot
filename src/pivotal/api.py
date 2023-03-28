import json

import requests, time
import pmxbot

baseurl = 'https://www.pivotaltracker.com/services/v5/'

SLACK_TO_PT_USER = {
    'npr': 1143238,
    'malecki': 1144426,
    'cferejohn': 1144452,
    'crunchbot': 1810940,
    'amol': 1940137,
    'jonkeane': 2913047,
    'brian.law': 2947033,
    'chrisj': 3041499
}

#note this is a global cache structure, so {} is ok here
members = {}

def formPivotalURL(path):
    if not path.startswith(baseurl):
        path = baseurl + path
    return path

def pivotalAPICall(url, method='GET', headers=None, params=None, data=None):
    url = formPivotalURL(url)
    m = getattr(requests, method.lower())

    try:
        token = pmxbot.config.pivotal_token
    except AttributeError:
        raise InvalidToken()

    kwargs = dict(params=params, headers={'X-TrackerToken': token})
    if data:
        kwargs['data'] = json.dumps(data)
        kwargs['headers'].update({"Content-Type": "application/json"})
    if headers:
        kwargs['headers'].update(headers)
    r = m(url, **kwargs)

    return r.json()

def requestStory(id):
    """
    {
      "updated_at": "2014-01-09T14:58:11Z",
      "url": "https://www.pivotaltracker.com/story/show/63538280",
      "kind": "story",
      "story_type": "feature",
      "created_at": "2014-01-09T14:58:11Z",
      "project_id": 1111,
      "description": "It would be nice to be able to search pivotal issues in IRC, and it would be great to get issue titles to appear along with the URLs. ",
      "name": "Add Pivotal integration to crunchbot",
      "requested_by_id": 1111,
      "id": 1111,
      "owner_ids": [1111],
      "current_state": "unscheduled",
      "labels": [

      ]
    }
    """

    r = pivotalAPICall('stories/%d' % int(id), 'GET')
    return r

def _requestMemberships(project_id):
    """
    this call returns something like this
    [
      {
        "id": 1111,
        "role": "member",
        "project_id": 1111,
        "wants_comment_notification_emails": true,
        "person": {
          "id": 1111,
          "username": "chrisferejohn",
          "email": "chris@example.com",
          "name": "Chris Ferejohn",
          "kind": "person",
          "initials": "CF"
        },
        "kind": "project_membership",
        "last_viewed_at": "2013-12-20T18:51:16Z"
      },
      etc.
    ]
    """
    r = pivotalAPICall('projects/%d/memberships' % project_id)
    return r

def requestPerson(project_id, person_id):
    global members
    now = time.time()
    if project_id is None or person_id is None:
        return "<none>"
    cache_exp_key = '%d updated' % project_id
    if project_id not in members or members[cache_exp_key] < (now - 4*3600):
        members[project_id] = _requestMemberships(project_id)
        members[cache_exp_key] = now
    for x in members[project_id]:
        if x['person']['id'] == person_id:
            return x['person']
    return "Unable to look up person %d" % person_id

def nameFromPerson(person):
    if isinstance(person, str):
        return person
    else:
        return person['name']

def formatStory(story, reporter="<none>", owners="<none>"):
    "Return a formatted string representing the story for IRC"

    if owners == []:
        owners = "(No one)"
    else:
        owners = ', '.join(owners)

    type_emoji = {
        "bug": ":beetle:",
        "feature": ":ticket:",
        "release": ":checkered_flag:",
        "chore": ":gear:"
    }
    state_emoji = {
        "rejected": ":x:",
        "accepted": ":white_check_mark:",
        "started": ":large_blue_diamond:",
        "finished": ":large_orange_diamond:",
        "unscheduled": ":snowman:",
        "unstarted": ":white_large_square:",
        "delivered": ":shipit:"
    }

    repdict = {
        'type': type_emoji.get(story['story_type'], story['story_type']),
        'name': story['name'].strip(),
        'url': story['url'],
        'reporter_name': reporter,
        'owners': owners,
        'current_state': story['current_state'].title(),
        'state_emoji': state_emoji.get(story['current_state'], "")
    }

    yield """%(type)s <%(url)s|%(name)s>. Reported by %(reporter_name)s; owned by %(owners)s; state %(current_state)s %(state_emoji)s""" % repdict

class PivotalException(Exception):
    "Generic Pivotal Exception %s"

    def __str__(self):
        #if self.args:
        #    return self.__doc__ % self.args
        #else:
        return self.__doc__

class InvalidToken(PivotalException):
    "Unable to use pivotal api token. Have you configured 'pivotal_token' in your config.yaml file?"

def lookupStoryAndUsers(id):
    #grab the story
    try:
        story = requestStory(id)
        owners = [requestPerson(story['project_id'], p)
            for p in story.get('owner_ids', [])]
        owners = [nameFromPerson(p) for p in owners]
        reporter = requestPerson(story['project_id'], story.get('requested_by_id', None))
        reporter = nameFromPerson(reporter)
    except PivotalException as e:
        return str(e)
    return dict(story=story, owners=owners, reporter=reporter)

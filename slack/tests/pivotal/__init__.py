# -*- coding: utf-8 -*-
import os
import pmxbot
from ...core.tests import TestHandler

#You need an api key on an account that has access to Joseph's
#public test project. Contact jtate@dragonstrider.com for access
api_key = os.environ.get('PIVOTAL_API_TOKEN', None)
story_id = os.environ.get('PIVOTAL_STORY_ID', None)

stories = {
    'unscheduled':  64068270,
    'unstarted':    64068314,
    'started':      64068372,
    'finished':     64068426,
    'delivered':    64068466,
    'accepted':     64068716,
    'rejected':     64068748,
    'deletedoneowner': 103708734,
    'deletedowner': 103708716,
    'deletedreporter': 103708644
}

stories['unassigned'] = 64068218
stories['chore'] = stories['started']
stories['bug'] = stories['unstarted']
stories['feature'] = stories['accepted']

story_fixture = {
      "updated_at": "2014-01-09T14:58:11Z",
      "url": "https://www.pivotaltracker.com/story/show/63538280",
      "kind": "story",
      "story_type": "feature",
      "created_at": "2014-01-09T14:58:11Z",
      "project_id": 1111,
      "description": "It would be nice to be able to search pivotal issues in IRC, and it would be great to get issue titles to appear along with the URLs. ",
      "name": "Add Pivotal integration to crunchbot\n",
      "requested_by_id": 99991,
      "id": 888888,
      "owner_ids": [99991],
      "current_state": "unscheduled",
      "labels": [ ]
    }


def degenerate(generator):
    #Makes a generator of strings a null joined string for easier verification
    return '\0'.join(generator)

class PivotalTest(TestHandler):

    @classmethod
    def setup_class(cls):
        TestHandler.setup_class()
        pmxbot.config.pivotal_token = api_key

    @classmethod
    def teardown_class(cls):
        TestHandler.teardown_class()
        del pmxbot.config.pivotal_token

    def _skip(self):
        global story_id
        if api_key is None:
            self.skipTest("No PIVOTAL_API_TOKEN environment variable provided, skipping") #pragma: no cover
        if story_id is None:
            story_id = stories['unstarted']



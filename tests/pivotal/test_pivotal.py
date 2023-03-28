# -*- coding: utf-8 -*-
import re
import random
from unittest import TestCase
import src.pivotal as commands
from src.pivotal import tests
from src.pivotal import api


class TestRegularExpressions(TestCase):
    def test_match_url(self):
        urls = [
            "https://www.pivotaltracker.com/story/show/162356558",
            "https://www.pivotaltracker.com/s/projects/stories/162356558",
            "https://www.pivotaltracker.com/services/v5/projects/123456/stories/162356558/"
        ]
        for u in urls:
            self.assertEqual(commands.get_tracker_ids(u), ["162356558"])

    def test_match_number(self):
        self.assertEqual(commands.get_tracker_ids("blah #162356558"), ["162356558"])

    def test_match_many(self):
        msg = "See also https://www.pivotaltracker.com/story/show/162356558 and #132356957"
        self.assertEqual(commands.get_tracker_ids(msg), ["162356558", "132356957"])

    def test_dont_match_slack_links(self):
        msg = "See also <https://www.pivotaltracker.com/story/show/162356558|this one>" \
            "and <https://www.pivotaltracker.com/story/show/132356957|that one>" \
            "and also https://www.pivotaltracker.com/story/show/122238843"
        self.assertEqual(commands.get_tracker_ids(msg), ["122238843"])


class TestPivotalHandlers(tests.PivotalTest):
    def test_pivotalurl(self):
        self._skip()
        patt = re.compile('https://www.pivotaltracker.com/(.*/stories/|story/show/)(\d+)')

        g = patt.search('https://www.pivotaltracker.com/s/projects/999999/stories/%s' % tests.story_id)
        ret = tests.degenerate(commands.pivotalurl("", "", "", "", g))
        self.assertTrue(ret.startswith('Bug'), ret)
        self.assertIn(str(tests.story_id), ret)

        g = patt.search('https://www.pivotaltracker.com/story/show/%s' % tests.story_id)
        ret = tests.degenerate(commands.pivotalurl("", "", "", "", g))
        self.assertTrue(ret.startswith('Bug'), ret)
        self.assertIn(str(tests.story_id), ret)

    def test_pivotalissue(self):
        self._skip()
        ret = tests.degenerate(commands.pivotalissue('', '', '', '', str(tests.stories['unassigned'])))
        self.assertIn('No one', ret)
        self.assertIn('Joseph Tate', ret)

        #repeat test with leading #
        ret = tests.degenerate(commands.pivotalissue('', '', '', '', '#' + str(tests.stories['unassigned'])))
        self.assertIn('No one', ret)
        self.assertIn('Joseph Tate', ret)

        ret = tests.degenerate(commands.pivotalissue('', '', '', '', ''))
        self.assertTrue( ret.startswith("Invalid Pivotal ID") )

        ret = tests.degenerate(commands.pivotalissue('', '', '', '', '-1939'))
        self.assertTrue( ret.startswith("Sorry, I don't understand that Pivotal ID"))


class TestAPIErrors(TestCase):
    def test_pivotalAPICallNoToken(self):
        self.assertRaises(api.InvalidToken, api.pivotalAPICall, 'foo')

    def test_requestPersonNone(self):
        self.assertEqual(api.requestPerson(None, None), '<none>')
        self.assertEqual(api.requestPerson(1, None), '<none>')
        self.assertEqual(api.requestPerson(None, 1), '<none>')

    def test_requestPersonMissing(self):
        api.members[-1] = []
        api.members['-1 updated'] = api.time.time()
        self.assertEqual(api.requestPerson(-1, 999), 'Unable to look up person 999')
        api.members.clear()

    def test_lookupStoryAndUsersError(self):
        self.assertEqual(api.lookupStoryAndUsers(999), api.InvalidToken.__doc__)

class TestPivotalAPI(tests.PivotalTest):
    def test_unassignedStory(self):
        self._skip()
        sid = tests.stories['unassigned']
        ret = api.lookupStoryAndUsers(sid)
        self.assertEqual(ret['owners'], [], ret)

    def test_deleted_users(self):
        self._skip()
        sid = tests.stories['deletedowner']
        ret = api.lookupStoryAndUsers(sid)
        self.assertEqual(ret['owners'], ['Unable to look up person 1798586'])

        sid = tests.stories['deletedoneowner']
        ret = api.lookupStoryAndUsers(sid)
        self.assertEqual(set(ret['owners']), set(['Unable to look up person 1798586', 'Joseph Tate']))

        sid = tests.stories['deletedreporter']
        ret = api.lookupStoryAndUsers(sid)
        self.assertEqual(ret['reporter'], 'Unable to look up person 1798586')
        self.assertEqual(ret['owners'], [])


    def test_statuses(self):
        self._skip()
        for x in random.sample(('accepted', 'delivered', 'finished', 'started', 'rejected', 'unstarted', 'unscheduled'), 2):
            ret = api.lookupStoryAndUsers(tests.stories[x])
            self.assertEqual(ret['story']['current_state'], x)

    def test_lookupStoryAndUsers(self):
        'This tests most of the module'
        self._skip()
        sid = int(tests.story_id)
        ret = api.lookupStoryAndUsers(sid)
        assert(ret['story']['url'].startswith('https://www.pivotaltracker.com/story/show/%d' % sid))
        self.assertNotEqual(ret['owners'], '<none>')
        self.assertNotEqual(ret['reporter'], '<none>')
        self.assertIn('Joseph Tate', ret['owners'])
        self.assertIn('Joseph Tate', ret['reporter'])

    def test_nameFromPerson(self):
        self._skip()
        self.assertEqual(api.nameFromPerson('<none>'), '<none>')
        self.assertEqual(api.nameFromPerson({'name': 'Foo Bar'}), 'Foo Bar')

    def test_formatStory(self):
        res = tests.degenerate(api.formatStory(tests.story_fixture, owners=["Neál Richardson"], reporter="Joseph Tate"))
        expected = ":ticket: <https://www.pivotaltracker.com/story/show/63538280|Add Pivotal integration to crunchbot>. Reported by Joseph Tate; owned by Neál Richardson; state Unscheduled :snowman:"
        self.assertEqual(res, expected)

    def test_formatStoryNoOne(self):
        res = tests.degenerate(api.formatStory(tests.story_fixture, owners=[], reporter="Joseph Tate"))
        assert "(No one)" in res, res

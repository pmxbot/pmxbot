from . import TestHandler
from ..import handler
import random
import pmxbot
import re

class TestCoreHandler(TestHandler):
    def test_rimshot(self):
        random.seed(12)
        vals = [ random.choice(handler.shots) for x in range(0,12)]

        random.seed(12)
        for corpum in vals:
            ret = handler.rimshot(None, None, None, None, None)
            self.assertEqual(ret, corpum)

    def test_debug_out(self):
        vals = ('aaaa', 'bbbb', '#cccc', 'dddd', 'eeee')
        ret = handler.debug_out(*vals)
        for x in vals:
            self.assertTrue(x in ret)

    def test_echo(self):
        ret = handler.echo('', '', '', '', '\x16iii\x0f')
        self.assertEqual('\x16iii\x0f', ret)

        #passthrough
        ret = handler.echo('', '', '', '', '\\u2603\xe9\xf4\xef\xf1')
        self.assertEqual('\\u2603\xe9\xf4\xef\xf1', ret)

    def test_rebase(self):
        random.seed(31)
        ret = handler.dadun('', '', '#public', '', '')
        self.assertTrue(ret.startswith("da-dun da-dun"))

        random.seed(2)
        ret = handler.dadun('', '', '#public', '', '')
        self.assertEqual(ret, None)

        ret = handler.rebase('', '', '#public', '', '')
        self.assertTrue(ret.startswith("da-dun"))

    def test_three_sir(self):
        r = r'\b(five|5)\b'
        ret = handler.three_sir('', '', '#public', '', '')
        self.assertEqual(ret, None)

        random.seed(31)
        ret = handler.three_sir('', '', '#inane', '', '')
        self.assertEqual(ret, "Five is right out!")

        rr = re.compile(r)
        self.assertTrue(rr.search('this should match 5'))
        self.assertTrue(rr.search('5 this will match'))
        self.assertTrue(rr.search('this 5 will match'))
        self.assertTrue(not rr.search('this 5will not match'))
        self.assertTrue(not rr.search('this wi5ll not match'))
        self.assertTrue(rr.search('five this will match'))
        self.assertTrue(rr.search('this should match five'))
        self.assertTrue(rr.search('this five will match'))
        self.assertTrue(not rr.search('this fivewill not match'))
        self.assertTrue(not rr.search('this wifivell not match'))

    def test_sentry_ds(self):
        regexp = re.compile(r'Dataset:([0-9a-f]{32})')
        msg = '<https://sentry.io/organizations/blah/issues/123/?project=456&referrer=slack|Error: 2>; Culprit:append; Dataset:1b6de58e0dd8a3abdc64d6a696683b3e; Project:production'
        self.assertEqual(regexp.search(msg).groups()[0], "1b6de58e0dd8a3abdc64d6a696683b3e")

import time

from . import PmxbotHarness

class TestPivotalMessages(PmxbotHarness):
    def test_no_op(self):
        "Test that the harness is working."

    def test_pvurl(self):
        self.client.send_message('#logged', 'This is just a test to see if the pivotalurl thing works https://www.pivotaltracker.com/story/show/64068466 in the middle of a message')

        self.check_for_log_msg(channel='#logged', nick='pmxbotTesting', message='Delivered Story')

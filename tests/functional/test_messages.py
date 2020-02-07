import time

from tests.functional import PmxbotHarness


class TestPmxbotMessages(PmxbotHarness):
    def test_no_op(self):
        """
        Test that the harness is working.
        """

    def test_non_ascii_message(self):
        """
        pmxbot should still be able to send international characters
        """
        self.client.send_message('#inane', '!echo язык')
        time.sleep(0.2)
        assert self.bot.poll() is None, "Bot failed sending non-ASCII message"

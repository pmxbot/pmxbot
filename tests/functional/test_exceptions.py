import time

from tests.functional import PmxbotHarness


class TestPmxbotExceptions(PmxbotHarness):
    def test_no_op(self):
        """
        Test that the harness is working.
        """

    def test_exception(self):
        """
        pmxbot should still be running after running a crashing command
        """
        self.client.send_message('#inane', '!crashnow')
        time.sleep(0.2)
        assert self.bot.poll() is None, "Bot is no longer running"

    def test_exception_in_generator(self):
        """
        pmxbot should still be running after running a crashing command
        """
        self.client.send_message('#inane', '!crashiter')
        time.sleep(0.2)
        assert self.bot.poll() is None, "Bot is no longer running"

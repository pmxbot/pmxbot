import time

from tests.functional import PmxbotHarness


class TestPmxbotRegexp(PmxbotHarness):
    def test_feck(self):
        """
        We send a command to the logged channel to make sure that the
        reponse happens
        """
        self.client.send_message('#logged', 'What the feck?!')
        time.sleep(0.2)
        assert self.check_logs(
            '#logged', nick="pmxbotTest", message="Clean up your language testingbot"
        )

import time
import uuid

from tests.functional import PmxbotHarness


class TestPmxbotLog(PmxbotHarness):
    def test_no_op(self):
        """
        Test that the harness is working.
        """

    def test_not_logged_channel(self):
        """
        Test that a basic message in an unlogged room is unlogged.
        """
        id = str(uuid.uuid4())
        msg = 'Unlogged msg from test_not_logged_channel. %s' % id
        self.client.send_message('#inane', msg)
        assert not self.check_logs(channel="#inane", message=msg)

    def test_logged_channel(self):
        """
        Test whether a basic message in a logged room is logged.
        """
        id = str(uuid.uuid4())
        msg = 'Logged msg from test_logged_channel. %s' % id
        self.client.send_message('#logged', msg)
        assert self.check_logs(channel="#logged", message=msg)

    def test_logged_channel_again(self):
        """
        Test whether a second basic message in a logged room is logged.
        """
        id = str(uuid.uuid4())
        msg = 'Logged msg number 2 from test_logged_channel_again. %s' % id
        self.client.send_message('#logged', msg)
        assert self.check_logs(channel="#logged", message=msg)

    def test_logged_channel_international(self):
        """
        Test that international characters get logged properly.
        """
        msg = 'Я предпочитаю круассаны с рыбой. {id}'.format(id=str(uuid.uuid4()))
        self.client.send_message('#logged', msg)
        assert self.check_logs(channel='#logged', message=msg)

    def test_strike_1(self):
        """
        Test the strike function for a single line.

        Send a single line that will remain, test that it was logged, then send
        one line that will be deleted, check it was logged, strike it, and check
        that it was deleted and the single line remains.
        """
        id = str(uuid.uuid4())
        pre_text = 'Strike pre-text msg from test_strike_1. %s' % id
        self.client.send_message('#logged', pre_text)
        assert self.check_logs(channel="#logged", message=pre_text)

        msg = 'Strike ME msg from test_strike_1. %s' % id
        self.client.send_message('#logged', msg)
        assert self.check_logs(channel="#logged", message=msg)

        self.client.send_message('#logged', "!strike")
        assert not self.check_logs(channel="#logged", message=msg)
        assert self.check_logs(channel="#logged", message=pre_text)

    def test_strike_3(self):
        """
        Test the strike function for multiple lines.

        Send a single line that will remain, test that it was logged, then send
        3 lines, test they were logged, send a strike 3, test the 3 lines were
        removed, and the pre-text still remains.
        """
        id = str(uuid.uuid4())
        pre_text = "Strike test pre-text from test_strike_3 %s" % id
        self.client.send_message("#logged", pre_text)
        assert self.check_logs(channel="#logged", message=pre_text)

        base = "Strike ME msg %s from test_strike_3. " + id
        for i in range(1, 4):
            self.client.send_message('#logged', base % i)
        for i in range(1, 4):
            assert self.check_logs(channel="#logged", message=(base % i))
        self.client.send_message('#logged', "!strike 3")
        for i in range(1, 4):
            assert not self.check_logs(channel="#logged", message=(base % i))
        assert self.check_logs(channel="#logged", message=pre_text)

    def test_blank_input_logged(self):
        self.client.send_message("#logged", '')
        time.sleep(1)
        assert self.bot.poll() is None

    def test_blank_input_notlogged(self):
        self.client.send_message("#inane", '')
        time.sleep(1)
        assert self.bot.poll() is None

    def test_onespace_input_logged(self):
        self.client.send_message("#logged", '  ')
        time.sleep(1)
        assert self.bot.poll() is None

    def test_onespace_input_notlogged(self):
        self.client.send_message("#inane", '  ')
        time.sleep(1)
        assert self.bot.poll() is None

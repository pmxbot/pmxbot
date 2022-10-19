import pytest

from pmxbot import logging


class TestLogging:
    @pytest.fixture
    def logger(self, request, db_uri):
        logger = logging.Logger.from_URI(db_uri)
        request.addfinalizer(logger.clear)
        return logger

    def test_get_random_logs(self, logger):
        logger.message('#inane', 'nik', 'message one')
        logger.message('#inane', 'nik', 'message two')
        messages = list(logger.get_random_logs(2))
        assert len(messages) == 2
        assert set(messages) == set(['message one', 'message two'])


class TestMongoDBLogging:
    def setup_logging(self, mongodb_uri):
        mongodb_uri = mongodb_uri + '/pmxbot_test'
        self.logger = logging.Logger.from_URI(mongodb_uri)
        return self.logger

    def teardown_method(self, method):
        if hasattr(self, 'logger'):
            self.logger.db.drop()
            self.logger.db.database.recent.drop()

    def test_message(self, mongodb_uri):
        self.setup_logging(mongodb_uri)
        self.logger.message(
            '#channel5', 'nik', 'something great happened today - the test passed'
        )
        assert self.logger.db.count_documents({}) == 1
        assert 'test passed' in self.logger.db.find_one()['message']

    def test_list_channels(self, mongodb_uri):
        logger = self.setup_logging(mongodb_uri)
        logger.message('#inane', 'nik', 'message one')
        logger.message('#inane', 'sam', 'message two')
        logger.message('#bar', 'nik', 'in walk two olives')
        channels = logger.list_channels()
        assert len(channels) == 2
        assert set(channels) == set(['bar', 'inane'])

    def test_search_miss(self, mongodb_uri):
        logger = self.setup_logging(mongodb_uri)
        assert not logger.search("foo")

    def test_search_hit(self, mongodb_uri):
        logger = self.setup_logging(mongodb_uri)
        logger.message('#inane', 'joe', "who da foo?")
        logger.make_anchor = "anchor".format
        (result,) = logger.search("foo")
        channel, date, anchor, msgs = result
        (msg_info,) = msgs
        time, nick, text = msg_info
        assert channel == 'inane'
        assert anchor == 'anchor'
        assert nick == 'joe'
        assert text == 'who da foo?'

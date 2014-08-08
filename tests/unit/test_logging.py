from pmxbot import logging

class TestMongoDBLogging(object):
	def setup_logging(self, mongodb_uri):
		logger = logging.Logger.from_URI(mongodb_uri)
		logger.db = logger.db.database.connection[
			logger.db.database.name+'_test'
			][logger.db.name]
		self.logger = logger
		return logger

	def teardown_method(self, method):
		if hasattr(self, 'logger'):
			self.logger.db.drop()
			self.logger.db.database.recent.drop()

	def test_message(self, mongodb_uri):
		self.setup_logging(mongodb_uri)
		l = self.logger
		l.message('#channel5', 'nik', 'something great happened today - '
			'the test passed')
		assert l.db.count() == 1
		assert 'test passed' in l.db.find_one()['message']

	def test_get_random_logs(self, mongodb_uri):
		l = self.setup_logging(mongodb_uri)
		l.message('#inane', 'nik', 'message one')
		l.message('#inane', 'nik', 'message two')
		messages = list(l.get_random_logs(2))
		assert len(messages) == 2
		assert set(messages) == set(['message one', 'message two'])

	def test_list_channels(self, mongodb_uri):
		l = self.setup_logging(mongodb_uri)
		l.message('#inane', 'nik', 'message one')
		l.message('#inane', 'sam', 'message two')
		l.message('#bar', 'nik', 'in walk two olives')
		channels = l.list_channels()
		assert len(channels) == 2
		assert set(channels) == set(['bar', 'inane'])

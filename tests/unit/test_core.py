import datetime
from unittest import TestCase, mock

from irc.schedule import DelayedCommand, now

from pmxbot.irc import LoggingCommandBot


class DelayedCommandMatch:
    def __eq__(self, other):
        return isinstance(other, DelayedCommand)


class LoggingCommandBotTest(TestCase):
    def setUp(self):
        self.bot = LoggingCommandBot(
            'localhost', 1234, 'some-nick', ['#some-channel'])

    @mock.patch('functools.partial')
    def test_doesnt_schedule_same_command_twice(self, mock_partial):
        conn = mock.MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = now()
        func = lambda x: x
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, doc)
        self.bot._schedule_at(conn, name, channel, when, func, doc)

        conn.reactor._schedule_command.assert_called_once_with(
            DelayedCommandMatch())
        mock_partial.assert_called_once_with(
            self.bot.background_runner, channel, func)

    @mock.patch('functools.partial')
    def test_schedules_same_command_if_names_differ(self, mock_partial):
        conn = mock.MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = now()
        func = lambda x: x
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, doc)
        self.bot._schedule_at(conn, 'other', channel, when, func, doc)

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            mock.call(DelayedCommandMatch()),
            mock.call(DelayedCommandMatch()),
        ])

    @mock.patch('functools.partial')
    def test_schedules_same_command_if_channels_differ(self, mock_partial):
        conn = mock.MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = now()
        func = lambda x: x
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, doc)
        self.bot._schedule_at(conn, name, '#other', when, func, doc)

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            mock.call(DelayedCommandMatch()),
            mock.call(DelayedCommandMatch()),
        ])

    @mock.patch('functools.partial')
    def test_schedules_same_command_if_datetimes_differ(self, mock_partial):
        conn = mock.MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = now()
        future = when + datetime.timedelta(days=15)
        func = lambda x: x
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, doc)
        self.bot._schedule_at(conn, name, channel, future, func, doc)

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            mock.call(DelayedCommandMatch()),
            mock.call(DelayedCommandMatch()),
        ])

    @mock.patch('functools.partial')
    def test_schedules_same_command_if_docs_differ(self, mock_partial):
        conn = mock.MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = now()
        func = lambda x: x
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, doc)
        self.bot._schedule_at(conn, name, channel, when, func, 'other')

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            mock.call(DelayedCommandMatch()),
            mock.call(DelayedCommandMatch()),
        ])

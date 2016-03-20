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
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, channel, when, func, args, doc)

        conn.reactor._schedule_command.assert_called_once_with(
            DelayedCommandMatch())
        mock_partial.assert_called_once_with(
            self.bot.background_runner, conn, channel, func, args)

    @mock.patch('functools.partial')
    def test_schedules_same_command_if_args_differ(self, mock_partial):
        conn = mock.MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = now()
        func = lambda x: x
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, channel, when, func, args + [4], doc)

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            mock.call(DelayedCommandMatch()),
            mock.call(DelayedCommandMatch()),
        ])

    @mock.patch('functools.partial')
    def test_schedules_same_command_if_names_differ(self, mock_partial):
        conn = mock.MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = now()
        func = lambda x: x
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, 'other', channel, when, func, args, doc)

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
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, '#other', when, func, args, doc)

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
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, channel, future, func, args, doc)

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
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, channel, when, func, args, 'other')

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            mock.call(DelayedCommandMatch()),
            mock.call(DelayedCommandMatch()),
        ])

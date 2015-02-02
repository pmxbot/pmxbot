import datetime
from unittest import TestCase

from irc.schedule import DelayedCommand
from mock import MagicMock, call, patch

from pmxbot.core import LoggingCommandBot


class DelayedCommandMatch:
    def __eq__(self, other):
        return isinstance(other, DelayedCommand)


class LoggingCommandBotTest(TestCase):
    def setUp(self):
        self.bot = LoggingCommandBot(
            'localhost', 1234, 'some-nick', ['#some-channel'])

    @patch('functools.partial')
    def test_doesnt_schedule_same_command_twice(self, mock_partial):
        conn = MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = datetime.datetime.now()
        func = lambda x: x
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, channel, when, func, args, doc)

        conn.reactor._schedule_command.assert_called_once_with(
            DelayedCommandMatch())
        mock_partial.assert_called_once_with(
            self.bot.background_runner, conn, channel, func, args)

    @patch('functools.partial')
    def test_schedules_same_command_if_args_differ(self, mock_partial):
        conn = MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = datetime.datetime.now()
        func = lambda x: x
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, channel, when, func, args + [4], doc)

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            call(DelayedCommandMatch()),
            call(DelayedCommandMatch()),
        ])

    @patch('functools.partial')
    def test_schedules_same_command_if_names_differ(self, mock_partial):
        conn = MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = datetime.datetime.now()
        func = lambda x: x
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, 'other', channel, when, func, args, doc)

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            call(DelayedCommandMatch()),
            call(DelayedCommandMatch()),
        ])

    @patch('functools.partial')
    def test_schedules_same_command_if_channels_differ(self, mock_partial):
        conn = MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = datetime.datetime.now()
        func = lambda x: x
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, '#other', when, func, args, doc)

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            call(DelayedCommandMatch()),
            call(DelayedCommandMatch()),
        ])

    @patch('functools.partial')
    def test_schedules_same_command_if_datetimes_differ(self, mock_partial):
        conn = MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = datetime.datetime.now()
        future = when + datetime.timedelta(days=15)
        func = lambda x: x
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, channel, future, func, args, doc)

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            call(DelayedCommandMatch()),
            call(DelayedCommandMatch()),
        ])

    @patch('functools.partial')
    def test_schedules_same_command_if_docs_differ(self, mock_partial):
        conn = MagicMock()
        name = 'some name'
        channel = '#some-channel'
        when = datetime.datetime.now()
        func = lambda x: x
        args = [1, 2, 3]
        doc = 'some doc'

        self.bot._schedule_at(conn, name, channel, when, func, args, doc)
        self.bot._schedule_at(conn, name, channel, when, func, args, 'other')

        self.assertEqual(conn.reactor._schedule_command.mock_calls, [
            call(DelayedCommandMatch()),
            call(DelayedCommandMatch()),
        ])

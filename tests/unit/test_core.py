import datetime
import copy

import pytest
from tempora.schedule import DelayedCommand, now

from pmxbot.core import AtHandler, Scheduled


class DelayedCommandMatch:
    def __eq__(self, other):
        return isinstance(other, DelayedCommand)


@pytest.fixture
def patch_scheduled_registry(monkeypatch):
    """
    Ensure Scheduled._registry is not mutated by these tests.
    """
    monkeypatch.setattr(Scheduled, '_registry', [])


@pytest.mark.usefixtures("patch_scheduled_registry")
class TestScheduledHandlerUniqueness:
    @pytest.fixture
    def handler(self):
        return AtHandler(
            name='some name',
            channel='#some-channel',
            when=now(),
            func=lambda x: x,
            doc='some doc',
        )

    def test_doesnt_schedule_same_command_twice(self, handler):
        handler.register()
        copy.copy(handler).register()

        assert len(Scheduled._registry) == 1

    def test_schedules_same_command_if_names_differ(self, handler):
        handler.register()

        handler2 = copy.copy(handler)
        handler2.name = 'other'
        handler2.register()

        assert len(Scheduled._registry) == 2

    def test_schedules_same_command_if_channels_differ(self, handler):
        handler.register()

        handler2 = copy.copy(handler)
        handler2.channel = '#other'
        handler2.register()

        assert len(Scheduled._registry) == 2

    def test_schedules_same_command_if_datetimes_differ(self, handler):
        handler.register()

        handler2 = copy.copy(handler)
        handler2.when = handler.when + datetime.timedelta(days=15)
        handler2.register()

        assert len(Scheduled._registry) == 2

    def test_schedules_same_command_if_docs_differ(self, handler):
        handler.register()

        handler2 = copy.copy(handler)
        handler2.doc = 'other'
        handler2.register()

        assert len(Scheduled._registry) == 2

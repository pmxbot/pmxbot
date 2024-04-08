import datetime
import copy

import pytest
from tempora.schedule import DelayedCommand, now

from pmxbot.core import AtHandler, Handler, Scheduled, command, initialize
from pmxbot.dictlib import ConfigDict
from pmxbot import irc
from pmxbot import slack


class DelayedCommandMatch:
    def __eq__(self, other):
        return isinstance(other, DelayedCommand)


@pytest.fixture
def patch_scheduled_registry(monkeypatch):
    """
    Ensure Scheduled._registry is not mutated by these tests.
    """
    monkeypatch.setattr(Scheduled, '_registry', [])


@pytest.fixture
def patch_handler_registry(monkeypatch):
    """
    Ensure Handler._registry is not mutated by these tests.
    """
    monkeypatch.setattr(Handler, '_registry', [])


@pytest.fixture
def logging_command_irc_bot_config():
    return ConfigDict({
        "server_host": "irc.example.com",
        "server_port": 23,
        "password": "some-secret",
        "bot_nickname": "test-bot",
        "log_channels": ["sample-log-channel"],
        "other_channels": ["sample-other-chan", "sample-other-chan2"],
    })


@pytest.fixture
def silent_command_irc_bot_config(logging_command_irc_bot_config):
    config = ConfigDict(logging_command_irc_bot_config)
    config["bot class"] = "pmxbot.irc:SilentCommandBot"
    return config


@pytest.fixture
def slack_bot_config():
    return ConfigDict({
        "slack token": "sample_slack_token",
        "slack_cache_ttl": 3600,
        "slack_pagesize": 1,
    })


@pytest.fixture(
    params=[
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": 1000,
            "slack_pagesize": 0,
        },
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": 1000,
            "slack_pagesize": -1,
        },
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": 1000,
            "slack_pagesize": 10000,
        },
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": 0,
            "slack_pagesize": 0,
        },
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": -1,
            "slack_pagesize": -1,
        },
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": 0,
            "slack_pagesize": 10,
        },
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": -1,
            "slack_pagesize": 10,
        },
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": "test",
            "slack_pagesize": 10,
        },
        {
            "slack token": "sample_slack_token",
            "slack_cache_ttl": 10,
            "slack_pagesize": "test",
        },
    ]
)
def slack_bot_invalid_config(request):
    return ConfigDict(request.param)


def test_initialize_irc_bot_with_defaults():
    config = ConfigDict()
    bot = initialize(config)

    assert isinstance(bot, irc.LoggingCommandBot)
    assert bot.nickname == "pmxbot"
    assert bot._nickname == "pmxbot"
    assert bot._realname == "pmxbot"
    assert bot._channels == []
    assert bot.servers[0].host == "localhost"
    assert bot.servers[0].port == 6667
    assert bot.servers[0].password is None


def test_initialize_logging_command_irc_bot(logging_command_irc_bot_config):
    bot = initialize(logging_command_irc_bot_config)

    assert isinstance(bot, irc.LoggingCommandBot)
    assert bot.nickname == "test-bot"
    assert bot._nickname == "test-bot"
    assert bot._realname == "test-bot"
    assert bot.servers[0].host == "irc.example.com"
    assert bot.servers[0].port == 23
    assert bot.servers[0].password == "some-secret"
    assert bot._channels == [
        "sample-log-channel",
        "sample-other-chan",
        "sample-other-chan2",
    ]


def test_initialize_silent_command_irc_bot(silent_command_irc_bot_config):
    bot = initialize(silent_command_irc_bot_config)

    assert isinstance(bot, irc.SilentCommandBot)
    assert bot.nickname == "test-bot"
    assert bot._nickname == "test-bot"
    assert bot._realname == "test-bot"
    assert bot.servers[0].host == "irc.example.com"
    assert bot.servers[0].port == 23
    assert bot.servers[0].password == "some-secret"
    assert bot._channels == [
        "sample-log-channel",
        "sample-other-chan",
        "sample-other-chan2",
    ]


def test_initialize_slack_bot_with_defaults(slack_bot_config):
    bot = initialize(
        ConfigDict({
            "slack token": "sample_slack_token",
            "slack_cache_ttl": None,
            "slack_pagesize": None,
        })
    )

    assert isinstance(bot, slack.Bot)
    assert bot.slack.token == "sample_slack_token"
    assert bot.slack_cache_ttl == slack.DEFAULT_SLACK_CACHE_TTL
    assert bot.slack_pagesize == slack.DEFAULT_SLACK_PAGESIZE


def test_initialize_slack_bot(slack_bot_config):
    bot = initialize(slack_bot_config)

    assert isinstance(bot, slack.Bot)
    assert bot.slack.token == "sample_slack_token"
    assert bot.slack_cache_ttl == 3600
    assert bot.slack_pagesize == 1


def test_invalid_initialize_slack_bot(slack_bot_invalid_config):
    with pytest.raises(ValueError):
        initialize(slack_bot_invalid_config)


@pytest.mark.usefixtures("patch_handler_registry")
class TestCommandHandlerUniqueness:
    def test_command_with_aliases(self):
        @command(aliases='mc')
        def my_cmd():
            "help for my command"

        assert len(Handler._registry) == 2

        # attempt to re-registor both the command and its alias
        for handler in Handler._registry:
            copy.deepcopy(handler).register()

        assert len(Handler._registry) == 2


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

import pytest
from unittest.mock import MagicMock, patch

from pmxbot import slack


@pytest.fixture
def slack_bot():
    with patch("slack_sdk.rtm_v2.RTMClient"):
        slack_bot = slack.Bot("fake token", 1, 1)
        return slack_bot


@pytest.fixture
def slack_user_list():
    user_list = iter([
        {
            "members": [
                {
                    "id": "foo1",
                    "name": "foo1",
                    "profile": {"email": "foo1@example.com"},
                },
                {
                    "id": "foo2",
                    "name": "foo2",
                    "profile": {"email": "foo2@example.com"},
                },
                {
                    "id": "foo3",
                    "name": "foo3",
                    "profile": {"email": "foo3@example.com"},
                },
                {
                    "id": "foo4",
                    "name": "foo4",
                    "profile": {"email": "foo4@example.com"},
                },
            ]
        },
        {
            "members": [
                {
                    "id": "bar1",
                    "name": "bar1",
                    "profile": {"email": "bar1@example.com"},
                },
                {
                    "id": "bar2",
                    "name": "bar2",
                    "profile": {"email": "bar2@example.com"},
                },
                {
                    "id": "bar3",
                    "name": "bar3",
                    "profile": {"email": "bar3@example.com"},
                },
                {
                    "id": "bar4",
                    "name": "bar4",
                    "profile": {"email": "bar4@example.com"},
                },
            ]
        },
        {
            "members": [
                {
                    "id": "baz1",
                    "name": "baz1",
                    "profile": {"email": "baz1@example.com"},
                },
                {
                    "id": "baz2",
                    "name": "baz2",
                    "profile": {},
                },
                {
                    "id": "baz3",
                    "name": "baz3",
                    "profile": {"email": "baz3@example.com"},
                },
            ]
        },
    ])
    return user_list


@pytest.fixture
def slack_conversation_list():
    conversation_list = iter([
        {
            "channels": [
                {
                    "id": "foo1",
                    "name": "foo1",
                },
                {
                    "id": "foo2",
                    "name": "foo2",
                },
                {
                    "id": "foo3",
                    "name": "foo3",
                },
                {
                    "id": "foo4",
                    "name": "foo4",
                },
            ]
        },
        {
            "channels": [
                {
                    "id": "bar1",
                    "name": "bar1",
                },
                {
                    "id": "bar2",
                    "name": "bar2",
                },
                {
                    "id": "bar3",
                    "name": "bar3",
                },
                {
                    "id": "bar4",
                    "name": "bar4",
                },
            ]
        },
        {
            "channels": [
                {
                    "id": "baz1",
                    "name": "baz1",
                },
                {
                    "id": "baz2",
                    "name": "baz2",
                },
                {
                    "id": "baz3",
                    "name": "baz3",
                },
            ]
        },
    ])
    return conversation_list


@pytest.mark.parametrize(
    ["user_name", "user_id"],
    (
        ["not-existing", None],
        ["foo1", "foo1"],
        ["FOO4", "foo4"],
        ["bar2", "bar2"],
        ["baz3", "baz3"],
    ),
)
def test_get_id_for_user_name(user_name, user_id, slack_bot, slack_user_list):
    slack.iter_cursor = MagicMock(return_value=slack_user_list)
    assert slack_bot.get_id_for_user_name(user_name) == user_id
    slack.iter_cursor.assert_called_once()


def test_cached_get_id_for_user_name(slack_bot, slack_user_list):
    slack.iter_cursor = MagicMock(return_value=slack_user_list)
    slack_bot.get_id_for_user_name("foo1")
    slack_bot.get_id_for_user_name("bar1")
    slack_bot.get_id_for_user_name("baz1")
    slack_bot.get_id_for_user_name("anything")

    slack.iter_cursor.assert_called_once()


@pytest.mark.parametrize(
    ["user_email", "user_id"],
    (
        ["something@example.com", None],
        ["foo1@example.com", "foo1"],
        ["FOO4@example.com", "foo4"],
        ["bar2@example.com", "bar2"],
        ["baz3@example.com", "baz3"],
    ),
)
def test_get_id_for_user_email(user_email, user_id, slack_bot, slack_user_list):
    slack.iter_cursor = MagicMock(return_value=slack_user_list)
    assert slack_bot.get_id_for_user_email(user_email) == user_id
    slack.iter_cursor.assert_called_once()


def test_cached_get_id_for_user_email(slack_bot, slack_user_list):
    slack.iter_cursor = MagicMock(return_value=slack_user_list)
    slack_bot.get_id_for_user_email("foo1@example.com")
    slack_bot.get_id_for_user_email("bar1@example.com")
    slack_bot.get_id_for_user_email("baz1@example.com")
    slack_bot.get_id_for_user_email("anything")

    slack.iter_cursor.assert_called_once()


@pytest.mark.parametrize(
    ["channel_name", "channel_id"],
    (
        ["#not-found", None],
        ["#FOO2", "foo2"],
        ["#Foo3", "foo3"],
        ["#bar4", "bar4"],
        ["#baz2", "baz2"],
    ),
)
def test_get_id_for_channel_name(
    channel_name, channel_id, slack_bot, slack_conversation_list
):
    slack.iter_cursor = MagicMock(return_value=slack_conversation_list)
    assert slack_bot.get_id_for_channel_name(channel_name) == channel_id
    slack.iter_cursor.assert_called_once()


def test_cached_get_id_for_channel_name(slack_bot, slack_conversation_list):
    slack.iter_cursor = MagicMock(return_value=slack_conversation_list)
    slack_bot.get_id_for_channel_name("#foo1")
    slack_bot.get_id_for_channel_name("#bar1")
    slack_bot.get_id_for_channel_name("#baz1")
    slack_bot.get_id_for_channel_name("#anything")

    slack.iter_cursor.assert_called_once()

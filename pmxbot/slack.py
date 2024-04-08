import functools
import importlib
import itertools
import logging
import re
import html
import threading
import time

from tempora import schedule

import pmxbot
from pmxbot import core


log = logging.getLogger(__name__)

DEFAULT_SLACK_CACHE_TTL = 60 * 60 * 4
DEFAULT_SLACK_PAGESIZE = 1000


def iter_cursor(callable, cursor=None):
    """
    Iterate a slack endpoint callable that uses paginated results.
    """
    resp = callable(cursor=cursor)
    yield resp.data
    next_cursor = resp.data.get('response_metadata', {}).get('next_cursor')
    if next_cursor:
        yield from iter_cursor(callable, cursor=next_cursor)


class Bot(pmxbot.core.Bot):
    def __init__(self, token, slack_cache_ttl, slack_pagesize):
        sc = importlib.import_module('slack_sdk.rtm_v2')
        self.slack = sc.RTMClient(token=token)
        self.scheduler = schedule.CallbackScheduler(self.handle_scheduled)
        self.slack_cache_ttl = slack_cache_ttl
        self.slack_pagesize = slack_pagesize

    @classmethod
    def from_config(cls, config):
        slack_cache_ttl = int(
            config.get("slack_cache_ttl")
            if config.get("slack_cache_ttl") is not None
            else DEFAULT_SLACK_CACHE_TTL
        )
        slack_pagesize = int(
            config.get("slack_pagesize")
            if config.get("slack_pagesize") is not None
            else DEFAULT_SLACK_PAGESIZE
        )

        if slack_cache_ttl < 1:
            raise ValueError(
                "Slack cache TTL must be a number greater than or equal to 1"
            )

        if slack_pagesize < 1 or slack_pagesize > 1000:
            raise ValueError("Slack pagesize must be a number between 1 and 1000")

        return cls(
            config['slack token'],
            slack_cache_ttl,
            slack_pagesize,
        )

    @property
    def slack_cache_ttl_key(self):
        return time.time() // self.slack_cache_ttl

    def start(self):
        self.init_schedule(self.scheduler)
        threading.Thread(target=self.run_scheduler_loop).start()

        @self.slack.on("message")
        def handle_payload(client, event):
            self.handle_message(event)

        self.slack.start()

    def run_scheduler_loop(self):
        while True:
            self.scheduler.run_pending()
            time.sleep(0.1)

    def handle_message(self, msg):
        if msg.get('type') != 'message':
            return

        # resolve nick based on message subtype
        # https://api.slack.com/events/message
        method_name = f'_resolve_nick_{msg.get("subtype", "standard")}'
        resolve_nick = getattr(self, method_name, None)
        if not resolve_nick:
            log.debug('Unhandled message %s', msg)
            return
        nick = resolve_nick(msg)

        channel_name = self._get_channel_name(msg['channel'])
        channel = core.AugmentableMessage(
            channel_name, channel_id=msg.get('channel'), thread=msg.get('thread_ts')
        )

        self.handle_action(channel, nick, html.unescape(msg['text']))

    @functools.lru_cache
    def _get_channel_name(self, channel_id):
        return (
            self.slack.web_client.conversations_info(channel=channel_id)
            .data['channel']
            .get('name')
        )

    def _resolve_nick_standard(self, msg):
        return self.slack.web_client.users_info(user=msg['user']).data['user']['name']

    _resolve_nick_me_message = _resolve_nick_standard

    def _resolve_nick_bot_message(self, msg):
        return msg.get('username') or msg.get('bot_id') or 'Anonymous Bot'

    def transmit(self, channel, message):
        """
        Send the message to Slack.

        :param channel: channel, user or email to whom the message should be sent.
            If a ``thread`` attribute is present, that thread ID is used.
        :param str message: message to send.
        """
        message = self._expand_references(message)

        # If this action was generated from a slack message event then we should have
        # the channel_id already. For other cases we need to query the Slack API using
        # the channel name, or the user name or email (for DMs)
        channel_id = (
            getattr(channel, "channel_id", None)
            or self.get_id_for_channel_name(channel)
            or self.get_id_for_user_name(channel)
            or self.get_id_for_user_email(channel)
        )

        if channel_id:
            log.info("Logging to channel " + str(channel_id))
            self.slack.web_client.chat_postMessage(
                channel=channel_id,
                text=message,
                thread_ts=getattr(channel, 'thread', None),
                as_user=True,
            )
        else:
            log.error(f"Failed to resolve a channel ID for: '{channel}'")

    @functools.lru_cache(maxsize=1)
    def _get_channel_mappings(self, _ttl_key):
        convos = functools.partial(
            self.slack.web_client.conversations_list,
            exclude_archived=True,
            limit=self.slack_pagesize,
        )
        return {
            channel['name'].lower(): channel['id']
            for channel in itertools.chain(*[
                convo['channels'] for convo in iter_cursor(convos)
            ])
        }

    @functools.lru_cache(maxsize=1)
    def _get_users_mappings(self, _ttl_key):
        users = functools.partial(
            self.slack.web_client.users_list,
            limit=self.slack_pagesize,
        )
        return [
            {
                "id": user["id"],
                "name": user["name"].lower(),
                "email": user["profile"]["email"].lower()
                if "email" in user["profile"]
                else None,
            }
            for user in itertools.chain(*[
                user_list['members'] for user_list in iter_cursor(users)
            ])
        ]

    def _get_user_name_to_id_mappings(self):
        users = self._get_users_mappings(self.slack_cache_ttl_key)
        return {user["name"]: user["id"] for user in users}

    def _get_user_email_to_id_mappings(self):
        users = self._get_users_mappings(self.slack_cache_ttl_key)
        return {user["email"]: user["id"] for user in users if user.get("email")}

    @functools.lru_cache
    def get_id_for_user_name(self, user_name):
        return self._get_user_name_to_id_mappings().get(user_name.lower())

    @functools.lru_cache
    def get_id_for_user_email(self, user_email):
        return self._get_user_email_to_id_mappings().get(user_email.lower())

    @functools.lru_cache
    def get_id_for_channel_name(self, channel_name):
        channels = self._get_channel_mappings(self.slack_cache_ttl_key)
        return channels.get(channel_name.strip('#').lower())

    def _expand_references(self, message):
        resolvers = {
            '@': self.get_id_for_user_name,
            '#': self.get_id_for_channel_name,
        }

        def _expand(match):
            match_type = match.groupdict()['type']
            match_name = match.groupdict()['name']

            try:
                ref = resolvers[match_type](match_name)
                assert ref is not None
            except Exception:
                # capture any exception, fallback to original text
                log.exception(f"Error resolving slack reference: {message}")
                return match.group(0)

            return f'<{match_type}{ref}>'

        regex = r'(?P<type>[@#])(?P<name>[\w\d\.\-_\|]*)'
        slack_refs = re.compile(regex)
        return slack_refs.sub(_expand, message)

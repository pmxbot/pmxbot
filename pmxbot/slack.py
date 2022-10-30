import functools
import time
import importlib
import logging
import re
import html
import threading
import contextlib

from tempora import schedule

import pmxbot
from pmxbot import core


log = logging.getLogger(__name__)

SLACK_CACHE_SECONDS = 7 * 24 * 60 * 60


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
    def __init__(self, server, port, nickname, channels, password=None):
        token = pmxbot.config['slack token']
        sc = importlib.import_module('slack_sdk.rtm_v2')
        self.slack = sc.RTMClient(token=token)
        self.scheduler = schedule.CallbackScheduler(self.handle_scheduled)

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

    @functools.lru_cache()
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
        # the channel_id already. For other cases we need to query the Slack API
        if getattr(channel, "channel_id", None):
            channel_id = channel.channel_id
        else:
            channel_id = self._get_id_for_channel(channel)

        self.slack.web_client.chat_postMessage(
            channel=channel_id, text=message, thread_ts=getattr(channel, 'thread', None)
        )

    @staticmethod
    def search_dicts(key, dicts):
        """
        Return the value for the first dict in dicts that has key.
        """
        for dict in dicts:
            with contextlib.suppress(KeyError):
                return dict[key]

    def _get_channel_mappings(self):
        convos = functools.partial(
            self.slack.web_client.conversations_list,
            exclude_archived=True,
        )
        return (
            {channel['name']: channel['id'] for channel in convo['channels']}
            for convo in iter_cursor(convos)
        )

    def _get_user_mappings(self):
        users = functools.partial(self.slack.web_client.users_list)
        return (
            {user['name']: user['id'] for user in user_list['members']}
            for user_list in iter_cursor(users)
        )

    @functools.lru_cache()
    def _get_id_for_user(self, user_name):
        return self.search_dicts(user_name, self._get_user_mappings())

    @functools.lru_cache()
    def _get_id_for_channel(self, channel_name):
        return self.search_dicts(channel_name.strip('#'), self._get_channel_mappings())

    def _expand_references(self, message):
        resolvers = {'@': self._get_id_for_user, '#': self._get_id_for_channel}

        def _expand(match):
            match_type = match.groupdict()['type']
            match_name = match.groupdict()['name']

            try:
                ref = resolvers[match_type](match_name)
                assert ref is not None
            except Exception:
                # capture any exception, fallback to original text
                log.exception("Error resolving slack reference: {}".format(message))
                return match.group(0)

            return f'<{match_type}{ref}>'

        regex = r'(?P<type>[@#])(?P<name>[\w\d\.\-_\|]*)'
        slack_refs = re.compile(regex)
        return slack_refs.sub(_expand, message)

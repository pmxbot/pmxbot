import functools
import time
import importlib
import logging
import re
import html
import threading

from tempora import schedule

import pmxbot
from pmxbot import core


log = logging.getLogger(__name__)

SLACK_CACHE_SECONDS = 7 * 24 * 60 * 60


def get_ttl_hash(seconds=None):
    """
    Return the same value withing `seconds` time period

    default seconds:
        7 days == 7days*24hours*60min*60seconds == 604800 seconds

    Cache time can be configured in config using `slack_cache` in seconds
    """
    if not seconds:
        try:
            seconds = pmxbot.config.get('slack_cache', SLACK_CACHE_SECONDS)
        except AttributeError:
            # whenever pmxbot doesn't have config
            seconds = SLACK_CACHE_SECONDS
    return round(time.time() / seconds)


class Bot(pmxbot.core.Bot):
    def __init__(self, server, port, nickname, channels, password=None):
        token = pmxbot.config['slack token']
        sc = importlib.import_module('slack_sdk.rtm_v2')
        self.slack = sc.RTMClient(token=token)
        sr = importlib.import_module('slacker')
        self.slacker = sr.Slacker(token)

        self.scheduler = schedule.CallbackScheduler(self.handle_scheduled)
        # Store in cache users on init
        self.get_email_username_map(
            ttl_hash=get_ttl_hash(pmxbot.config.get('slack_cache'))
        )

    @functools.lru_cache(maxsize=1)
    def get_email_username_map(self, ttl_hash=get_ttl_hash()):
        """
        Generate a map {email -> slack username}

        :param ttl_hash: hash to control the lru_cache
        """
        users = self.slacker.users.list()
        if users.body.get('ok', False):
            members = users.body.get('members', [])
            return {
                member.get('profile', {}).get('email', ""): member.get("name")
                for member in members
            }

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
            time.sleep(1)

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

        channel_name = (
            self.slacker.conversations.info(msg['channel'])
            .body.get('channel', {})
            .get('name')
        )
        channel = core.AugmentableMessage(
            channel_name, channel_id=msg.get('channel'), thread=msg.get('thread_ts')
        )

        self.handle_action(channel, nick, html.unescape(msg['text']))

    def _resolve_nick_standard(self, msg):
        return self.slacker.users.info(msg['user']).body['user']['name']

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
        channel_id = self._get_channel_id(channel)
        self.slack.web_client.chat_postMessage(
            channel=channel_id, text=message, thread_ts=getattr(channel, 'thread', None)
        )

    @functools.lru_cache()
    def _get_channel_id(self, channel):
        # If this action was generated from a slack message event then we should have
        # the channel_id already. For other cases we need to query the Slack API to get
        # the channel id
        if getattr(channel, "channel_id", None):
            return channel.channel_id

        channel_name = channel.strip('#')
        cursor = None
        while True:
            resp = self.slacker.conversations.list(cursor=cursor, exclude_archived=True)
            if not resp.successful:
                log.error('Failed calls to conversations.list')
                return None
            cursor = resp.body['response_metadata']['next_cursor']
            chan_mapping = dict([(x['name'], x['id']) for x in resp.body['channels']])
            if channel_name in chan_mapping:
                return chan_mapping[channel_name]
            if not cursor:
                break

    def _expand_references(self, message):
        resolvers = {
            '@': self.slacker.users.get_user_id,
            '#': self.slacker.channels.get_channel_id,
        }

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

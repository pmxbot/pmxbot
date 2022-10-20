import functools
import time
import importlib
import os
import logging
import html

from tempora import schedule

import pmxbot
from pmxbot import core

import slacker

# monkey patch slacker _request to send the auth header
slacker.DEFAULT_RETRIES = 1

import requests
from slacker import Error, Response, DEFAULT_WAIT, get_api_url


class SlackerMonkey(slacker.BaseAPI):
    def _request(self, request_method, method, **kwargs):
        #if self.token:
        #    kwargs.setdefault('params', {})['token'] = self.token

        url = get_api_url(method)

        # while we have rate limit retries left, fetch the resource and back
        # off as Slack's HTTP response suggests
        for retry_num in range(self.rate_limit_retries):
            response = request_method(
                url, timeout=self.timeout, proxies=self.proxies,
                headers={'Authorization': 'Bearer {}'.format(self.token)},
            **kwargs
            )

            if response.status_code == requests.codes.ok:
                break
            # handle HTTP 429 as documented at
            # https://api.slack.com/docs/rate-limits
            if response.status_code == requests.codes.too_many:
                time.sleep(int(
                    response.headers.get('retry-after', DEFAULT_WAIT)
                ))
                continue
            response.raise_for_status()
        else:
            # with no retries left, make one final attempt to fetch the
            # resource, but do not handle too_many status differently
            response = request_method(
                url, timeout=self.timeout, proxies=self.proxies,
                headers = {'Authorization': 'Bearer {}'.format(self.token)},
                **kwargs
            )
            response.raise_for_status()
        response = Response(response.text)
        if not response.successful:
            raise Error(response.error)
        return response

slacker.BaseAPI._request = SlackerMonkey._request

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
        token = os.environ.get("SLACK_TOKEN", pmxbot.config.get('slack token'))
        sc = importlib.import_module('slackclient')
        self.slack = sc.SlackClient(token)
        self.slacker = slacker.Slacker(token)

        self.scheduler = schedule.CallbackScheduler(self.handle_scheduled)
        # Store in cache users on init
        self.get_email_username_map(
            ttl_hash=get_ttl_hash(pmxbot.config.get('slack_cache'))
        )

        self.recache_channels()

    def recache_channels(self):
        # cache all the slack channels that pmxbot uses
        convos = self.slack.api_call("conversations.list",
                                     types="public_channel,private_channel,mpim,im",
                                     limit=1000)
        self.slack.server.parse_channel_data(convos["channels"])

    def get_channel(self, channel):
        channel = self.slack.server.channels.find(channel)
        if channel is None:
            # try to get the channel listing again
            self.recache_channels()
            channel = self.slack.server.channels.find(channel)
        if channel is None:
            log.error("Unknown channel", channel)
        return channel

    @functools.lru_cache(maxsize=1)
    def get_id_username_map(self, ttl_hash=get_ttl_hash()):
        users = self.slacker.users.list()

        if users.body.get('ok', False):
            members = users.body.get('members', [])
            mems = {
                member.get('id'): member.get("name")
                for member in members
            }
            return mems

    @property
    def users_by_id(self):
        return self.get_id_username_map()

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
        res = self.slack.rtm_connect(with_team_state=False)
        assert res, "Error connecting"
        self.init_schedule(self.scheduler)
        while True:
            for msg in self.slack.rtm_read():
                self.handle_message(msg)
            self.scheduler.run_pending()
            time.sleep(0.1)

    def handle_message(self, msg):
        if msg.get('type') != 'message':
            return
        if msg.get('subtype') == 'message_changed':
            # Pay attention to the revised message
            channel = msg["channel"]
            msg = msg["message"]
            msg["channel"] = channel
            msg['user'] = msg.get('user', msg['user'])
            msg['text'] = msg.get('text', msg['text'])

        # resolve nick based on message subtype
        # https://api.slack.com/events/message
        method_name = f'_resolve_nick_{msg.get("subtype", "standard")}'
        resolve_nick = getattr(self, method_name, None)

        if not resolve_nick:
            log.info('Unhandled message %s', msg)
            return
        nick = resolve_nick(msg)

        channel = self.get_channel(msg["channel"])

        if channel is None:
            return

        channel = core.AugmentableMessage(channel.name, thread=msg.get('thread_ts'))

        content = msg.get('text')
        if not content and len(msg.get('attachments')):
            att = msg['attachments'][0]
            content = att.get('fallback') or att.get('pretext') or att.get('title')
            if 'fields' in att:
                field_data = ['%s:%s' % (f['title'], f['value']) for f in att['fields']]
                content += '; %s' % "; ".join(field_data)

        self.handle_action(channel, nick, html.unescape(content))

    def _resolve_nick_standard(self, msg):
        return self.users_by_id[msg["user"]]

    _resolve_nick_me_message = _resolve_nick_standard
    _resolve_nick_channel_join = _resolve_nick_standard
    _resolve_nick_slackbot_response = _resolve_nick_standard

    def _resolve_nick_bot_message(self, msg):
        return msg.get('username') or msg.get('bot_id') or 'Anonymous Bot'

    def _find_user_channel(self, username):
        """
        Use slacker to resolve the username to an opened IM channel
        """
        user_id = self.slacker.users.get_user_id(username)
        im = user_id and self.slacker.im.open(user_id).body['channel']['id']
        return im and self.slack.server.channels.find(im)

    def transmit(self, channel, message):
        """
        Send the message to Slack.

        :param channel: channel, user or email to whom the message should be sent.
            If a ``thread`` attribute is present, that thread ID is used.
        :param str message: message to send.
        """
        target = (
            self.slack.server.channels.find(channel)
            or self._find_user_channel(username=channel)
            or self._find_user_channel(
                username=self.get_email_username_map().get(channel)
            )
        )
        if message.startswith("/me "):
            # Hack: just make them italicized, looks the same to slack ;)
            message = "_" + message[4:] + "_"

        target.send_message(message, thread=getattr(channel, 'thread', None))

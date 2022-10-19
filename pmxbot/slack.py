import functools
import time
import importlib
import logging
import re
import html

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
        sc = importlib.import_module('slackclient')
        self.slack = sc.SlackClient(token)
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
        res = self.slack.rtm_connect()
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
            msg['user'] = msg.get('user', msg['user'])
            msg['text'] = msg.get('text', msg['text'])

        # resolve nick based on message subtype
        # https://api.slack.com/events/message
        method_name = f'_resolve_nick_{msg.get("subtype", "standard")}'
        resolve_nick = getattr(self, method_name, None)
        if not resolve_nick:
            log.debug('Unhandled message %s', msg)
            return
        nick = resolve_nick(msg)

        channel = self.slack.server.channels.find(msg['channel']).name
        channel = core.AugmentableMessage(channel, thread=msg.get('thread_ts'))

        content = msg.get('text')
        if not content and len(msg.get('attachments')):
            att = msg['attachments'][0]
            content = att.get('fallback') or att.get('pretext') or att.get('title')
            if 'fields' in att:
                field_data = ['%s:%s' % (f['title'], f['value']) for f in att['fields']]
                content += '; %s' % "; ".join(field_data)

        self.handle_action(channel, nick, html.unescape(content))

    def _resolve_nick_standard(self, msg):
        return self.slack.server.users.find(msg['user']).name

    _resolve_nick_me_message = _resolve_nick_standard

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
        message = self._expand_references(message)
        if message.startswith("/me "):
            # Hack: just make them italicized, looks the same to slack ;)
            message = "_" + message[4:] + "_"

        target.send_message(message, thread=getattr(channel, 'thread', None))

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

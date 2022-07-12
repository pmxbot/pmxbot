import re

import yaml

import pmxbot
from pmxbot.core import command


@command()
def config(client, event, channel, nick, rest):
    "Change the running config, something like a=b or a+=b or a-=b"
    pattern = re.compile(r'(?P<key>\w+)\s*(?P<op>[+-]?=)\s*(?P<value>.*)$')
    match = pattern.match(rest)
    if not match:
        return "Command not recognized"
    res = match.groupdict()
    key = res['key']
    op = res['op']
    value = yaml.safe_load(res['value'])
    if op in ('+=', '-='):
        # list operation
        op_name = {'+=': 'append', '-=': 'remove'}[op]
        op_name
        if key not in pmxbot.config:
            return f"{key} not found in config. Can't {op_name}."
        if not isinstance(pmxbot.config[key], (list, tuple)):
            return f"{key} is not list or tuple. Can't {op_name}."
        op = getattr(pmxbot.config[key], op_name)
        op(value)
    else:  # op is '='
        pmxbot.config[key] = value

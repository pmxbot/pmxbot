"""
System commands
"""

import sys
import operator
import io
import time

import importlib_resources

import pmxbot.core
from pmxbot.core import command, Handler


@command(aliases='h')
def help(rest):
    """Help (this command)"""
    rs = rest.strip()
    if rs:
        # give help for matching commands
        for handler in Handler._registry:
            if handler.name == rs.lower():
                yield '!%s: %s' % (handler.name, handler.doc)
                break
        else:
            yield "command not found"
        return

    # give help for all commands
    def mk_entries():
        handlers = (
            handler
            for handler in Handler._registry
            if type(handler) is pmxbot.core.CommandHandler
        )
        handlers = sorted(handlers, key=operator.attrgetter('name'))
        for handler in handlers:
            res = "!" + handler.name
            if handler.aliases:
                alias_names = (alias.name for alias in handler.aliases)
                res += " (%s)" % ', '.join(alias_names)
            yield res

    o = io.StringIO(" ".join(mk_entries()))
    more = o.read(160)
    while more:
        yield more
        time.sleep(0.3)
        more = o.read(160)


@command(aliases=('controlaltdelete', 'controlaltdelete', 'cad', 'restart', 'quit'))
def ctlaltdel(rest):
    """Quits pmxbot. A supervisor should automatically restart it."""
    if 'real' in rest.lower():
        sys.exit()
    return "Really?"


@command()
def logo():
    """
    The pmxbot logo in ascii art.  Fixed-width font recommended!

    >>> from more_itertools import consume
    >>> consume(map(print, logo()))
                                                    MI=7+MM .M:
                                                 M=..        .M M
    ...
    """
    logo_txt = importlib_resources.files('pmxbot').joinpath('asciilogo.txt').read_text()
    for line in logo_txt.splitlines():
        yield line.rstrip()

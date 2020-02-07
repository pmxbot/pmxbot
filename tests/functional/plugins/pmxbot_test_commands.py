from pmxbot import core


@core.command("crashnow")
def crash_immediately():
    "Crash now!"
    raise TypeError("You should never call this!")


@core.command("crashiter")
def crash_in_iterator():
    "Crash in iterator!"
    raise TypeError("You should never call this!")
    yield "You can't touch this"


@core.regexp('feck', r'\bfeck\b', doc="We don't use that sort of language around here")
def foobar(client, event, channel, nick, match):
    if match:
        return "Clean up your language %s" % nick


@core.command()
def echo(rest):
    "echo"
    return rest

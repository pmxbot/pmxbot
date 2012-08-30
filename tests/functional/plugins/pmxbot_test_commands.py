from pmxbot import core

@core.command("crashnow", doc="Crash now!")
def crash_immediately(client, event, channel, nick, rest):
	raise TypeError("You should never call this!")

@core.command("crashiter", doc="Crash in iterator!")
def crash_in_iterator(client, event, channel, nick, rest):
	raise TypeError("You should never call this!")
	yield "You can't touch this"

@core.command("echo", doc="echo")
def echo(client, event, channel, nick, rest):
	return rest

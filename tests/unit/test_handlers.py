from pmxbot import core

def test_contains_always_match():
	"""
	Contains handler should always match if no rate is specified.
	"""
	handler = core.ContainsHandler(name='#', func=None)
	assert handler.match('Tell me about #foo', channel='bar')

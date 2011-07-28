import re

from pmxbot import popquotes
from pmxbot import botbase

quote_pattern = re.compile('\(\d+/\d+\): .+')

def test_bender():
	res = popquotes.bartletts('bender', 'somenick', '')
	assert res is not None
	assert quote_pattern.match(res)

def test_registered():
	handlers = botbase._handler_registry
	all_names = [handler[1] for handler in handlers]
	assert 'bender' in all_names

import re

from pmxbot import popquotes

quote_pattern = re.compile('\(\d+/\d+\): .+')

def test_bender():
	res = popquotes.bartletts('bender', 'somenick', '')
	assert res is not None
	assert quote_pattern.match(res)

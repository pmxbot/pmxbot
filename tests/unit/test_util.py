from pmxbot import util


def test_lookup(needs_wordnik):
	assert util.lookup('dachshund') is not None


def test_emergency_compliment(needs_internet):
	assert util.load_emergency_compliments()


def test_acronym_lookup(needs_internet):
	assert util.lookup_acronym('NSFW')

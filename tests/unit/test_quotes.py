from pmxbot import quotes


def test_MongoDBQuotes(mongodb_uri):
	q = quotes.Quotes.from_URI(mongodb_uri)
	q.lib = 'test'
	clean = lambda: q.db.remove({'library': 'test'})
	clean()
	try:
		q.quoteAdd('who would ever say such a thing')
		q.quoteAdd('go ahead, take my pay')
		q.quoteAdd("let's do the Time Warp again")
		q.quoteLookup('time warp')
		q.quoteLookup('nonexistent')
	finally:
		clean()

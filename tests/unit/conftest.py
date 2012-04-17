import py.test

def pytest_funcarg__mongodb_uri(request):
	test_host = 'mongodb://localhost'
	try:
		import pymongo
		pymongo.Connection(test_host)
	except Exception:
		py.test.skip("No local mongodb found")
	return test_host

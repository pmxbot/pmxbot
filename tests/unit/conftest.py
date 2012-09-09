import py.test
from jaraco.test import services

def mongodb_instance():
	try:
		import pymongo
		instance = services.MongoDBInstance()
		instance.log_root = ''
		instance.start()
		pymongo.Connection(instance.get_connect_hosts())
	except Exception:
		return None
	return instance

def pytest_funcarg__mongodb_uri(request):
	instance = request.cached_setup(setup=mongodb_instance, scope='session',
		teardown=lambda instance: instance.stop() if instance else None)
	if not instance:
		py.test.skip("MongoDB not available")
	return 'mongodb://' + ','.join(instance.get_connect_hosts())

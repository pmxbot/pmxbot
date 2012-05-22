# copied from jaraco.util.timing
from __future__ import unicode_literals

import datetime

class Stopwatch(object):
	"""
	A simple stopwatch which starts automatically.

	>>> w = Stopwatch()
	>>> _1_sec = datetime.timedelta(seconds=1)
	>>> w.split() < _1_sec
	True
	>>> import time
	>>> time.sleep(1.0)
	>>> w.split() >= _1_sec
	True
	>>> w.stop() >= _1_sec
	True
	>>> w.reset()
	>>> w.start()
	>>> w.split() < _1_sec
	True
	"""
	def __init__(self):
		self.reset()
		self.start()

	def reset(self):
		self.elapsed = datetime.timedelta(0)
		if hasattr(self, 'start_time'):
			del self.start_time

	def start(self):
		self.start_time = datetime.datetime.now()

	def stop(self):
		stop_time = datetime.datetime.now()
		self.elapsed += stop_time - self.start_time
		del self.start_time
		return self.elapsed

	def split(self):
		local_duration = datetime.datetime.now() - self.start_time
		return self.elapsed + local_duration

	# context manager support
	__enter__ = start

	def __exit__(self, exc_type, exc_value, traceback):
		self.stop()

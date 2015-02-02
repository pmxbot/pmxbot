import abc

import pmxbot
from pmxbot import storage

class ChannelList(storage.SelectableStorage, list):
	"""
	Channel list, persisted to a storage layer.
	"""
	_finalizers = []

	@classmethod
	def initialize(cls):
		for aspect in 'member', 'log':
			cls._initialize_aspect(aspect)

	@classmethod
	def _initialize_aspect(cls, aspect):
		key = aspect + ' channels'
		store = cls.from_URI(pmxbot.config.database)
		store.aspect = aspect
		store.load()
		store._compat_load(aspect)
		pmxbot.config[key] = store
		cls._finalizers.append(store.finalize)

	def finalize(self):
		key = self.aspect + ' channels'
		del pmxbot.config[key]

	def _compat_load(self):
		"""
		Older versions of pmxbot would store config in 'log_channels' and
		'other_channels'. Support those keys.
		"""
		if self.items:
			return

		legacy_values = pmxbot.config.get('log_channels', [])
		if self.aspect == 'member':
			legacy_values += pmxbot.config.get('other_channels', [])
		self[:] = legacy_values

	@abc.abstractmethod
	def load(self):
		"""
		Load the list of channels from the db. Sets items on self.
		"""

	@abc.abstractmethod
	def save(self):
		"""
		Save the list of channels back to the db.
		"""

	# override MutableSequence methods to persist changes
	def __setitem__(self, *args, **kwargs):
		super().__setitem__(*args, **kwargs)
		self.save()

	def __delitem__(self, *args, **kwargs):
		super().__delitem__(*args, **kwargs)
		self.save()

	def insert(self, *args, **kwargs):
		super().insert(*args, **kwargs)
		self.save()

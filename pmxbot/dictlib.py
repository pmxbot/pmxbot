import yaml
from jaraco.util.dictlib import ItemsAsAttributes

class ConfigDict(ItemsAsAttributes, dict):
	@classmethod
	def from_yaml(cls, filename):
		with open(filename) as f:
			return cls(yaml.load(f))

	def to_yaml(self, filename):
		with open(filename, 'wb') as f:
			yaml.dump(self, f)

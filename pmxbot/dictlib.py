import yaml
from jaraco.collections import ItemsAsAttributes


class ConfigDict(ItemsAsAttributes, dict):
	@classmethod
	def from_yaml(cls, filename):
		with open(filename) as f:
			return cls(yaml.load(f))

	def to_yaml(self, filename):
		dumper = getattr(yaml, 'danger_dump', yaml.dump)
		with open(filename, 'w') as f:
			dumper(self, f)

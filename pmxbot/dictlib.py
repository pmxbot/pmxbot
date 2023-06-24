import yaml
from jaraco.collections import ItemsAsAttributes


class ConfigDict(ItemsAsAttributes, dict):
    @classmethod
    def from_yaml(cls, filename):
        with open(filename, encoding='utf-8') as f:
            return cls(yaml.safe_load(f))

    def to_yaml(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            yaml.safe_dump(dict(self), f)

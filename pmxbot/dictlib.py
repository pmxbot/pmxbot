from __future__ import unicode_literals

import yaml

# from jaraco.util.dictlib
class ItemsAsAttributes(object):
	"""
	Mix-in class to enable a mapping object to provide items as
	attributes.

	>>> C = type(str('C'), (dict, ItemsAsAttributes), dict())
	>>> i = C()
	>>> i['foo'] = 'bar'
	>>> i.foo
	u'bar'

	# natural attribute access takes precedence
	>>> i.foo = 'henry'
	>>> i.foo
	u'henry'

	# but as you might expect, the mapping functionality is preserved.
	>>> i['foo']
	u'bar'

	# A normal attribute error should be raised if an attribute is
	#  requested that doesn't exist.
	>>> i.missing
	Traceback (most recent call last):
	...
	AttributeError: 'C' object has no attribute 'missing'

	It also works on dicts that customize __getitem__
	>>> missing_func = lambda self, key: 'missing item'
	>>> C = type(str('C'), (dict, ItemsAsAttributes), dict(__missing__ = missing_func))
	>>> i = C()
	>>> i.missing
	u'missing item'
	>>> i.foo
	u'missing item'
	"""
	def __getattr__(self, key):
		try:
			return getattr(super(ItemsAsAttributes, self), key)
		except AttributeError as e:
			# attempt to get the value from the mapping (return self[key])
			#  but be careful not to lose the original exception context.
			noval = object()
			def _safe_getitem(cont, key, missing_result):
				try:
					return cont[key]
				except KeyError:
					return missing_result
			result = _safe_getitem(self, key, noval)
			if result is not noval:
				return result
			# raise the original exception, but use the original class
			#  name, not 'super'.
			e.message = e.message.replace('super',
				self.__class__.__name__, 1)
			e.args = (e.message,)
			raise

class ConfigDict(ItemsAsAttributes, dict):
	@classmethod
	def from_yaml(cls, filename):
		with open(filename) as f:
			return cls(yaml.load(f))


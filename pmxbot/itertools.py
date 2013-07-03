import io

import six

def always_iterable(item):
	r"""
	Given an item from a pmxbot handler, always return an iterable.

	If the item is None, return an empty iterable.
	>>> list(always_iterable(None))
	[]

	If the item is a string, return an iterable of the lines in the string.
	>>> print('/'.join(always_iterable('foo')))
	foo
	>>> print('/'.join(always_iterable('foo\nbar')))
	foo/bar

	>>> list(always_iterable([1,2,3]))
	[1, 2, 3]

	>>> always_iterable(iter('abc'))  # doctest: +ELLIPSIS
	<...iterator ...>

	And any other non-iterable objects are returned as single-tuples of that
	item.
	>>> list(always_iterable(object()))  # doctest: +ELLIPSIS
	[<object object at ...>]
	"""
	if item is None:
		item = ()

	if isinstance(item, six.string_types):
		item = (line.rstrip('\n') for line in io.StringIO(six.text_type(item)))

	if not hasattr(item, '__iter__'):
		item = item,

	return item

def generate_results(function):
	"""
	Take a function, which may return an iterator or a static result
	and convert it to a late-dispatched generator.
	"""
	for item in always_iterable(function()):
		yield item

def trap_exceptions(results, handler, exceptions=Exception):
	"""
	Iterate through the results, but if an exception occurs, stop
	processing the results and instead replace
	the results with the output from the exception handler.
	"""
	try:
		for result in results:
			yield result
	except exceptions as exc:
		for result in always_iterable(handler(exc)):
			yield result

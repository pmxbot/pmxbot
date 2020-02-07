from jaraco.itertools import always_iterable


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

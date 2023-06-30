from jaraco.itertools import always_iterable


def generate_results(function):
    """
    Take a function, which may return an iterator or a static result
    and convert it to a late-dispatched generator.
    """
    yield from always_iterable(function())


def trap_exceptions(results, handler, exceptions=Exception):
    """
    Iterate through the results, but if an exception occurs, stop
    processing the results and instead replace
    the results with the output from the exception handler.
    """
    try:
        yield from results
    except exceptions as exc:
        yield from always_iterable(handler(exc))

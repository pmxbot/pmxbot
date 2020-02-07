from pmxbot import core


def test_contains_always_match():
    """
    Contains handler should always match if no rate is specified.
    """
    handler = core.ContainsHandler(name='#', func=None)
    assert handler.match('Tell me about #foo', channel='bar')


def test_contains_rate_limit():
    """
    Contains handler with a rate should only appear sometimes.
    """
    handler = core.ContainsHandler(name='#', func=None, rate=0.5)
    results = set(
        handler.match('Tell me about #foo', channel='bar') for x in range(1000)
    )
    assert True in results and False in results

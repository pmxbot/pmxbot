from unittest import mock

import pmxbot.config_


@mock.patch('pmxbot.config', {})
def test_config_append():
    """
    += should append an item to a list
    """
    pmxbot.config['foo'] = []
    text = 'foo += {"a": 3, "b": foo}'
    pmxbot.config_.config(None, None, None, None, text)
    assert pmxbot.config['foo'][0] == {'a': 3, 'b': 'foo'}

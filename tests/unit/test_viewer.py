import pmxbot.web.viewer


def test_get_context():
    """
    Calling get_context should return a dictionary.
    """
    pmxbot.web.viewer.init_config()
    assert isinstance(pmxbot.web.viewer.HelpPage.get_context(), dict)

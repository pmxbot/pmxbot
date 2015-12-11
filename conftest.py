import pmxbot.config_


# This test must be in the root directory.
def pytest_addoption(parser):
	parser.addoption("--runslow", action="store_true", help="run slow tests")


def pytest_configure():
	pmxbot.config_.initialize({})

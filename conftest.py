import pytest


@pytest.fixture(scope='session', autouse=True)
def init_config():
	__import__('pmxbot').config = {}

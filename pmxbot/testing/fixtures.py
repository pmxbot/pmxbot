import pytest


@pytest.fixture(scope='session', autouse=True)
def init_config():
    __import__('pmxbot').config = {}


@pytest.fixture(params=['mongodb', 'sqlite'])
def db_uri(request):
    if request.param == 'mongodb':
        return request.getfixturevalue('mongodb_uri')
    return 'sqlite:pmxbot.sqlite'

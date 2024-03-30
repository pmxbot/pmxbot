import importlib

import pmxbot.storage


def run():
    # load the storage classes so the migration routine will find them.
    for mod in ('pmxbot.logging', 'pmxbot.karma', 'pmxbot.quotes', 'pmxbot.rss'):
        importlib.import_module(mod)
    pmxbot.storage.migrate_all('sqlite:pmxbot.sqlite', 'mongodb://localhost')


if __name__ == '__main__':
    run()

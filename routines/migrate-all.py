from pmxbot import logging
from pmxbot import util
from pmxbot import rss
from pmxbot import storage
storage.migrate_all('sqlite:pmxbot.sqlite', 'mongodb://localhost')

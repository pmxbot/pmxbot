import os
from unittest import TestCase

import pmxbot
from pmxbot import core

class TestHandler(TestCase):
    @classmethod
    def setup_class(cls):                                                                 
        path = os.path.dirname(os.path.abspath(__file__))
        configfile = os.path.join(path, 'testconf.yaml')                                  
        config = pmxbot.dictlib.ConfigDict.from_yaml(configfile)                          
        cls.bot = core.initialize(config)
        pmxbot.config.update(config)

    @classmethod
    def teardown_class(cls):
        path = os.path.dirname(os.path.abspath(__file__))
        try:
            os.remove(os.path.join(path, 'pmxbot.sqlite'))
        except:
            pass



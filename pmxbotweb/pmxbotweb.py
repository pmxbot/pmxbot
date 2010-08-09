#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim:ts=4:sw=4:noexpandtab
"""
pmxbotweb.py

s
"""

import sys
import os
import yaml
import cherrypy
from viewer import PmxbotPages

def run(configFile=None, configDict=None, start=True):
	global config
	class O(object): 
		def __init__(self, d):
			for k, v in d.iteritems():
			    setattr(self, k, v)

	if configDict:
        config = O(configDict)
	else:
	    if configFile:
    	    config_file = configFile
        else:
    	    if len(sys.argv) < 2:
        		sys.stderr.write("error: need config file as first argument")
        		raise SystemExit(1)
        	config_file = sys.argv[1]
	    config = O(yaml.load(open(config_file)))
    try:
		if config.web_base and config.web_base[0] != '/':
        	config.web_base = '/%s' % config.web_base
	except AttributeError:
		config.web_base = '/'
	try:
		config.web_host
	except AttributeError:
		config.web_host = '0.0.0.0'
	try:
		config.web_port
	except AttributeError:
		config.web_port = 8080

    # Cherrypy configuration here
    app_conf = {
        'global': {
            'server.socket_port': config.web_port,
            'server.socket_host': config.web_host,
        },
        'db' : {'database' : os.path.join(config.database_dir, 'pmxbot.sqlite')},
		'botconf' : {'config' : config},
    }

    cherrypy.quickstart(PmxbotPages(), config.web_base, config=app_conf)

if __name__ == '__main__':
    '''Useful for development mode'''
    run()



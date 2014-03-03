#!/usr/bin/python
# -*- coding: utf-8 -*-

##BP

import logging

from flask.ext.script import Server
from pybble.manager import Manager
from pybble import create_app, ROOT_NAME
from pybble.core.db import db

#from flask.ext.collect import Collect
#from quokka import create_app
#from quokka.core.db import db
#from quokka.ext.blueprints import load_blueprint_commands

def create_app_and_log(logging=False,**kv):
	if logging:
		logging.basicConfig(
			level=getattr(logging, app.config.get("LOGGER_LEVEL", "DEBUG")),
			format=app.config.get(
				"LOGGER_FORMAT",
				'%(asctime)s %(name)-12s %(levelname)-8s %(message)s'),
			datefmt=app.config.get("LOGGER_DATE_FORMAT", '%d.%m %H:%M:%S')
		)
	return create_app(**kv)

manager = Manager(create_app_and_log)
manager.add_option("-c", "--config", dest="config", required=False, default='local_settings', help="Config file to use")
manager.add_option("-s", "--site", dest="site", required=False, default=ROOT_NAME, help="which Site to run on")
manager.add_option("-v", "--verbose", dest="logging", required=False, default=False, help="Enable verbose logging")
manager.add_option("-t", "--test", dest="test", required=False, default=False, help="Use the test database")

#collect = Collect()
#collect.init_script(manager)


@manager.shell
def make_shell_context():
	" Update shell. "
	return dict(app=manager.app, db=db)


@manager.command
def check():
	"""Prints app status"""
	from flask import current_app
	app = current_app

	from pprint import pprint
	print("App:",)
	print str(app)
	print("Extensions:")
	pprint(app.extensions)
	print("Modules:")
	pprint(app.blueprints)


#@manager.command
#def populate():
#	"""Populate the database with sample data"""
#	from quokka.utils.populate import Populate
#	Populate(db)()
#
#
#@manager.command
#def show_config():
#	"print all config variables"
#	from pprint import pprint
#	print("Config.")
#	pprint(dict(app.config))
#
#manager.add_command("run0", Server(
#	use_debugger=True,
#	use_reloader=True,
#	host='0.0.0.0',
#	port=8000
#))

#load_blueprint_commands(manager)

if __name__ == '__main__':
	manager.run()

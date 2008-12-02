#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug import script
import settings
from werkzeug.debug import DebuggedApplication

def res(x):
	def r():
		return x
	return r

def make_app():
	from pybble.application import Pybble
	app = Pybble('sqlite:///'+settings.DATABASE_FILE)
	return app

def make_shell():
	from pybble import models, utils
	application = make_app()
	return locals()

action_runserver = script.make_runserver(
	res(DebuggedApplication(make_app(), evalex=True, show_hidden_frames=True)),
	use_reloader=True)
action_shell = script.make_shell(make_shell)
action_initdb = make_app().init_database()
action_initsite = make_app().init_site()
action_initsite_replace = make_app().init_site_replace()
action_showdb = make_app().show_database()

script.run()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug import script
from pybble import _settings as settings
from werkzeug.debug import DebuggedApplication
from pybble.utils import all_addons

import sys
if "pdb" in sys.modules:
	settings.SERVER_RELOAD = False

def res(x):
	def r():
		return x
	return r

def make_app():
	from pybble.application import Pybble
	return Pybble()

def make_shell():
	from pybble import models, utils
	application = make_app()
	return locals()

app = make_app()
if settings.SERVER_DEBUG:
	app = DebuggedApplication(app, evalex=True, show_hidden_frames=True)
action_runserver = script.make_runserver(res(app), use_reloader=settings.SERVER_RELOAD)
action_shell = script.make_shell(make_shell)
action_initdb = make_app().init_database()
action_initsite = make_app().init_site()
action_initsite_replace = make_app().init_site_replace()
action_trigger = make_app().trigger()
action_dbscript = make_app().dbscript()
action_show = make_app().show()
action_dump = make_app().dump()

for addon in all_addons():
	for a,b in addon.__dict__.iteritems():
		if a.startswith("action_") and a in addon.__ALL__:
			globals()[a]=b

script.run()

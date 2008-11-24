#!/usr/bin/env python
# -*- coding: utf-8 -*-

from werkzeug import script
import settings

def make_app():
    from pybble.application import Pybble
    return Pybble('sqlite:///'+settings.DATABASE_FILE)

def make_shell():
    from pybble import models, utils
    application = make_app()
    return locals()

action_runserver = script.make_runserver(make_app, use_reloader=False)
action_shell = script.make_shell(make_shell)
action_initdb = make_app().init_database()
action_initsite = make_app().init_site()
action_initsite_replace = make_app().init_site_replace()
action_showdb = make_app().show_database()

script.run()

#!/usr/bin/env python
from werkzeug import script

def make_app():
    from pybble.application import Pybble
    return Pybble('sqlite:////tmp/shorty.db')

def make_shell():
    from pybble import models, utils
    application = make_app()
    return locals()

action_runserver = script.make_runserver(make_app, use_reloader=True)
action_shell = script.make_shell(make_shell)
action_initdb = lambda: make_app().init_database()
action_showdb = lambda: make_app().show_database()

script.run()

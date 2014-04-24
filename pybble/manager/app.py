#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

import os
import sys

from flask import Flask

from . import Manager,Command,Option
from ..app import list_apps

class _fake_app(Flask):
	"""
	This class is only used to load the configuration
	and for initial database access
	"""
	pass

class AppCommand(Command):
	"""Runs app-specific commands"""
	capture_all_args = True
	add_help = False

	def __init__(self):
		super(AppCommand,self).__init__()
		self.add_option(Option("-h","--help", dest="help",action="store_true"))

	def __call__(self,app,args, help=False, **kwargs):
		mgr = Manager(app)
		app.init_manager(mgr)
		mgr.handle("manage.py app",args)


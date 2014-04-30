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

import sys
from flask import Flask
from flask.ext.script import Manager as BaseManager
from flask.ext.script import Command,Option # used by pybble.manager.main

class Manager(BaseManager):
	def add_default_commands(self):
		"""NO we do NOT want the default stuff!"""
		pass

class PrepCommand(Command):
	def __call__(self,app,*a,**k):
		with app.test_request_context():
			app.preprocess_request()
			return self.run(*a,**k)

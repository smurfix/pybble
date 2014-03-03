# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

import sys
from flask import Flask
from flask.ext.script import Manager as BaseManager
from flask.ext.script import Command

class Manager(BaseManager):
	def add_default_commands(self):
		"""NO we do NOT want the default stuff!"""
		pass

	def handle(self, *a,**k):
		if "app" not in self._commands:
			def app(*a,**k):
				"""Call application-specific commands. Details: '--help'."""
				assert len(a)==1
				a = a[0]
				mgr = BaseManager()
				mgr.app = self.app
				self.app.init_manager(mgr)
				sys.argv = [sys.argv[0]+" app"] + list(a)
				mgr.run()
				
			cmd = Command(app)
			cmd.name = 'app'
			cmd.capture_all_args = True
			self.add_command(cmd)

		return super(Manager,self).handle(*a,**k)
			
	def create_app(self, app=None, **kwargs):
		app = super(Manager,self).create_app(app, **kwargs)
		self.app = app
		return app


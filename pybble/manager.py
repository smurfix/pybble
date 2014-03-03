# -*- coding: utf-8 -*-
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
		## cloned from flask.ext.script.Manager
		if self.parent:
			# Sub-manager, defer to parent Manager
			return self.parent.create_app(**kwargs)

		if isinstance(self.app, Flask):
			return self.app

		app = self.app(**kwargs)
		self.app = app
		return app


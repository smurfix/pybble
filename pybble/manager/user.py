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

from flask import current_app
from flask._compat import text_type

from . import PrepCommand as Command
from . import Option, Manager
from ..core.models.user import User
from ..core.users import create_user,drop_user
from ..utils import random_string

class AddUser(Command):
	"""Add a new user"""
	def __init__(self):
		super(AddUser,self).__init__()
		self.add_option(Option("name", nargs='?', action="store",help="The new user's name"))

	def run(self, help=False, name=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		create_user(current_app.site, name)
		
class ListUsers(Command):
	"""Show the list of known sites"""
	add_help = False

	def run(self):
		for user in User.q.filter_by(parent=current_app.site).all():
			print(user.id, user.username or '-anon-', user.email, user.name, sep="\t")

		
class DropUser(Command):
	def __init__(self):
		super(DropUser,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The user name"))
	def run(self, help=False,name=None):
		if help or name is None:
			self.parser.print_help()
			sys.exit(not help)
		drop_user(name)

class ParamUser(Command):
	"""Set a user-specific parameter"""
	def __init__(self):
		super(ParamUser,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("--blueprint","-b", dest="bp", nargs='?', action="store",help="The affected blueprint"))
		self.add_option(Option("--force","-f", dest="force", action="store_true",help="Set value for different site"))
		self.add_option(Option("name", nargs='?', action="store",help="The user's name (print defaults if empty)"))
		self.add_option(Option("key", nargs='?', action="store",help="The parameter name (print all individual values if empty)"))
		self.add_option(Option("value", nargs='?', action="store",help="The value (print current value if not empty)"))
	def run(self, help=False,name=None,key=None,value=None,bp=None,force=False):
		if help:
			self.parser.print_help()
			sys.exit(0)
		site = current_app.site
		if bp is not None:
			site = SiteBlueprint.q.get_by(site=site, name=name).blueprint
		else:
			site = site.app
		if name is None:
			for var in ConfigVar.q.get_by(parent=site):
				print(var.name,var.value, sep="\t")
			return
		user = User.q.get_by(name=key)
		if user.parent != current_app.site and not force:
			raise InvalidCommand("This user's main site is ‘{}’.\nYou're changing settings for ‘{}’.\nUse the ‘--force’ option if you mean it.".format(user.parent.name,current_app.site.name))
		if key is None:
			for v in SiteConfigVar.q.filter(SiteConfigVar.owner.parent==site, SiteConfigVar.parent==user):
				print(v.var.name,v.value, sep="\t")
			return
		var = ConfigVar.q.get_by(parent=site,name=key)
		try:
			v = SiteConfigVar.q.get_by(var=var,owner=user)
		except NoData:
			v = None
		if value is None:
			if v is None:
				print("-not set-")
			else:
				print(v.value)
			return
		if value == "-":
			if v is not None:
				db.delete(v)
		elif v is None:
			SiteConfigVar(var=var,owner=user,value=value)
		else:
			v.value=value
		db.commit()
		
class UserManager(Manager):
	"""Manage web domains (a 'site') and their primary content (the 'app')."""
	def __init__(self):
		super(UserManager,self).__init__()
		self.add_command("add", AddUser())
		self.add_command("list", ListUsers())
		self.add_command("delete", DropUser())
		self.add_command("param", ParamUser())

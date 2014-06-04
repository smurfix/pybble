#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division, unicode_literals
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2009-2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details,
## including an optimistic statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time,
## courtesy of "make update". The original is in ‘utils/_boilerplate.py’.
## Thus, please do not remove the next line, or insert any blank lines.
##BP

import os
import sys

from flask import request
from flask._compat import text_type

from . import PrepCommand as Command
from . import Option, Manager
from ..core.models.site import Site,App
from ..globals import current_site
from ..app import create_site

def list_sites(site,level=0):
	if level:
		prefix=u"  "*((level-1)*2) + u"↳ "
	else:
		prefix=""
	
	print(prefix+site.domain,site.app.name if site.app else "-",site.name)
	level += 1
	for s in site.all_children("Site"):
		list_sites(s,level)

class AddSite(Command):
	"""Add a new sub-site"""
	add_help = False

	def __init__(self):
		super(AddSite,self).__init__()
		self.add_option(Option("site_name", nargs='?', action="store",help="The new site's name"))
		self.add_option(Option("app_name", nargs='?', action="store",help="The Pybble app module to install"))
		self.add_option(Option("domain", nargs='?', action="store",help="The domain to listen to"))

	def run(self, args=(), domain=None,app_name=None,site_name=None, help=False):
		if help or domain is None:
			self.parser.print_help()
			sys.exit(not help)
		create_site(current_site, domain,app_name,site_name)
		
class ListSites(Command):
	"""Show the list of known sites"""
	add_help = False

	def run(self):
		list_sites(current_site)
		
class DirSites(Command):
	"""List available apps, or app details."""
	def __init__(self):
		super(DirSites,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="An apps's name, for displaying details"))
	def run(self, help=False,name=None):
		if help:
			self.parser.print_help()
			sys.exit(not help)
		if name is None:
			print("Available apps:")
			for app in App.q.all():
				print(app.name,app.path, sep="\t")
			return
		app = App.q.get_by(name=text_type(name))
		if name is None:
			name = app.name
		if app.doc:
			print(app.doc)
		else:
			print("This app does not have individual configuration.")
		has_params = False
		for var in app.all_children("ConfigVar"):
			if not has_params:
				print("Name","Default","Usage", sep="\t")
				has_params = True
			print(var.name,var.value,var.doc, sep="\t")
		if not has_params:
			print("This app cannot be configured individually.")
		
class ParamSite(Command):
	"""Set a site's parameter"""
	def __init__(self):
		super(ParamSite,self).__init__()
		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("key", nargs='?', action="store",help="The parameter name"))
		self.add_option(Option("value", nargs='?', action="store",help="The value"))
	def run(self, help=False,name=None,key=None,value=None):
		if help:
			self.parser.print_help()
			sys.exit(0)
		site = current_site
		if key is None:
			for k,v in site.config.items():
				print(k,v)
			return
		if value is None:
			print(site.config[key])
			return
		if value == "-":
			del site.config[key]
		else:
			try:
				value = eval(value)
			except (SyntaxError,NameError):
				pass
			site.config[key] = value
		
class SiteManager(Manager):
	"""Manage web domains (a 'site') and their primary content (the 'app')."""
	def __init__(self):
		super(SiteManager,self).__init__()
		self.add_command("add", AddSite())
		self.add_command("dir", DirSites())
		self.add_command("list", ListSites())
		self.add_command("param", ParamSite())

	def create_app(self, app):
		return app
	

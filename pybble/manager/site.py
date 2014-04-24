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

from . import Command,Option
from ..core.models.site import Site
from ..app import create_site, list_apps

def list_sites(site,level=0):
	if level:
		prefix=u"  "*((level-1)*2) + u"↳ "
	else:
		prefix=""
	
	print(prefix+site.domain,site.app,site.name)
	level += 1
	for s in site.children:
		list_sites(s,level)

class AddSiteCommand(Command):
	"""Add a new sub-app"""
	add_help = False

	def __init__(self):
		super(AddSiteCommand,self).__init__()
		self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
		self.add_option(Option("name", nargs='?', action="store",help="The new site's name"))
		self.add_option(Option("app", nargs='?', action="store",help="The Pybble app module to install"))
		self.add_option(Option("domain", nargs='?', action="store",help="The domain to listen to"))

	def __call__(self,app_, args=(), domain=None,app=None,name=None, help=False):
		if help or domain is None:
			self.parser.print_help()
			print("Available apps: "+" ".join(list_apps()),file=sys.stderr)
			sys.exit(not help)
		create_site(app_.site,domain,app,name)
		
class SitesCommand(Command):
	"""Show a list of known sites"""
	add_help = False

	def __call__(self,app):
		list_sites(app.site)
		

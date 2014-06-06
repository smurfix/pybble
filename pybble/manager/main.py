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
import logging
from importlib import import_module
from gevent.wsgi import WSGIServer

from flask import Flask, url_for
from flask.config import Config

from flask.ext.script import Server
from flask.ext.migrate import Migrate, MigrateCommand

from werkzeug.exceptions import NotFound
from werkzeug.wsgi import responder

from . import Manager,Command,Option
from .. import ROOT_SITE_NAME
from ..core.db import db
from ..core.session import SubdomainDispatcher
from ..core.models.site import Site,Blueprint
from ..core.signal import all_apps,app_list
from ..app import create_site, list_apps

logger = logging.getLogger('pybble.manager.main')

def make_shell_context():
	" Update shell. "
	from flask import current_app
	return dict(app=current_app, db=db)

def check():
	"""Prints app status"""
	from flask import current_app
	from pprint import pprint
	app = current_app

	with app.app_context():
		print("App:",)
		print(str(app))
		print("Extensions:")
		pprint(app.extensions)
		print("Modules:")
		pprint(app.blueprints)
    
def config():
	"""Dumps configuration data"""
	from flask import current_app
	app = current_app
	for k,v in app.config.items():
		print("%s=%s" % (k,repr(v)))

class ShowUrls(Command):
	"""
		Displays all of the url matching routes for the project
	"""
	def __init__(self, order='rule'):
		self.order = order

	def get_options(self):
		return (
			Option('url',
				   nargs='?',
				   help='URL (/static/image.png) or endpoint (static)'),
			Option('params', nargs="*", help='Parameters (file=img/lolcats.img)')
		)
		return options

	def run(self, url=None, params=()):
		from flask import current_app
		from werkzeug.exceptions import NotFound, MethodNotAllowed

		if url is None: # list
			column_headers = ('Rule', 'Endpoint')

			rules = sorted(current_app.url_map.iter_rules(), key=lambda rule: rule.rule)
			max_rule_length = max(4,max(len(r.rule) for r in rules))
			max_ep_length = max(4,max(len(r.endpoint) for r in rules))
			str_template = '%%-%ds  %%s' % (max_rule_length,)
			table_width = max_rule_length +2+ max_ep_length

			print(str_template % column_headers)
			print('-' * table_width)
	
			for r in rules:
				print(str_template % (r.rule,r.endpoint))
			return

		a = current_app.url_map.bind(current_app.site.domain)

		opts = {}
		for s in params:
			try:
				s,v = s.split('=',1)
			except ValueError:
				v = True
			opts[s] = v

		if url.startswith('/'): # match an URL ➙ emit an endpoint
			r = a.match(url, query_args=opts)
			print(r[0]+"  "+" ".join("%s=%s"%(k,v) for k,v in r[1].items()))

		else: # match an endpoint ➙ emit a URL
			print(url_for(url, **opts))

############################### Root

class RootManager(Manager):
	_pdb = False
	_dump = False
	def __init__(self, app=None, *a,**kw):
		super(RootManager, self).__init__(*a,**kw)
		self.add_root_options()
		self.add_root_commands()
		self.app = app

	def add_root_options(self):
		self.add_option("-c", "--config", dest="config", required=False, default=None, help="Config file to use")
		self.add_option("-s", "--site", dest="site", required=False, default=ROOT_SITE_NAME, help="which Site to run on")
		self.add_option("-S", "--no-site", dest="site", action="store_const", const=None, required=False, help="Do not choose a site")
		self.add_option("-t", "--test", dest="testing", action="store_true", required=False, default=False, help="Use the test database")
		self.add_option("-d", "--pdb", dest="pdb", action="store_true", required=False, default=False, help="drop into the debugger if there's an error")
		self.add_option("-D", "--stackdump", dest="dump", action="store_true", required=False, default=False, help="Do not catch crashes at all")

	def add_root_commands(self):
		from .blueprint import BlueprintManager
		from .app import AppCommand
		from .populate import PopulateCommand
		from .add import AddCommand
		from .schema import SchemaCommand
		from .mime import MIMEManager
		from .objtyp import TypManager
		from .obj import RESTManager
		from .site import SiteManager
		from .user import UserManager

		coremanager = Manager()
		coremanager.__doc__ = "Examine and change Pybble's internal data"
		coremanager.command(check)
		coremanager.command(config)
		coremanager.add_command("objtyp",TypManager())
		coremanager.add_command("mime",MIMEManager())
		coremanager.add_command("url",ShowUrls())
		coremanager.add_command("populate",PopulateCommand())
		coremanager.add_command("add",AddCommand())
		coremanager.add_command("schema",SchemaCommand())
		coremanager.add_command("migrate",MigrateCommand)
		coremanager.shell(make_shell_context)

		self.add_command("site",SiteManager())
		#self.add_command("app",AppCommand())
		self.add_command("blueprint",BlueprintManager())
		self.add_command("obj",RESTManager())
		self.add_command("run",SubdomainServer())
		self.add_command("core",coremanager)
		self.add_command("user",UserManager())

	def __call__(self, app=None, pdb=False, dump=False, **kw):
		self._pdb = pdb
		self._dump = dump
		if self.app is not None:
			# this can't happen in production
			assert self.app.testing, self.app
			return self.app
		from ..app import create_app
		app = create_app(**kw)
		return app

############################### Accessing sub-sites by domain

class SubdomainServer(Server):
	"""Actually run the server"""
	def __call__(self,app, host,port,**opts):
		dispatch = SubdomainDispatcher(app)
		with app.app_context():
			if app.config.BEHIND_PROXY:
				from werkzeug.contrib.fixers import ProxyFix
				dispatch = ProxyFix(dispatch)
		server = WSGIServer((host,port), dispatch)
		logger.debug("Serving requests.")
		server.serve_forever()
		
class DeadApp(object):
	def __init__(self, exc,msg):
		self.exc = exc()
		self.msg = msg
	@responder
	def __call__(self,environ,start_response):
		e = self.exc
		e.description = self.msg
		return e


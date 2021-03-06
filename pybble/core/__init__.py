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

from .utils import attrdict
import os
from flask import Flask
from flask._compat import text_type
from flask.config import Config

# We use our own template system
from formalchemy import config as fa_config
def _render_template(*a,**k):
	# This prevents circular imports
	from pybble.render import render_template
	fa_config.engine = render_template
	return render_template(*a,**k)
fa_config.engine = _render_template

def _std_values(x):
	if x == "None":
		return None
	if x == "True":
		return True
	if x == "False":
		return False
	return x

class config(attrdict,Config):
	_module = None
	_not_really = set()
	_really = set()
	def __init__(self):
		self._load()

	def _is_fixed(self,k):
		if k in self._really:
			return True
		if k in self._not_really:
			return False
		if k in self:
			return True
		return False

	def _load(self,config=None):
		if config is None:
			try:
				config=os.environ['PYBBLE']
			except KeyError:
				raise RuntimeError("You need to define the ‘PYBBLE’ environment variable.")

		from werkzeug import import_string
		if self._module is not None:
			if self._module == config:
				return

		## clean out
		while self:
			self.pop()

		try:
			py=import_string(config)
		except ImportError as e:
			import sys
			print("Error:",str(e), file=sys.stderr)

			raise RuntimeError("You have a problem with the ‘{}’ configuration module.")
		for k,v in py.__dict__.items():
			if not k.startswith('_'):
				self[k]=v

		self._default('TESTING',False)
		self._default('DEBUG',None)
		self._default('TRACE',False)
		self._default('sql_driver','mysql')
		self._default('sql_host','localhost')
		self._default('sql_port',3306,int)
		self._default('sql_user','test')
		self._default('sql_pass','test')
		self._default('sql_database','pybble')

		self._default('sql_uri',None)
		self._default('web_port',8080,int)

		from . import default_settings as DS
		for k,v in DS.__dict__.items():
			if k != k.upper(): continue
			# These are overrideable
			if k not in self:
				self[k] = v
				self._not_really.add(k)
			self._default(text_type(k),v)

		if 'SECRET_KEY' not in self:
			if self.TESTING:
				self.SECRET_KEY = 'If you use this in production, you deserve to lose.'
			else:
				raise RuntimeError("For production use, you need to set SECRET_KEY in config.")

		if self.sql_uri is None:
			if self.sql_pass == "test" and not self.TESTING:
				raise RuntimeError("For production use, you need to set a database password (or URI).")
			
			if self.sql_database.startswith("/") or self.sql_database.startswith(":"): # it's a file
				self.sql_uri = "%s:///%s" % (self.sql_driver,self.sql_database)
			else: # it's a remote connection
				self.sql_uri = "%s://%s:%s@%s:%s/%s" % (self.sql_driver,self.sql_user,self.sql_pass,self.sql_host,self.sql_port,self.sql_database)

		for k,v in Flask.default_config.items():
			# These are overrideable
			if k not in self:
				self[k] = v
				self._not_really.add(k)

		# for Alembic
		self.SQLALCHEMY_DATABASE_URI = self.sql_uri

		self._module = config

	def _default(self,k,v,conv=_std_values):
		try:
			v = os.environ['PYBBLE_'+k.upper()]
			if conv:
				v = conv(v)
			self._really.add(k)
		except KeyError:
			if k in self:
				return
		self[k] = v
	
	def _dump(self, shell=False):
		if shell:
			p="%s=$( echo -ne %r )"
		else:
			p="%s=%r"

		from pybble.compat import PY2
		for k,v in self.items():
			if PY2:
				if isinstance(k,unicode):
					k = k.encode("utf-8")
				if isinstance(v,unicode):
					v = v.encode("utf-8")
			print(p % (k,v))

config = config()

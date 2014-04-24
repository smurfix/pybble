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

from .utils import attrdict
import os
from flask import Flask

class config(attrdict):
	_module = None
	def __init__(self):
		self._load()

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

		self._default('TEST',False)
		self._default('DEBUG',False)
		self._default('TRACE',False)
		self._default('mysql_host','localhost')
		self._default('mysql_port',3306,int)
		self._default('mysql_user','test')
		self._default('mysql_pass','test')
		self._default('mysql_database','pybble')
		self._default('mysql_uri',None)
		self._default('web_port',8080,int)

		if 'SECRET_KEY' not in self:
			if self.TEST:
				self.SECRET_KEY = 'If you use this in production, you deserve to lose.'
			else:
				raise RuntimeError("For production use, you need to set SECRET_KEY in config.")

		if self.mysql_uri is None:
			if self.mysql_pass == "test" and not self.TEST:
				raise RuntimeError("For production use, you need to set a database password (or URI).")
			
			self.mysql_uri = "mysql://%s:%s@%s:%s/%s" % (self.mysql_user,self.mysql_pass,self.mysql_host,self.mysql_port,self.mysql_database)

		for k,v in Flask.default_config.items():
			self.setdefault(k,v)

		self._module = config

	def _default(self,k,v,conv=None):
		try:
			v = os.environ['PYBBLE_'+k.upper()]
			if conv:
				v = conv(v)
		except KeyError:
			pass
		if k not in self:
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

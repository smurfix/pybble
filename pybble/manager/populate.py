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

import os
import sys
import logging

from sqlalchemy.orm.exc import NoResultFound

from . import Manager,Command,Option

logger = logging.getLogger('pybble.manager.populate')

content_types = [
	## MIME type,subtype, file extension, name, description
	('text','html','html','Web page',"A complete HTML-rendered web page"),
	('text','plain','txt','Plain text',"raw text, no formatting"),
	('text','html+obj',None,'HTML content',"one HTML element"),
	('text','html+haml','haml','HAML template',"HTML template (HAML syntax)"),
]
class PopulateCommand(Command):
#	def __init__(self):
#		super(PopulateCommand,self).__init__()
#		#self.add_option(Option("-?","--help", dest="help",action="store_true",help="Display this help text and exit"))
#		self.add_option(Option("name", nargs='?', action="store",help="The blueprint's internal name"))
#		self.add_option(Option("bp", nargs='?', action="store",help="The Pybble blueprint to install"))
#		self.add_option(Option("path", nargs='?', action="store",help="The path prefix to attach it to"))

	def __call__(self,app):
		with app.test_request_context('/'):
			self.main()

	def main(self):
		from ..core.models.site import Site
		from ..core.models.types import MIMEtype
		from ..core.models.config import ConfigVar
		from .. import ROOT_NAME

		## main site
		try:
			root = Site.q.get_by(name=ROOT_NAME)
		except NoResultFound:
			root = Site(name=ROOT_NAME)
			db.add(root)
			logger.debug("The root site has been created.")
		else:
			logger.debug("The root site exists. Good.")
		db.commit()

		## MIME types
		for type,subtype,ext,name,doc in content_types:
			try:
				MIMEtype.q.get_by(typ=type,subtyp=subtype)
			except NoResultFound:
				db.add(MIMEtype(typ=type, subtyp=subtype, ext=ext, name=name, doc=doc))
				logger.info("MIME type '%s/%s' (%s) created." % (type,subtype,name))
		db.commit()
		
		## default variables
		from pybble.manager import default_settings as DS
		for k,v in DS.__dict__.items():
			if k != k.upper(): continue
			try:
				cf = ConfigVar.q.get_by(name=k)
			except NoResultFound:
				cf = ConfigVar(parent=root, name=k, value=v)
				db.add(ConfigVar(parent=root, name=k, value=v))

			if not cf.info:
				cf.info = getattr(DS,'d_'+k,None)
		db.commit()


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
from flask import request

from ..utils import random_string
from ..core.db import db
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
		from ..core.models import Discriminator
		from ..core.models._descr import D
		from ..core.models.site import Site
		from ..core.models.user import User
		from ..core.models.types import MIMEtype
		from ..core.models.config import ConfigVar
		from .. import ROOT_SITE_NAME,ROOT_USER_NAME, ANON_USER_NAME

		count = added = updated = 0

		## Object discriminators
		for id,name in D.items():
			count += 1
			doc = D._doc.get(id,None)
			try:
				d = Discriminator.q.get_by(id=id)
			except NoResultFound:
				d = Discriminator(id=id,name=name, display_name=name, infotext=doc)
				db.add(d)
				added += 1
			else:
				if doc and (d.infotext is None or d.infotext != doc):
					d.infotext = doc
					updated += 1
		db.commit()
		if count == added:
			logger.debug("Discriminators have been loaded.")
		elif added or updated:
			logger.debug("{}/{} discriminators updated/added.".format(updated,added))

		## main site
		try:
			root = Site.q.get_by(name=ROOT_SITE_NAME)
		except NoResultFound:
			root = Site(domain="localhost", name=ROOT_SITE_NAME)
			logger.debug("The root site has been created.")
		else:
			logger.debug("The root site exists. Good.")
		db.commit()
		request.site = root

		## anon user
		try:
			anon = User.q.get_by(parent=root, username=ANON_USER_NAME)
		except NoResultFound:
			anon = User(ANON_USER_NAME)
			logger.debug("The anon user has been created.")
		else:
			logger.debug("The anon user exists. Good.")
		db.commit()

		## main user
		superuser = root.owner
		if superuser is None:
			try:
				superuser = User.q.get_by(username=ROOT_USER_NAME, parent=root)
			except NoResultFound:
				password = random_string()
				superuser = User(ROOT_USER_NAME,password)
				db.commit()
				logger.info(u"The root user has been created. Password: ‘{}’.".format(password))
			else:
				logger.warning(u"The root user has been associated. This is strange.")
			root.owner = superuser
			db.flush()
		elif superuser.username != ROOT_USER_NAME:
			logger.warn(u"The root site's owner is ‘{}’, not ‘{}’".format(superuser.username,ROOT_USER_NAME))
		else:
			logger.debug("The root user exists. Good.")
		db.commit()

		## MIME types
		for type,subtype,ext,name,doc in content_types:
			try:
				mt = MIMEtype.q.get_by(typ=type,subtyp=subtype)
			except NoResultFound:
				mt = MIMEtype(typ=type, subtyp=subtype, ext=ext, name=name, doc=doc)
				db.add(mt)
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
				db.flush()

			if not cf.info:
				cf.info = getattr(DS,'d_'+k,None)
		db.commit()


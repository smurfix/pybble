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
import logging
import re
from traceback import print_exc,format_exc

from flask import request, _app_ctx_stack
from flask._compat import text_type,string_types

from .. import TEMPLATE_PATH, STATIC_PATH
from ..utils import random_string,NotGiven
from ..core import config
from ..core.db import db, NoData
from ..core.add import process_module
from . import Command,Option

logger = logging.getLogger('pybble.manager.populate')

_metadata = re.compile('##:?(\S+) *[ :] *(.*)\n') # re.U ?

upload_content_types = [
	## MIME type,subtype, file extension, name, description
	('text','html','html','Web page',"A complete HTML-rendered web page"),
	('text','plain','txt','Plain text',"raw text, no formatting"),
	('text','javascript','js',"JavaScript",None),
	('text','css','css',"CSS",None),
	('image','png','png',"PNG image",None),
	('image','jpeg',('jpg','jpeg'),"JPEG image",None),
	('image','gif','gif',"GIF image",None),
	('application','binary','bin',"raw data",None),
	('application','pdf','pdf',"PDF document",None),
]
MIME = upload_content_types+[
	('application','rss+xml','rss',"RSS feed",None),
	('text','xml','xml',"XML data",None),
	('message','rfc822',None,"Email message",None),

	('pybble','_empty',None,"no data",None),

	('pybble','*',None,"any pybble data",None),
	('html','*',None,"any html data",None),
	('text','*',None,"any text data",None),

	('html','subpage',None,NotGiven,"a (main) part of a webpage"),
	('html','string',None,NotGiven,"a short string describing an object"),
	('html','detail',None,NotGiven,"a tabular view of an object's internal state"),
	('html','snippet',None,NotGiven,"a fragment for the explore view"),
	('html','hierarchy',None,NotGiven,"a fragment for hierarchical view within a page"),
	('html','preview',None,NotGiven,"a view for previewing"),
	('html','edit',None,NotGiven,"the form for editing"),
	('xml','rss',None,NotGiven,"a fragment for the RSS feed"),
]

MODEL = (
	'pybble.core.models.objtyp.ObjType',
	'pybble.core.models.config.ConfigVar',
	'pybble.core.models.config.ConfigData',
	'pybble.core.models.config.SiteConfigVar',
	'pybble.core.models.site.App',
	'pybble.core.models.site.Blueprint',
	'pybble.core.models.site.Site',
	'pybble.core.models.site.SiteBlueprint',
	'pybble.core.models.user.User',
	'pybble.core.models.user.Group',
	'pybble.core.models.user.Member',
	'pybble.core.models.tracking.TrackingObject',
	'pybble.core.models.tracking.Breadcrumb',
	'pybble.core.models.tracking.Change',
	'pybble.core.models.tracking.Delete',
	'pybble.core.models.tracking.Tracker',
	'pybble.core.models.tracking.WantTracking',
	'pybble.core.models.tracking.UserTracker',
	'pybble.core.models.permit.Permission',
	'pybble.core.models.types.MIMEtype',
	'pybble.core.models.types.MIMEext',
	'pybble.core.models.types.MIMEtranslator',
	'pybble.core.models.types.MIMEadapter',
	'pybble.core.models.template.Template',
	'pybble.core.models.template.TemplateMatch',
	'pybble.core.models.storage.Storage',
	'pybble.core.models.files.BinData',
	'pybble.core.models.files.StaticFile',
	'pybble.core.models.verifier.VerifierBase',
	'pybble.core.models.verifier.Verifier',
)

VAR = []
APP = []
BLUEPRINT = []
VERIFIER = []
TEMPLATE = []

class PopulateCommand(Command):
	"""Add minimal basic data to the database"""
	def __init__(self):
		super(PopulateCommand,self).__init__()
		self.add_option(Option("-f","--force", dest="force",action="store_true",help="Override all database changes"))

	def __call__(self,app, force=False):
		with app.test_request_context('/'):
			self.main(app,force)

	def main(self,app, force=False):
		from ..core.models.site import Site,App,Blueprint,SiteBlueprint
		from ..core.models.storage import Storage
		from ..core.models.files import StaticFile
		from ..core.models.user import User
		from ..core.models.permit import Permission,permit
		from ..core.models.types import MIMEtype
		from ..core.models._const import PERM_ADD
		from ..translator import list_translators
		from ..verifier import list_verifiers
		from .. import ROOT_SITE_NAME,ROOT_USER_NAME

		from ..app import list_apps
		from ..blueprint import list_blueprints

		if 'MEDIA_PATH' not in config:
			raise RuntimeError("You have to set MEDIA_PATH so that I can store my files somewhere")

		global VAR
		def gen_vars():
			from pybble.core import default_settings as DS
			for k,v in DS.__dict__.items():
				if k != k.upper(): continue
				if k in app.config: # add overrides
					v = app.config[k]
				yield text_type(k),v,getattr(DS,'d_'+k,None)
		VAR = gen_vars()

		global APP
		def gen_apps():
			for name in list_apps():
				name = text_type(name)
				yield ("pybble.app.{}.App".format(name),name)
		APP = list(gen_apps()) # required twice

		global BLUEPRINT
		def gen_bps():
			for name in list_blueprints():
				name = text_type(name)
				yield ("pybble.blueprint.{}.Blueprint".format(name),name)
		BLUEPRINT = gen_bps()

		global TRANSLATOR
		def gen_translators():
			for name in list_translators():
				name = text_type(name)
				yield ("pybble.translator.{}.Translator".format(name),name)
		TRANSLATOR = gen_translators()

		global VERIFIER
		def gen_translators():
			for name in list_verifiers():
				name = text_type(name)
				yield ("pybble.verifier.{}.Verifier".format(name),name)
		VERIFIER = gen_translators()

		## Bootstrapping is tricky.
		process_module({'MODEL':MODEL, 'MIME':MIME, 'APP':APP}, force=force)

		## main site
		rapp = App.q.get_by(name='_root')
		try:
			try:
				root = Site.q.get_by(parent=None)
			except NoData:
				root = Site.q.get_by(name=ROOT_SITE_NAME)
		except NoData:
			root = Site.new(domain="localhost", name=ROOT_SITE_NAME, app=rapp)
			logger.debug("The root site has been created.")
		else:
			if root.app is None or force:
				if root.app != rapp:
					root.app = rapp
					logger.debug("Root site's app set.")

			if root.parent is not None:
				if force:
					root.parent = None
					logger.warning("The root site is not actually root. This has been corrected.")
				else:
					logger.error("The root site is not actually root. This is a problem.")

		db.session.flush()
		_app_ctx_stack.top.site = root
		_app_ctx_stack.top.app.app = root.app

		## Default storage
		try:
			try:
				st = Storage.q.get_by(name=u"Pybble")
			except NoData:
				st = Storage.q.get_by(name=u"Test")
		except NoData:
			st = Storage.new("Test",app.config.MEDIA_PATH,"/static", site=root)
			if Storage.q.filter_by(site=root,default=True).count() == 0:
				st.default = True
		else:
			st.site = root
		db.session.flush()

		## main user
		try:
			superuser = User.q.get_by(username=ROOT_USER_NAME)
		except NoData:
			password = random_string()
			superuser = User.new(site=root,username=ROOT_USER_NAME,password=password)
			db.session.flush()
			logger.info(u"The root user has been created. Password: ‘{}’.".format(password))
		else:
			if superuser.site != root:
				logger.warning(u"The root user's site is {}, not {}.".format(superuser.site,root))
				if force:
					superuser.site = root
		db.session.flush()
		if superuser.email is None or (force and superuser.email != config.ADMIN_EMAIL):
			if superuser.email is not None:
				logger.info(u"The main admin email changed from ‘{}’ to ‘{}’".format(superuser.email,config.ADMIN_EMAIL))
			superuser.email = text_type(config.ADMIN_EMAIL)
		db.session.flush()
		request.user = superuser
		root.initial_permissions(superuser)

		global STATIC
		STATIC = ((STATIC_PATH,''),)

		def find_templates(dirpath,webpath="",mapper=""):
			if not os.path.isdir(dirpath):
				return

			for fn in os.listdir(dirpath):
				if fn.startswith("."):
					continue
				newdirpath = os.path.join(dirpath,fn)
				newwebpath = "{}/{}".format(webpath,fn) if webpath else fn
				m=mapper
				if os.path.isdir(newdirpath):
					if m: m=m.do_dir(fn)
					for r in find_templates(newdirpath,newwebpath,m):
						yield r
				else:
					if m: m=m.do_file(fn)
					yield (newdirpath,newwebpath,m)

		class M(object):
			"""Infer template metadata from the file name"""
			def __init__(self,path=()):
				self.path=path
			def do_dir(self,fn):
				return M(self.path+(fn,))
			def do_file(self,fn):
				if len(self.path) != 1: return ""
				fn,ext = fn.split('.',1)
				if ext == "html": ext = "jinja"
				elif ext != "haml": return ""
				p = self.path[0]
				if p == "details": p = "html/detail"
				elif p == "email": p = "text/plain"
				elif p == "linktext": p = "html/string"
				elif p == "rss": p = "xml/rss"
				elif p == "preview": p = "html/preview"
				elif p == "hierarchy": p = "html/hierarchy"
				elif p == "snippet": p = "html/snippet"
				elif p == "edit": p = "html/edit"
				else: return ""
				return """\
##src pybble/{}
##dst {}
##typ template/{}
##named 1
##inherit -
##match root
##weight 0
""".format(fn,p,ext)

		global TEMPLATE
		TEMPLATE = find_templates(TEMPLATE_PATH,mapper=M())

		# APP is here again because of attached templates which might not
		# have loaded the first time because of missing translators
		process_module({'MODEL':MODEL}, force=True)
		process_module({'VAR':VAR, 'BLUEPRINT':BLUEPRINT, 'APP':APP, 'TRANSLATOR':TRANSLATOR, 'VERIFIER':VERIFIER, 'STATIC':STATIC, 'TEMPLATE':TEMPLATE}, force=force)

		## possible root app fix-ups
		aapp = App.q.get_by(name="_alias")
		import socket
		hostname = text_type(socket.gethostname())
		try:
			asite = Site.q.get_by(name="root alias",parent=root)
		except NoData:
			asite = Site.new(name="root alias", domain=hostname, app=aapp)
			logger.info("Root site aliased ‘{}’ created.".format(hostname))
		else:
			if asite.domain != hostname:
				logger.warn("Root site alias is {}, not {}".format(asite.domain,hostname))
				if force:
					logger.warn("This is NOT aut-corrected.")
		db.session.flush()

		try:
			root_bp = Blueprint.q.get_by(name='_root')
		except NoData:
			logger.error("The ‘_root’ blueprint is not present. Setup is incomplete!")
		else:
			try:
				rbp = SiteBlueprint.q.get_by(site=root,blueprint=root_bp,path="")
			except NoData:
				rbp = SiteBlueprint.new(site=root,blueprint=root_bp,path="",name="pybble")
				logger.debug("Root site's content blueprint created.")
			else:
				if rbp.name != "pybble" and force:
					logger.warn("Root site's blueprint name changed from ‘{}’ to ‘pybble’.".format(rbp.name))
					rbp.name = "pybble"
				if rbp.endpoint != "pybble" and force:
					logger.warn("Root site's static blueprint endpoint changed from ‘{}’ to ‘pybble’.".format(rbp.name))
					rbp.endpoint = "pybble"
		db.session.flush()

		try:
			static_bp = Blueprint.q.get_by(name='static')
		except NoData:
			logger.error("The ‘static’ blueprint is not present. Setup is incomplete!")
		else:
			try:
				rbp = SiteBlueprint.q.get_by(site=root,blueprint=static_bp,path="")
			except NoData:
				rbp = SiteBlueprint.new(site=root,blueprint=static_bp,path="",name="static",endpoint="")
				logger.debug("Root site's static blueprint created.")
			else:
				if rbp.name != "static" and force:
					logger.warn("Root site's static blueprint name changed from ‘{}’ to ‘static’.".format(rbp.name))
					rbp.name = "static"
				if rbp.endpoint != "" and force:
					logger.warn("Root site's static blueprint endpoint changed from ‘{}’ to ‘static’.".format(rbp.name))
					rbp.endpoint = ""
		db.session.flush()

		# Add file types that may be uploaded
		for typ,subtyp,ext,name,doc in upload_content_types:
			mt = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
			permit(root,root, right=PERM_ADD, new_objtyp=StaticFile.type, new_mimetyp=mt)

		## All done!
		logger.debug("Setup finished.")
		db.session.commit()

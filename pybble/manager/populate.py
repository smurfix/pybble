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
import logging

from flask import request
from flask._compat import text_type

from .. import TEMPLATE_PATH, STATIC_PATH
from ..utils import random_string
from ..core import config
from ..core.db import db, NoData
from ..core.db import db, NoData
from . import Manager,Command,Option

logger = logging.getLogger('pybble.manager.populate')

content_types = [
	## MIME type,subtype, file extension, name, description
	('text','html','html','Web page',"A complete HTML-rendered web page"),
	('text','plain','txt','Plain text',"raw text, no formatting"),
	('text','html+obj',None,'HTML content',"one HTML element"),
	('text','html+haml','haml','HAML template',"HTML template (HAML syntax)"),
    ('text','javascript','js',"JavaScript",None),
    ('text','css','css',"CSS",None),
    ('image','png','png',"PNG image",None),
    ('image','jpeg','jpg',"JPEG image",None),
    ('image','jpeg','jpeg',"JPEG image",None),
    ('image','gif','gif',"GIF image",None),
    ('application','binary','bin',"raw data",None),
    ('application','pdf','pdf',"PDF document",None),
    ('text','xml','xml',"XML data",None),
]

class PopulateCommand(Command):
	"""Add minimal basic data to the database"""
	def __init__(self):
		super(PopulateCommand,self).__init__()
		self.add_option(Option("-f","--force", dest="force",action="store_true",help="Override all database changes"))

	def __call__(self,app, force=False):
		with app.test_request_context('/'):
			self.main(app,force)

	def main(self,app, force=False):
		from ..core.models import Discriminator,Renderer
		from ..core.models._descr import D
		from ..core.models.site import Site
		from ..core.models.storage import Storage
		from ..core.models.files import BinData,StaticFile
		from ..core.models.user import User
		from ..core.models.types import MIMEtype
		from ..core.models.template import Template
		from ..core.models.config import ConfigVar
		from .. import ROOT_SITE_NAME,ROOT_USER_NAME, ANON_USER_NAME

		if 'MEDIA_PATH' not in config:
			raise RuntimeError("You have to set MEDIA_PATH so that I can store my files somewhere")

		## helper to load known apps, blueprints, renderers
		def loadables(lister,Obj,path):
			added=changed=found=0
			for name in lister():
				name = text_type(name)
				found += 1
				is_new = False
				try:
					obj = Obj.q.get_by(name=name)
				except NoData:
					obj = Obj(name=name, path="{}.{}.{}".format(path,name,Obj.__name__))
					is_new = True
				db.flush()
				try:
					a = obj.mod
				except Exception as e:
					logger.warn("{} ‘{}’ ({}) is not usable: {}".format(Obj.__name__,name,obj.path,str(e)))
					if is_new:
						# Dance 
						db.add(obj)
						db.flush()
						db.delete(obj)
				else:
					if obj.doc is None or force:
						try:
							obj.doc = a.__doc__
						except AttributeError:
							pass
			if not found:
				logger.warn("{}: None found".format(Obj.__name__))
			elif not changed and not added:
				logger.debug("{}: {} found, No changes".format(Obj.__name__,found))
			else:
				logger.info("{}: {} new, {} updated".format(Obj.__name__,added,changed))
			db.commit()

		## Object discriminators
		count = added = updated = 0
		for id,name in D.items():
			count += 1
			doc = D._doc.get(id,None)
			path = "pybble.core.models."+name
			name = name.rsplit(".")[-1]
			try:
				d = Discriminator.q.get_by(id=id)
			except NoData:
				d = Discriminator(id=id,name=name, path=path, doc=doc)
				db.add(d)
				added += 1
			else:
				d.path = path
				if (doc and (d.doc is None or d.doc != doc)) or force:
					d.doc = doc
					updated += 1
		db.commit()
		if count == added:
			logger.debug("Discriminators have been loaded.")
		elif added or updated:
			logger.debug("{}/{} discriminators updated/added.".format(updated,added))

		## main site
		try:
			root = Site.q.get_by(name=ROOT_SITE_NAME)
		except NoData:
			root = Site(domain="localhost", name=ROOT_SITE_NAME)
			logger.debug("The root site has been created.")
		else:
			if root.parent is not None:
				if force:
					root.parent = None
					logger.warning("The root site is not actually root. This has been corrected.")
				else:
					logger.error("The root site is not actually root. This is a problem.")

			else:
				logger.debug("The root site exists. Good.")
		db.commit()
		request.site = root

		## storage
		try:
			st = Storage.q.get_by(name=u"Pybble")
		except NoData:
			try:
				st = Storage.q.get_by(name=u"Test")
			except NoData:
				st = Storage("Test",app.config.MEDIA_PATH,"localhost:5000/static")
		else:
			st.superparent = root
		db.commit()

		## anon user
		try:
			anon = User.q.get_by(parent=root, username=ANON_USER_NAME)
		except NoData:
			anon = User(ANON_USER_NAME)
			logger.debug("The anon user has been created.")
		else:
			logger.debug("The anon user exists. Good.")
		db.commit()

		## main user
		superuser = root.owner
		if superuser is None or force:
			try:
				superuser = User.q.get_by(username=ROOT_USER_NAME, parent=root)
			except NoData:
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
		request.user = superuser

		## MIME types
		added=0
		for type,subtype,ext,name,doc in content_types:
			try:
				mt = MIMEtype.q.get_by(typ=type,subtyp=subtype)
			except NoData:
				mt = MIMEtype(typ=type, subtyp=subtype, ext=ext, name=name, doc=doc)
				db.add(mt)
				logger.info("MIME type '%s/%s' (%s) created." % (type,subtype,name))
				added += 1
			else:
				if mt.doc is None or force:
					mt.doc = doc
		if not added:
			logger.debug("No new MIME types necessary.")
		db.commit()
		
		## Rendering actual content
		from ..render import list_renderers
		from ..core.models.types import mime_ext
		loadables(list_renderers,Renderer,"pybble.render")

		## static files (recursive)
		def add_files(dir,path):
			added=0
			for f in os.listdir(dir):
				if f.startswith("."):
					continue
				f = f.decode("utf-8")
				filepath = os.path.join(dir,f)
				webpath = path+'/'+f
				if os.path.isdir(filepath):
					added += add_files(filepath,webpath)
					continue
				dot = f.rindex(".")
				mime = mime_ext(f[dot+1:])
				with open(filepath,"rb") as fd:
					content = fd.read()
					try:
						sb = BinData.lookup(content)
					except NoData:
						sb = BinData(f[:dot],ext=f[dot+1:],content=content, storage=st)

					try:
						sf = StaticFile.q.get_by(path=webpath,superparent=root)
					except NoData:
						sf = StaticFile(webpath,sb)
					else:
						try:
							c = sf.content
						except EnvironmentError as e:
							import errno
							if e.errno != errno.ENOENT:
								raise
							logger.error("File ‘{}’ vanished".format(filepath))
							sf.bindata.hash = None
							sf.bindata.record_deletion("file vanished")
							sf.record_deletion("file vanished")
							db.flush()

							sb = BinData(f[:dot],ext=f[dot+1:],content=content, storage=st)
							sf = StaticFile(webpath,sb)
							c = sf.content

						if content != sf.content:
							logger.warning("StaticFile %d:‘%s’ differs." % (sf.id,webpath))
							if force:
								sf.bindata.record_deletion("replaced by update")
								sf.record_deletion("replaced by update")
								sf = StaticFile(webpath,sb)
					db.commit()
			return added
		added = add_files(STATIC_PATH, u"")
		logger.debug("{} files changed.".format(added))

		## templates (not recursive)
		def get_template(filepath,webpath):
			added = 0
			with file(filepath) as f:
				try:
					data = f.read().decode("utf-8")
				except Exception:
					print("While reading",filepath,file=sys.stderr)
					raise

			webpath = unicode(webpath)
			try:
				t = Template.q.get_by(name=webpath,parent=root)
			except NoData:
				t = Template(name=webpath,data=data,parent=root)
				t.owner = superuser
				added += 1
			else:
				if t.mime is None:
					dot = filepath.rindex(".")
					try:
						t.mime = mime_ext(filepath[dot+1:])
					except NoData:
						raise NoData(filepath[dot+1:])

				if t.data != data:
					print (u"Warning: Template %d '%s' differs." % (t.id,filepath)).encode("utf-8")
					if force:
						t.data = data
				if force:
					t.superparent = root
					t.owner = superuser
					added += 1
			db.commit()
			return added

		def get_templates(dirpath,webpath=""):
			added = 0
			for fn in os.listdir(dirpath):
				if fn.startswith("."):
					continue
				newdirpath = os.path.join(dirpath,fn)
				newwebpath = "{}/{}".format(webpath,fn) if webpath else fn
				if os.path.isdir(newdirpath):
					added += get_templates(newdirpath,newwebpath)
				else:
					added += get_template(newdirpath,newwebpath)
			return added

		added = 0
		get_templates(TEMPLATE_PATH)
		logger.debug("{} templates changed.".format(added))

		## Variables.
		## Generic code because it doesn't hurt and may be used for Blueprint vars later.
		def add_vars(gen,parent):
			"""Add variables. The generator yields (name,value,docstring) triples."""
			
			added=[]
			for k,v,d in gen:
				try:
					cf = ConfigVar.q.get_by(name=k, parent=parent)
				except NoData:
					cf = ConfigVar(parent=parent, name=k, value=v, info=d)
					db.flush()
					added.append(k)
				else:
					if not cf.info or force:
						cf.info = d
			if added:
				logger.info("New variables for {}: ".format(str(parent))+",".join(added))
			else:
				logger.debug("No new variables for {} necessary.".format(str(parent)))
			db.commit()

		## Set default variables
		def gen_vars():
			from pybble.core import default_settings as DS
			for k,v in DS.__dict__.items():
				if k != k.upper(): continue
				if k in app.config: # add overrides
					v = app.config[k]
				yield text_type(k),v,getattr(DS,'d_'+k,None)
		add_vars(gen_vars(),root)

		from ..app import list_apps
		from ..blueprint import list_blueprints
		from ..core.models.site import App,Blueprint,SiteBlueprint
		loadables(list_apps,App,"pybble.app")
		loadables(list_blueprints,Blueprint,"pybble.blueprint")

		for bp in Blueprint.q.all():
			mod = sys.modules[bp.mod.__module__]
			path = os.path.join(mod.__path__[0], 'templates')
			added = get_templates(path, bp.name)
			if added:
				logger.info("{} templates for {} added/changed.".format(added,bp.name))
			else:
				logger.debug("No new/changed templates for {}.".format(bp.name))

			if hasattr(mod,"PARAMS"):
				## Set default variables
				def gen_vars():
					from pybble.manager import default_settings as DS
					for k,v in DS.__dict__.items():
						if k != k.upper(): continue
						yield text_type(k),v,getattr(DS,'d_'+k,None)
				add_vars(mod.PARAMS,bp)

			else:
				logger.debug("No parameters in {}.".format(bp.name))
		
		rapp = App.q.get_by(name="_root")
		if root.app is None or force:
			if root.app is not rapp:
				root.app = rapp
				logger.debug("Root site's app set.")
				db.commit()

		aapp = App.q.get_by(name="_alias")
		import socket
		hostname = text_type(socket.gethostname())
		try:
			asite = Site.q.get_by(domain=hostname)
		except NoData:
			asite = Site(name="root alias", domain=hostname)
			asite.app = aapp
			logger.info("Root site aliased ‘{}’ created.".format(hostname))
		db.commit()

		try:
			root_bp = Blueprint.q.get_by(name="_root")
		except NoData:
			logger.error("The ‘_root’ blueprint is not present. Setup is incomplete!")
		else:
			try:
				rbp = SiteBlueprint.q.get_by(site=root,blueprint=root_bp,path="/")
			except NoData:
				rbp = SiteBlueprint(site=root,blueprint=root_bp,path="/")
				logger.debug("Root site's blueprint created.")
		db.commit()

		logger.debug("Setup finished.")

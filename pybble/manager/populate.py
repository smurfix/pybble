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
import re
from traceback import print_exc,format_exc

from sqlalchemy import or_

from flask import request,current_app
from flask._compat import text_type,string_types
from werkzeug import import_string

from .. import TEMPLATE_PATH, STATIC_PATH
from ..utils import random_string
from ..core import config
from ..core.utils import attrdict
from ..core.db import db, NoData
from . import Manager,Command,Option

logger = logging.getLogger('pybble.manager.populate')

_metadata = re.compile('##:?(\S+) *[ :] *(.*)\n') # re.U ?

upload_content_types = [
	## MIME type,subtype, file extension, name, description
	('text','html','html','Web page',"A complete HTML-rendered web page"),
	('text','plain','txt','Plain text',"raw text, no formatting"),
    ('text','javascript','js',"JavaScript",None),
    ('text','css','css',"CSS",None),
    ('image','png','png',"PNG image",None),
    ('image','jpeg','jpg',"JPEG image",None),
    ('image','jpeg','jpeg',"JPEG image",None),
    ('image','gif','gif',"GIF image",None),
    ('application','binary','bin',"raw data",None),
    ('application','pdf','pdf',"PDF document",None),
]
content_types = upload_content_types+[
    ('application','rss+xml','rss',"RSS feed",None),
    ('text','xml','xml',"XML data",None),
    ('message','rfc822',None,"Email message",None),

    ('pybble','_empty',None,"no data",None),

    ('pybble','*',None,"any pybble data",None),
    ('html','*',None,"any html data",None),
    ('text','*',None,"any text data",None),

    ('html','subpage',None,"a (main) part of a webpage",None),
    ('html','string',None,"a short string describing an object",None),
    ('html','detail',None,"a tabular view of an object's internal state",None),
    ('html','snippet',None,"a fragment for the explore view",None),
    ('html','hierarchy',None,"a fragment for hierarchical view within a page",None),
    ('html','hierarchy',None,"a fragment for hierarchical view within a page",None),
    ('html','preview',None,"a view for previewing",None),
    ('html','edit',None,"the form for editing",None),
    ('xml','rss',None,"a fragment for the RSS feed",None),
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
		from ..core.models import Discriminator
		from ..core.models import PERM_ADMIN,PERM_READ,PERM_ADD
		from ..core.models import TM_DETAIL_SUBPAGE,TM_DETAIL_DETAIL,TM_DETAIL_HIERARCHY,TM_DETAIL_RSS,TM_DETAIL_STRING,TM_DETAIL_EMAIL,TM_DETAIL_SNIPPET,TM_DETAIL_PREVIEW,TM_DETAIL_id
		from ..core.models._descr import D
		from ..core.models.site import Site
		from ..core.models.storage import Storage
		from ..core.models.files import BinData,StaticFile
		from ..core.models.user import User,Permission,Group,Member
		from ..core.models.types import MIMEtype,MIMEtranslator,MIMEadapter
		from ..core.models.template import Template,TemplateMatch
		from ..core.models.config import ConfigVar
		from ..core.models.verifier import VerifierBase
		from ..core.models.tracking import Delete
		from ..core.users import create_user
		from .. import ROOT_SITE_NAME,ROOT_USER_NAME, ANON_USER_NAME

		if 'MEDIA_PATH' not in config:
			raise RuntimeError("You have to set MEDIA_PATH so that I can store my files somewhere")

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

		## MIME types for Pybble objects
		count = added = updated = 0
		for id,name in D.items():
			count += 1
			doc = D._doc.get(id,None)
			path = "pybble.core.models."+name
			name = name.rsplit(".")[-1]
			try:
				d = MIMEtype.q.get_by(typ="pybble",subtyp=name.lower())
			except NoData:
				d = MIMEtype(id=id,typ="pybble",subtyp=name.lower(), path=path, doc=doc)
				added += 1
			else:
				d.path = path
				if (doc and (d.doc is None or d.doc != doc)) or force:
					d.doc = doc
					updated += 1
		db.commit()
		if count == added:
			logger.debug("PybbleMIME types have been loaded.")
		elif added or updated:
			logger.debug("{}/{} PybbleMIME types updated/added.".format(updated,added))

		## main site
		try:
			try:
				root = Site.q.get(Site.parent==None,Site.owner!=None)
			except NoData:
				root = Site.q.get(name=ROOT_SITE_NAME)
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
		if User.q.filter_by(parent=root, username=ANON_USER_NAME).count():
			logger.debug("An anon user exists. Good.")
		else:
			User(ANON_USER_NAME, parent=root)
			logger.debug("An initial anon user has been created.")
		db.commit()

		## anon group
		try:
			anon = Group.q.get_by(parent=root, owner=root, name=ANON_USER_NAME)
		except NoData:
			anon = Group(parent=root, owner=root, name=ANON_USER_NAME)
			logger.debug("An anon user group has been created.")
		else:
			logger.debug("The anon user group exists. Good.")

		## check membership
		for a in User.q.filter_by(parent=root, username=ANON_USER_NAME):
			try:
				Member.q.get_by(parent=anon, owner=a)
			except NoData:
				Member(parent=anon, owner=a)
				logger.warn("{} was added to the anon group".format(a))
			else:
				logger.debug("{} is an anon-group member".format(a))

		## main user
		superuser = root.owner
		if superuser is None or force:
			try:
				superuser = User.q.get_by(username=ROOT_USER_NAME, parent=root)
			except NoData:
				password = random_string()
				superuser = create_user(site=root,name=ROOT_USER_NAME,password=password)
				db.commit()
				logger.info(u"The root user has been created. Password: ‘{}’.".format(password))
			else:
				if root.owner != superuser:
					logger.warning(u"The root user is not ({}, not {}). This is strange.".format(root.owner,superuser))
			root.owner = superuser
			db.flush()
		elif superuser.username != ROOT_USER_NAME:
			logger.warn(u"The root site's owner is ‘{}’, not ‘{}’".format(superuser.username,ROOT_USER_NAME))
		else:
			logger.debug("The root user exists. Good.")
		if superuser.email is None or force:
			if superuser.email is not None:
				logger.info(u"The main admin email changed from ‘{}’ ro ‘{}’".format(superuser.email,config.ADMIN_EMAIL))
			superuser.email = text_type(config.ADMIN_EMAIL)
		db.commit()
		request.user = superuser

		## more MIME types
		added=0
		for typ,subtyp,ext,name,doc in content_types:
			try:
				mt = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
			except NoData:
				mt = MIMEtype(typ=typ, subtyp=subtyp, ext=ext, name=name, doc=doc)
				logger.info("MIME type ‘{}’ ({}) created.".format(mt,name))
				added += 1
			else:
				if mt.doc is None or force:
					mt.doc = doc
		if not added:
			logger.debug("No new MIME types necessary.")

		for mt in MIMEtype.q.all():
			if mt.superparent is None and Delete.q.filter_by(parent=mt).count() == 0:
				mt.superparent = root
		db.commit()
		
		## MIME translators
		def get_them(types, add=False):
			if isinstance(types,string_types):
				types = (types,)
			for s in types:
				mt = MIMEtype.get(s, add=add)
				if mt.subtyp == "*":
					yield mt,10
					for r in MIMEtype.q.filter_by(typ=mt.typ):
						if r.subtyp == '*' or r.subtyp.startswith('_'):
							continue
						yield mt,50
				else:
					yield mt,0

		def translators(lister,path="pybble.translator"):
			added=found=0
			for name in lister():
				name = text_type(name)
				found += 1
				is_new = False
				mpath = "{}.{}.{}".format(path,name,"Translator")
				mod = "??"
				try:
					E=mpath
					mod = import_string(mpath)
					E=mod.SOURCE
					src = get_them(mod.SOURCE, add=True)
					E=mod.DEST
					dst = get_them(mod.DEST, add=True)
					E=mod.CONTENT
					mt = MIMEtype.get(mod.CONTENT, add=True)
					E="??"
					w = mod.WEIGHT
				except NoData as e:
					logger.warn("{} is not usable ({}): {}\n{}".format(mod,E,str(e), format_exc()))
					continue
				try:
					trans = MIMEtranslator.q.get_by(path=mpath)
				except NoData:
					trans = MIMEtranslator(path=mpath,mime=mt,weight=w,name=mpath)
				else:
					if trans.mime != mt:
						logger.warn("{} has a broken type: {} instead of {}".format(mod,trans.mime,mt))
						if force:
							trans.mime = mt
					if force:
						trans.weight=w

				for s,sw in src:
					for d,dw in dst:
						n = "{} to {} with {}".format(src,dst,mt)
						w=sw+dw
						try:
							obj = MIMEadapter.q.get_by(from_mime=s,to_mime=d,translator=trans)
						except NoData:
							obj = MIMEadapter(from_mime=s,to_mime=d,translator=trans,name=n,weight=w)
							added += 1
						else:
							if force:
								obj.weight = w
								obj.name = n
			if not found:
				logger.warn("{}: None found".format(MIMEtranslator.__name__))
			else:
				logger.info("{}: {} new".format(MIMEtranslator.__name__,added))
			db.commit()

		## Variable installer.
		## Generic code because it doesn't hurt and may be used for Blueprint vars later.
		def add_vars(gen,parent):
			"""Add variables. The generator yields (name,value,docstring) triples."""
			
			added=[]
			for k,v,d in gen:
				try:
					cf = ConfigVar.q.get_by(name=k, parent=parent)
				except NoData:
					cf = ConfigVar(parent=parent, name=k, value=v, doc=d)
					db.flush()
					added.append(k)
				else:
					if not cf.doc or force:
						cf.doc = d
			if added:
				logger.info("New variables for {}: ".format(str(parent))+",".join(added))
			else:
				logger.debug("No new variables for {} necessary.".format(str(parent)))
			db.commit()

		## helper to load known apps, blueprints
		def loadables(lister,Obj,path, iname=None,add_vars=add_vars,root=root):
			if iname is None:
				iname = Obj.__name__
			added=changed=found=0
			for name in lister():
				name = text_type(name)
				found += 1
				is_new = False
				try:
					obj = Obj.q.get_by(name=name)
				except NoData:
					obj = Obj(name=name, path="{}.{}.{}".format(path,name,iname))
					is_new = True
				if force or obj.superparent is None:
					obj.superparent = root
				try:
					a = obj.mod
				except Exception as e:
					logger.warn("{} ({}) is not usable: {}\n{}".format(iname,obj.path,str(e), format_exc()))
					if is_new:
						# Dance 
						db.flush((obj,))
						db.delete(obj)
				else:
					if obj.doc is None or force:
						try:
							obj.doc = a.__doc__
						except AttributeError:
							pass

					if hasattr(a,"PARAMS"):
						## Set default variables
						add_vars(a.PARAMS,obj)

					else:
						logger.debug("No parameters in {}.".format(obj.path))
				
			if not found:
				logger.warn("{}: None found".format(Obj.__name__))
			elif not changed and not added:
				logger.debug("{}: {} found, No changes".format(Obj.__name__,found))
			else:
				logger.info("{}: {} new, {} updated".format(Obj.__name__,added,changed))
			db.commit()

		from ..verifier import list_verifiers
		loadables(list_verifiers,VerifierBase,"pybble.verifier","Verifier")

		from ..translator import list_translators
		translators(list_translators)

		## static files (recursive)
		def add_files(dir,path):
			added=0
			for f in os.listdir(dir):
				if f.startswith("."):
					continue
				f = f.decode("utf-8")
				filepath = os.path.join(dir,f)
				if path:
					webpath = path+'/'+f
				else:
					webpath = f
				if os.path.isdir(filepath):
					added += add_files(filepath,webpath)
					continue
				dot = f.rindex(".")
				mime = MIMEtype.get(f[dot+1:])
				with open(filepath,"rb") as fd:
					content = fd.read()
					try:
						sb = BinData.lookup(content)
					except NoData:
						sb = BinData(f[:dot],ext=f[dot+1:],content=content, storage=st)

					try:
						try:
							sf = StaticFile.q.get_by(path=webpath,superparent=root)
						except NoData:
							sf = StaticFile.q.get_by(path='/'+webpath,superparent=root)
					except NoData:
						sf = StaticFile(webpath,sb)
					else:
						if sf.path.startswith('/'):
							sf.path = sf.path[1:] # silently fix this

						try:
							c = sf.content
						except EnvironmentError as e:
							import errno
							if e.errno != errno.ENOENT:
								raise
							logger.error("File ‘{}’ vanished".format(filepath))
							sf.bindata.hash = None
							sf.bindata.record_deletion("file vanished")
							db.flush()

							sb = BinData(f[:dot],ext=f[dot+1:],content=content, storage=st)
							osb = sf.bindata
							sf.bindata = sb
							sf.record_change({"bindata":[osb,sb]},"file vanished")
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

		## templates
		def read_template(parent, filepath,webpath, inferred=""):
			extmap = { 'haml':'template/haml', 'html':'template/jinja' }

			added = 0
			with file(filepath) as f:
				try:
					data = inferred + f.read().decode("utf-8")
				except Exception:
					print("While reading",filepath,file=sys.stderr)
					raise

			hdr = attrdict(match=[],inherit=None)
			m = _metadata.match(data)
			while m:
				k,v = m.groups()
				ov = hdr.get(k,None)
				if ov is None:
					if v == "-":
						v = None
					elif '/' in v:
						v = MIMEtype.get(v)
					elif v in ("True False 0 1 None".split()):
						v = eval(v)
					elif k == "weight":
						v = int(v)
					hdr[k] = v
				elif k == "match":
					hdr[k].append((v,hdr.inherit))
				else:
					raise ValueError("Template ‘{}’: duplicate metadata key ‘{}’".format(filepath,k))
				data = data[m.end():]
				m = _metadata.match(data)

			if "src" not in hdr: hdr.src = "pybble/_empty"
			if "dst" not in hdr: hdr.dst = "html/*"
			if "named" not in hdr: hdr.named = True
			if "dsc" not in hdr: hdr.dsc = None
			if "weight" not in hdr: hdr.weight = 0
			if "typ" not in hdr:
				try:
					dot = filepath.rindex(".")
					hdr.typ = MIMEtype.get(extmap[filepath[dot+1:]])
				except (ValueError,KeyError,NoData):
					logger.error("Template ‘{}’ not loaded: unknown MIME type".format(filepath))
					return added

			hdr_src = MIMEtype.get(hdr.src)
			hdr_dst = MIMEtype.get(hdr.dst)
			hdr_typ = MIMEtype.get(hdr.typ)
			hdr_dsc = TM_DETAIL_id(hdr.dsc) if hdr.dsc is not None else None
			n="{} from {} to {}".format(hdr_typ,hdr_src,hdr_dst)

			try:
				tr = MIMEtranslator.q.get_by(mime=hdr_typ)
			except NoData:
				logger.error("Template ‘{}’ not loaded: no translator which understands {}".format(filepath,hdr_typ))
				return added
			try:
				a = MIMEadapter.q.get_by(from_mime=hdr_src, to_mime=hdr_dst, translator=tr)
			except NoData:
				a = MIMEadapter(from_mime=hdr_src, to_mime=hdr_dst, translator=tr, name=n)

			try:
				t = Template.q.get_by(source=filepath)
			except NoData:
				t = Template(source=filepath, data=data, parent=parent, adapter=a, weight=hdr.weight or 0)
				t.owner = superuser
				if hdr.named:
					t.name = webpath
				added += 1
			else:
				chg = 0
				if t.parent is not parent:
					logger.warn("Template {} ‘{}’: changed parent from {} to {}".format(t.id, filepath, t.parent,parent))
					if force:
						t.parent = parent
						chg = 1

				if t.adapter is not a:
					logger.warn("Template {} ‘{}’: changed adapter from {} to {}".format(t.id, filepath, t.adapter,a))
					if force:
						t.adapter = a
						chg = 1

				if t.content != data:
					logger.warn(u"Template {} ‘{}’ differs.".format(t.id,filepath))
					if force:
						t.data = data
						chg = 1

				if force:
					t.owner = superuser
					t.weight = hdr.weight
					added += chg
			for m,inherit in hdr.match:
				if m == "root":
					m = root
				elif m == "superuser":
					m = superuser
				else:
					logger.warn("Template {} ‘{}’: I don't know how to attach to {}".format(t.id, filepath, m))

				try:
					tm = TemplateMatch.q.filter_by(template=t,obj=m,for_discr=hdr_dsc).filter(or_(TemplateMatch.inherit == None,TemplateMatch.inherit==inherit)).one()
				except NoData:
					tm = TemplateMatch(template=t,obj=m,for_discr=hdr_dsc,inherit=inherit)

			db.commit()
			return added

		def find_templates(parent, dirpath,webpath="",mapper=""):
			if not os.path.isdir(dirpath):
				return 0

			added = 0
			for fn in os.listdir(dirpath):
				if fn.startswith("."):
					continue
				newdirpath = os.path.join(dirpath,fn)
				newwebpath = "{}/{}".format(webpath,fn) if webpath else fn
				m=mapper
				if os.path.isdir(newdirpath):
					if m: m=m.do_dir(fn)
					added += find_templates(parent, newdirpath,newwebpath,m)
				else:
					if m: m=m.do_file(fn)
					added += read_template(parent, newdirpath,newwebpath,m)
			return added

		class M(object):
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
		added = find_templates(root, TEMPLATE_PATH,mapper=M())
		logger.debug("{} templates changed.".format(added))

		## Set default variables
		def gen_vars():
			from pybble.core import default_settings as DS
			for k,v in DS.__dict__.items():
				if k != k.upper(): continue
				if k in app.config: # add overrides
					v = app.config[k]
				yield text_type(k),v,getattr(DS,'d_'+k,None)
		add_vars(gen_vars(),root)

		## built-in Apps and Blueprints
		from ..app import list_apps
		from ..blueprint import list_blueprints
		from ..core.models.site import App,Blueprint,SiteBlueprint

		loadables(list_apps,App,"pybble.app")
		for app in App.q.all():
			try:
				mod = sys.modules[app.mod.__module__]
				try:
					mp = os.path.dirname(mod.__file__)
				except AttributeError:
					mp = mod.__path__[0]
				path = os.path.join(mp, 'templates')
				added = find_templates(app, path)
				if added:
					logger.info("{} templates for app {} added/changed.".format(added,app.name))
				else:
					logger.debug("No new/changed templates for app {}.".format(app.name))
			except Exception:
				print("Error trying to load app ‘{}’".format(app.path), file=sys.stderr)
				print_exc()
				sys.exit(1)

		loadables(list_blueprints,Blueprint,"pybble.blueprint")
		for bp in Blueprint.q.all():
			try:
				mod = sys.modules[bp.mod.__module__]
				try:
					mp = os.path.dirname(mod.__file__)
				except AttributeError:
					mp = mod.__path__[0]
				path = os.path.join(mp, 'templates')
				added = find_templates(bp, path)
				if added:
					logger.info("{} templates for blueprint {} added/changed.".format(added,bp.name))
				else:
					logger.debug("No new/changed templates for blueprint {}.".format(bp.name))
			except Exception:
				print("Error trying to load blueprint ‘{}’".format(bp.path), file=sys.stderr)
				print_exc()
				sys.exit(1)

		## Basic permissions
		s=root
		u=root.owner
		for d in Discriminator.q.all():
			if Permission.q.filter(Permission.for_discr==d,Permission.right>=PERM_ADMIN, Permission.parent==root).count():
				continue
			p=Permission(u, s, d, PERM_ADMIN)
			p.superparent=s
		db.flush()

		dw = Discriminator.q.get_by(name="WikiPage")
		ds = Discriminator.q.get_by(name="Site")
		dp = Discriminator.q.get_by(name="Permission")
		dk = Discriminator.q.get_by(name="Comment")
		dt = Discriminator.q.get_by(name="WantTracking")
		dd = Discriminator.q.get_by(name="BinData")

		a = anon
		for d in (dw,ds,dt,dd):
			if not Permission.q.filter(Permission.for_discr==d,Permission.right>=0,Permission.owner==a, Permission.parent==s).count():
				p=Permission(a, s, d, PERM_READ)
				p.superparent=s
			if not Permission.q.filter(Permission.for_discr==d,Permission.right>=0,Permission.owner==s, Permission.parent==s).count():
				p=Permission(s, s, d, PERM_READ)
				p.superparent=s

		for d,e in ((ds,dd),(dw,dd),(ds,dw),(ds,dp),(dw,dw),(dw,dp),(dw,dk),(dk,dk),(ds,dt)):
			if Permission.q.filter(Permission.new_discr==e,Permission.for_discr==d, Permission.parent==s).count():
				continue
			p=Permission(u, s, d, PERM_ADD)
			p.new_discr=e
			p.superparent=s

			# View templates
			#for addon in self.addons:
			#	for cls in addon.__dict__.values():
			#		if not(isinstance(cls,type) and issubclass(cls,Object)):
			#			continue
			#		if cls.__name__ not in addon.__ALL__:
			#			continue
			#		if db.filter_by(Permission, discr=cls.cls_discr()).count():
			#			continue
			#		p=Permission(u, s, ds, PERM_ADMIN)
			#		p.new_discr=cls.cls_discr()
			#		p.superparent=s
			#		db.store.add(p)
			#
			#		p=Permission(u, s, ds, PERM_ADD)
			#		p.new_discr=cls.cls_discr()
			#		p.superparent=s

			db.flush()

		## Add uplaod permissions
		#for typ,subtyp,ext,name,doc in upload_content_types:
		#	mt = MIMEtype.q.get_by(typ=typ,subtyp=subtyp)
		#	if Permission.q.filter(Permission.new_discr==e,Permission.for_discr==d, Permission.parent==s).count():
		#		continue
		#	p=Permission(u, s, d, PERM_ADD)
		#	p.new_discr=e
		#	p.superparent=s
#
#			/perm


		## possible root app fix-ups
		rapp = App.q.get_by(name='_root')
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
			root_bp = Blueprint.q.get_by(name='_root')
		except NoData:
			logger.error("The ‘_root’ blueprint is not present. Setup is incomplete!")
		else:
			try:
				rbp = SiteBlueprint.q.get_by(site=root,blueprint=root_bp,path="/")
			except NoData:
				rbp = SiteBlueprint(site=root,blueprint=root_bp,path="/",name="pybble")
				logger.debug("Root site's content blueprint created.")
			else:
				if rbp.name != "pybble" and force:
					logger.warn("Root site's blueprint name changed from ‘{}’ to ‘pybble’.".format(rbp.name))
					rbp.name = "pybble"
				if rbp.endpoint != "pybble" and force:
					logger.warn("Root site's static blueprint endpoint changed from ‘{}’ to ‘pybble’.".format(rbp.name))
					rbp.endpoint = "pybble"
		db.commit()

		try:
			static_bp = Blueprint.q.get_by(name='static')
		except NoData:
			logger.error("The ‘static’ blueprint is not present. Setup is incomplete!")
		else:
			try:
				rbp = SiteBlueprint.q.get_by(site=root,blueprint=static_bp,path="/")
			except NoData:
				rbp = SiteBlueprint(site=root,blueprint=static_bp,path="/",name="static",endpoint="")
				logger.debug("Root site's static blueprint created.")
			else:
				if rbp.name != "static" and force:
					logger.warn("Root site's static blueprint name changed from ‘{}’ to ‘static’.".format(rbp.name))
					rbp.name = "static"
				if rbp.endpoint != "" and force:
					logger.warn("Root site's static blueprint endpoint changed from ‘{}’ to ‘static’.".format(rbp.name))
					rbp.endpoint = ""
		db.commit()

		## All done!
		logger.debug("Setup finished.")

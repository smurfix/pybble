# -*- coding: utf-8 -*-

from __future__ import with_statement
from werkzeug import Request, ClosingIterator
from werkzeug.exceptions import HTTPException, NotFound, Unauthorized
from pybble.utils import STATIC_PATH, local, local_manager, \
	 TEMPLATE_PATH, AuthError, all_addons
from pybble.render import expose_map, url_map, send_mail, expose
from pybble.database import db, NoResult, dsn, database
from storm.locals import Store,And,Or

import pybble.models
import pybble.admin
import pybble.part.wikipage
import pybble.part.permission
import pybble.part.wanttracking
import pybble.part.usertracker
import pybble.part.change
import pybble.rss
from pybble.session import add_session, add_user, add_site, save_session, \
	add_response_headers

import StringIO
from pybble import _settings as settings
import sys,os
from datetime import datetime

## Adapters
from pybble import views,login,confirm

def setup_code_env(site):
	from pybble import utils
	environ = {}
	environ['wsgi.url_scheme'] = "http"
	environ['SERVER_PORT'] = "80"
	environ['SERVER_NAME'] = site.domain
	environ['REQUEST_METHOD'] = "GET"
	utils.current_request.site = site
	utils.local.url_adapter = url_map.bind_to_environ(environ)

extensions = ( \
	("js","text/javascript","JavaScript"), \
	("css","text/css","CSS"), \
	("html","text/html","HTML"), \
	("txt","text/plain","plain text"), \
	("dtd","application/xml-dtd","DTD"), \
	("png","image/png","PNG image"), \
	("jpg","image/jpeg","JPEG image"), \
	("jpeg","image/jpeg","JPEG image"), \
	("gif","image/gif","GIF image"), \
	("bin","application/binary","raw data"), \
)

class Pybble(object):

	def __init__(self):
		local.application = self
		self.addons = []
		for addon in all_addons():
			self.addons.append(addon)


	def init_database(self):
		def action():
			"""Initialize or update the database"""
			raise NotImplementedError("Do this manually")
		return action
		
	def init_site_replace(self):
		return self.init_site(replace_templates=True)

	def init_site(self, replace_templates=False):
		def action(domain=("d","localhost:5000"),name=("n",u"local debug site")):

			"""Initialize a new site"""
			# ... or in fact the first one

			from pybble.models import Site,User,Object,Discriminator,Template,TemplateMatch,VerifierBase,WikiPage,Storage,BinData,StaticFile
			from pybble.models import Group,Permission, add_mime,mime_ext, Renderer
			from pybble.models import TM_DETAIL_SUBPAGE, PERM_READ,PERM_ADMIN,PERM_ADD, TM_DETAIL_DETAIL, TM_DETAIL, TM_DETAIL_SNIPPET, TM_DETAIL_HIERARCHY, TM_DETAIL_RSS, TM_DETAIL_EMAIL, TM_DETAIL_STRING
			from pybble import utils
			from werkzeug import Request

			utils.local.request = Request({})
			utils.local.store = Store(database)

			for rn in (u"markdown",):
				rc = "pybble.render.render_"+rn
				try:
					r = db.get_by(Renderer, name=rn)
				except NoResult:
					r = Renderer(rn,rc)
					db.store.add(r)
				else:
					if r.cls != rc:
						print "Warning: Renderer '%s' differs (%s | %s)." % (rn,r.cls,rc)
						if replace_templates:
							r.cls = rc

			db.store.flush()

			from pybble import models as m
			for k,v in m._discr2cls.iteritems():
				try:
					o=db.get_by(Discriminator, id=k)
				except NoResult:
					o=Discriminator(v)
					db.store.add(o)
				else:
					if o.name != v.__name__:
						raise ValueError("Discriminator '%d' pointed at '%s', now '%s'!" % (k,o.name,v.__name__))
					try:
						n = v._display_name
					except AttributeError:
						pass
					else:
						o.display_name = unicode(n)
			del m
			db.store.flush()

			domain=domain.decode("utf-8")
			try:
				s=db.get_by(Site, domain=domain)
			except NoResult:
				s=Site(domain,name=name)
				db.store.add(s)
			else:
				print u"%s found." % s

			utils.current_request.site = s

			for ext,typ,name in extensions:
				typ,subtyp = typ.split("/",1)
				add_mime(name,typ,subtyp,ext)
			db.store.flush()

			try:
				st = db.get_by(Storage, name=u"Pybble")
			except NoResult:
				try:
					st = db.get_by(Storage, name=u"Test")
				except NoResult:
					st = Storage("Test","/var/tmp/testkram","localhost:5000/static")
					db.store.add(st)
			else:
				st.superparent = s
			db.store.flush()
			if s.storage is None:
				s.storage = st
				db.store.flush()

			u=s.users.find(User.username==u"root").one()
			if u is None:
				u=User(u"root")
				u.email=settings.ADMIN
				u.sites.add(s)
				db.store.add(u)
			else:
				print u"%s found." % u

			db.store.flush()
			u.verified=True
			u.parent = s
			db.store.flush()
			if s.owner != u:
				s.owner = u
				db.store.flush()
			utils.current_request.user = u

			def add_files(dir,path):
				for f in os.listdir(dir):
					if f.startswith("."):
						continue
					f = f.decode("utf-8")
					fp = os.path.join(dir,f)
					dp = os.path.join(path,f)
					if os.path.isdir(fp):
						add_files(fp,dp)
						continue
					dot = f.rindex(".")
					mime = mime_ext(f[dot+1:])
					with open(fp,"rb") as fd:
						content = fd.read()
						try:
							sb = BinData.lookup(content)
						except NoResult:
							sb = BinData(f[:dot],ext=f[dot+1:],content=content, storage=st)
							db.store.add(sb)

						try:
							sf = db.get_by(StaticFile, path=dp,superparent=s)
						except NoResult:
							sf = StaticFile(dp,sb)
							db.store.add(sf)
						else:
							c = sf.content
							if content != sf.content:
								print "Warning: StaticFile '%s' differs." % (dp,)
								if replace_templates:
									sf.bindata.record_deletion("replaced by update")
									sf.record_deletion("replaced by update")
									sf = StaticFile(dp,sb)
									db.store.add(sf)


			add_files(os.path.join(u"pybble",u"static"),u"")
		
			try:
				a=db.get_by(User, superparent=s, username=u"")
			except NoResult:
				a=User(u"", password=u"")
				a.owner = u
				a.superparent = s
				a.sites.add(s)
				db.store.add(a)
			else:
				print u"%s found." % a

			db.store.flush()
			a.verified=False

			db.store.flush()

			for d in db.store.find(Discriminator):
				if db.store.find(Permission,And(Permission.discr==d.id,Permission.right>=0)).count():
					continue
				p=Permission(u, s, d, PERM_ADMIN)
				p.superparent=s
				db.store.add(p)
			db.store.flush()

			dw = db.get_by(Discriminator, name="WikiPage")
			ds = db.get_by(Discriminator, name="Site")
			dp = db.get_by(Discriminator, name="Permission")
			dk = db.get_by(Discriminator, name="Comment")
			dt = db.get_by(Discriminator, name="WantTracking")
			dd = db.get_by(Discriminator, name="BinData")

			for d in (dw,ds,dt,dd):
				if db.store.find(Permission, And(Permission.discr==d.id,Permission.right>=0,Permission.owner_id==a.id)).count():
					continue
				p=Permission(a, s, d, PERM_READ)
				p.superparent=s
				db.store.add(p)

			for d,e in ((ds,dd),(dw,dd),(ds,dw),(ds,dp),(dw,dw),(dw,dp),(dw,dk),(dk,dk),(ds,dt)):
				if db.store.find(Permission,And(Permission.new_discr==e.id,Permission.discr==d.id)).count():
					continue
				p=Permission(u, s, d, PERM_ADD)
				p.new_discr=e.id
				p.superparent=s
				db.store.add(p)

			# View templates
			for addon in self.addons:
				for cls in addon.__dict__.values():
					if not(isinstance(cls,type) and issubclass(cls,Object)):
						continue
					if cls.__name__ not in addon.__ALL__:
						continue
					if db.filter_by(Permission, discr=cls.cls_discr()).count():
						continue
					p=Permission(u, s, ds, PERM_ADMIN)
					p.new_discr=cls.cls_discr()
					p.superparent=s
					db.store.add(p)

					p=Permission(u, s, ds, PERM_ADD)
					p.new_discr=cls.cls_discr()
					p.superparent=s
					db.store.add(p)

			db.store.flush()

			def get_template(fn):
				with file(os.path.join(TEMPLATE_PATH,fn)) as f:
					try:
						data = f.read().decode("utf-8")
					except Exception:
						print >>sys.stderr,"While reading",fn
						raise

				fn = unicode(fn)
				try:
					t = db.get_by(Template, name=fn,parent=s)
				except NoResult:
					t = Template(name=fn,data=data,parent=s)
					t.owner = u
					db.store.add(t)
				else:
					if t.data != data:
						print "Warning: Template '%s' differs." % (fn,)
						if replace_templates:
							t.data = data
					if replace_templates:
						t.superparent = s
						t.owner = u

			for fn in os.listdir(TEMPLATE_PATH):
				if fn.startswith(".") or (not fn.endswith(".html") and not fn.endswith(".txt") and not fn.endswith(".xml")):
					continue
				get_template(fn)

			for fn in os.listdir(os.path.join(TEMPLATE_PATH,"edit")):
				if fn.startswith(".") or not fn.endswith(".html"):
					continue
				get_template(os.path.join("edit",fn))

			db.store.flush()

			VerifierBase.register("register","pybble.login.verifier")
			db.store.flush()


			with file(os.path.join("doc","TOC.txt")) as f:
				try:
					data = f.read().decode("utf-8")
				except Exception:
					print >>sys.stderr,"While reading",fn
					raise
			
			try:
				w = db.get_by(WikiPage, name=u"Documentation",superparent=s)
			except NoResult:
				w = WikiPage(u"Documentation",data)
				w.owner=u
				w.parent=s
				w.superparent=s
				w.mainpage=True
				db.store.add(w)
			else:
				if w.data != data:
					print "Warning: DocPage 'TOC' differs."
					if replace_templates:
						w.data = data
				if not w.superparent:
					w.superparent=s

			for fn in os.listdir("doc"):
				if fn.startswith("."):
					continue
				if fn == "TOC.txt":
					continue
				if not fn.endswith(".txt"):
					continue
				fn = fn.decode("utf-8")
				with file(os.path.join("doc",fn)) as f:
					try:
						data = f.read().decode("utf-8")
					except Exception:
						print >>sys.stderr,"While reading",fn
						raise
				fn = unicode(fn[:-4])
				
				try:
					ww = db.get_by(WikiPage, name=fn,parent=w)
				except NoResult:
					ww = WikiPage(fn,data)
					ww.owner=u
					ww.parent=w
					ww.superparent=s
					ww.mainpage=False
					db.store.add(ww)
				else:
					ww.superparent=s
					ww.mainpage=False
					if ww.data != data:
						print "Warning: DocPage '%s' differs." % (fn,)
						if replace_templates:
							ww.data = data

			db.store.flush()
			for d in db.store.find(Discriminator):
				for detail,name in ((TM_DETAIL_SUBPAGE,"view"),
					(TM_DETAIL_DETAIL,"details"),
					(TM_DETAIL_HIERARCHY,"hierarchy"),
					(TM_DETAIL_RSS,"rss"),
					(TM_DETAIL_STRING,"linktext"),
					(TM_DETAIL_EMAIL,"email"),
					(TM_DETAIL_SNIPPET,"snippet")):
					try:
						data = open("pybble/templates/%s/%s.html" % (name,d.name.lower(),)).read().decode("utf-8")
					except (IOError,OSError):
						pass
					else:
						try:
							t = db.get_by(TemplateMatch, obj_id=s.id, discr=d.id, detail=detail)
						except NoResult:
							t = TemplateMatch(obj=s, discr=d.id, detail=detail, data=data)
							db.store.add(t)
						else:
							if t.data != data:
								print "Warning: AssocTemplate '%s/%s.html' differs." % (name,d.name.lower())
								if replace_templates:
									t.data = data
					db.store.flush()

			for addon in self.addons:
				try: ai = addon.initsite
				except AttributeError: pass
				else: ai(replace_templates)

				# Named templates
				try: at = addon.TEMPLATES
				except AttributeError: pass
				else:
					for t in at:
						data = open(os.path.join(addon.__path__[0],t)).read().decode("utf-8")
						fn = u"%s/%s" % (os.path.split(addon.__path__[0])[1],t)
						try:
							t = db.get_by(Template, name=fn,superparent=s)
						except NoResult:
							t = Template(name=fn,data=data)
							t.superparent = s
							t.owner = u
							db.store.add(t)
						else:
							if t.data != data:
								print "Warning: Template '%s' differs." % (fn,)
								if replace_templates:
									t.data = data
							if replace_templates:
								t.superparent = s
								t.owner = u
					db.store.flush()

				# View templates
				for cls in addon.__dict__.values():
					if not(isinstance(cls,type) and issubclass(cls,Object)):
						continue
					if cls.__name__ not in addon.__ALL__:
						continue
					for t,n in TM_DETAIL.items():
						try:
							data = open(os.path.join(addon.__path__[0],"%s.%s.html" % (cls.__name__.lower(),n.lower()))).read().decode("utf-8")
						except (IOError,OSError):
							continue
						else:
							try:
								t = db.get_by(TemplateMatch, obj_id=s.id, discr=cls.cls_discr(), detail=t)
							except NoResult:
								t = TemplateMatch(obj=s, discr=cls.cls_discr(), detail=t, data=data)
								db.store.add(t)
							else:
								if t.data != data:
									print "Warning: AddOn-Template %s: '%s.%s.html' differs." % (addon.__name__, cls.__name__, n.lower())
									if replace_templates:
										t.data = data

			db.store.commit()
			print "Your root user is named '%s' and has the password '%s'." % (u.username, u.password)
		return action

	def trigger(self):
		def action(user=("u",""), site=("s",""), verbose=("v",False)):
			"""Process trigger records."""
			from pybble.models import Site,WantTracking,UserTracker,Tracker,User,Delete,Change
			from pybble import utils

			utils.local.request = Request({})
			utils.local.store = Store(database)

			filter = {}
			if site:
				filter["name"]=site
			
			for s in db.filter_by(Site,**filter):
				setup_code_env(s)
				if user:
					u = db.store.filter_by(User, site=s,name=user).value()
				else:
					u = None
				tq = db.store.filter_by(Tracker, site=s)
				if s.tracked:
					tq = tq.filter(Tracker.timestamp>s.tracked)
				if u:
					tq = tq.filter_by(owner=u)

				for t in tq.order_by(Tracker.timestamp):
					o=t.change_obj
					if o is None:
						print "ChangeObj??",t
						continue
					wq=Or(WantTracking.discr==None,WantTracking.discr==o.discriminator)
					processed = set()
					while o:
						wantq=And(wq, WantTracking.parent==o)
						if processed:
							wantq=And(wantq, Not(Or(*( WantTracking.owner_id == i for i in processed))))

						inew = None
						imod = None
						idel = None
						for w in db.store.find(WantTracking, wantq):
							processed.add(w.owner_id)
							if not w.owner.can_read(t.change_obj):
								continue
							if isinstance(t.parent,Delete):
								if not w.track_del: continue
								idel=t.parent
							elif isinstance(t.parent,Change):
								if not w.track_mod: continue
								imod=t.parent
							else:
								if not w.track_new: continue
								inew=t.parent

							if db.store.filter_by(UserTracker, owner=w.owner, parent=t).count():
								continue
							ut=UserTracker(user=w.owner,tracker=t,want=w)
							db.store.add(ut)
							if w.email:
								utils.local.request.user = ut.owner
								try:
									send_mail(ut.owner.email, 'tracker_email.txt',
										usertracker=ut, tracker=ut.parent,
										user=ut.owner, site=s, watcher=w,
										obj=t.change_obj)
								except AuthError:
									pass

						if o.deleted and isinstance(t.parent,Delete):
							o=t.parent.superparent
						else:
							o=o.parent

					if not u:
						s.tracked=t.timestamp
				db.store.commit()

		return action

	def show(self):
		from pybble.models import TM_DETAIL_EMAIL, TM_DETAIL_RSS
		from pybble.render import jinja_env
		
		def action(obj=("o",""),user=("u",""), site=("s",""), detail=("d",TM_DETAIL_EMAIL), verbose=("v",False)):
			"""Show an object."""
			from pybble.models import Object,obj_get
			from pybble import utils

			utils.local.request = Request({})
			utils.local.store = Store(database)

			obj = obj_get(obj)
			if site:
				s = db.get_by(Site, name=site)
			else:
				s = obj.site
			setup_code_env(s)

			if user:
				u = obj_get(user)
			else:
				u = s.owner
			utils.current_request.user = u

			if detail >= TM_DETAIL_RSS:
				print jinja_env.from_string("{{subrss(obj,detail)}}").render(detail=detail,obj=obj)
			else:
				print jinja_env.from_string("{{subpage(obj,detail)}}").render(detail=detail,obj=obj)

		return action

	def dbscript(self):
		def action(script=("s")):
			"""Run a script on the database."""
			def Do(stmt):
				db.store.execute(stmt)

			execfile(script, globals(),locals())

		return action

	def dispatch(self, environ, start_response):
		local.application = self
		request = Request(environ)
		local.request = request
		if not hasattr(local,"store"):
			local.store = Store(database)
		local.url_adapter = adapter = url_map.bind_to_environ(environ)
		try:
			add_site(request)
			add_session(request)
			add_user(request)

			endpoint, values = adapter.match()
			handler = expose_map[endpoint]
			response = handler(request, **values)
			save_session(request,response)
			db.store.commit()
		except (NotFound,NoResult), e:
			db.store.rollback()
			from traceback import print_exc
			print_exc(file=sys.stderr)
			response = views.not_found(request, request.url)
			response.status_code = 404
		except AuthError, e:
			db.store.rollback()
			from traceback import print_exc
			print_exc(file=sys.stderr)
			response = views.not_allowed(request, e.obj,e.perm)
			response.status_code = 403
		except HTTPException, e:
			db.store.rollback()
			response = e
		except Exception:
			a,b,c = sys.exc_info()
			try: db.store.rollback()
			except Exception: pass
			raise a,b,c
		try:
			add_response_headers(request,response)
		except Exception, e:
			print >>sys.stderr,repr(e)
			raise
		return ClosingIterator(response(environ, start_response),
							   [local.store.close, local_manager.cleanup])

	def __call__(self, environ, start_response):
		return self.dispatch(environ, start_response)


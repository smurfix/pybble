# -*- coding: utf-8 -*-

from __future__ import with_statement
from werkzeug import Request, ClosingIterator
from werkzeug.exceptions import HTTPException, NotFound, Unauthorized
from pybble.utils import STATIC_PATH, local, local_manager, \
	 TEMPLATE_PATH, AuthError, all_addons
from pybble.render import expose_map, url_map, send_mail, expose
from pybble.database import metadata, db, NoResult, dsn
from sqlalchemy.sql import and_, or_, not_
from sqlalchemy.orm import create_session
try:
	from sqlalchemy.engine.ddl import SchemaGenerator
except ImportError:
	pass
import sqlalchemy.exc

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
			metadata.create_all(db.engine)
		return action
		
	def init_site_replace(self):
		return self.init_site(replace_templates=True)

	def init_site(self, replace_templates=False):
		def action(domain=("d","localhost:5000"),name=("n",u"local debug site")):

			"""Initialize a new site"""
			# ... or in fact the first one

			from pybble.models import Site,User,Object,Discriminator,Template,TemplateMatch,VerifierBase,WikiPage,Storage,BinData,StaticFile
			from pybble.models import Group,Permission, add_mime,mime_ext, Renderer
			from pybble.models import TM_DETAIL_SUBPAGE, PERM_READ,PERM_ADMIN,PERM_ADD, TM_DETAIL_DETAIL, TM_DETAIL, TM_DETAIL_SNIPPET, TM_DETAIL_HIERARCHY, TM_DETAIL_RSS, TM_DETAIL_EMAIL
			from pybble import utils
			from werkzeug import Request

			for rn in ("markdown",):
				rc = "pybble.render.render_"+rn
				try:
					r = Renderer.q.get_by(name=rn)
				except NoResult:
					r = Renderer(rn,rc)
					db.session.add(r)
				else:
					if r.cls != rc:
						print "Warning: Renderer '%s' differs (%s | %s)." % (rn,r.cls,rc)
						if replace_templates:
							r.cls = rc

			db.session.flush()

			for k,v in Object.__mapper__.polymorphic_map.iteritems():
				v=v.class_

				try:
					o=Discriminator.q.get_by(id=k)
				except NoResult:
					o=Discriminator(v)
					db.session.add(o)
				else:
					if o.name != v.__name__:
						raise ValueError("Discriminator '%d' pointed at '%s', now '%s'!" % (k,o.name,v.__name__))
			db.session.flush()

			domain=domain.decode("utf-8")
			try:
				s=Site.q.get_by(domain=domain)
			except NoResult:
				s=Site(domain,name=name)
				db.session.add(s)
			else:
				print u"%s found." % s

			utils.local.request = Request({})
			utils.current_request.site = s

			for ext,typ,name in extensions:
				typ,subtyp = typ.split("/",1)
				add_mime(name,typ,subtyp,ext)
			db.session.flush()

			try:
				st = Storage.q.get_by(name=u"Test")
			except NoResult:
				st = Storage("Test","/var/tmp/testkram","localhost:5000/static")
				db.session.add(st)
			else:
				st.superparent = s
			db.session.flush()
			if s.storage is None:
				s.storage = st
				db.session.flush()

			try:
				u=User.q.get_one(and_(User.sites.contains(s), User.username==u"root"))
			except NoResult:
				u=User(u"root")
				u.email=settings.ADMIN
				u.sites.append(s)
				db.session.add(u)
			else:
				print u"%s found." % u

			db.session.flush()
			u.verified=True
			u.parent = s
			db.session.flush()
			s.owner_id = u.id ## recursion trap
			db.session.flush()
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
							sb = BinData(f[:dot],f[dot+1:],content, storage=st)
							db.session.add(sb)
							sb.save()

						try:
							sf = StaticFile.q.get_by(path=dp,superparent=s)
						except NoResult:
							sf = StaticFile(dp,sb)
							db.session.add(sf)
						else:
							if content != sf.content:
								print "Warning: StaticFile '%s' differs." % (dp,)
								if replace_templates:
									db.session.delete(sf)
									sf = StaticFile(dp,sb)
									db.session.add(sf)


			add_files(os.path.join(u"pybble",u"static"),u"")
		
			try:
				a=User.q.get_by(superparent=s, username=u"")
			except NoResult:
				a=User(u"", password="")
				a.owner = u
				a.superparent = s
				a.sites.append(s)
				db.session.add(a)
			else:
				print u"%s found." % a

			db.session.flush()
			a.verified=False

			db.session.flush()

			for d in Discriminator.q.all():
				if Permission.q.filter(and_(Permission.discr==d.id,Permission.right>=0)).count():
					continue
				p=Permission(u, s, d, PERM_ADMIN)
				p.superparent=s
				db.session.add(p)

			dw = Discriminator.q.get_by(name="WikiPage")
			ds = Discriminator.q.get_by(name="Site")
			dp = Discriminator.q.get_by(name="Permission")
			dk = Discriminator.q.get_by(name="Comment")
			dt = Discriminator.q.get_by(name="WantTracking")
			dd = Discriminator.q.get_by(name="BinData")

			for d in (dw,ds,dt,dd):
				if Permission.q.filter(and_(Permission.discr==d.id,Permission.right>=0,Permission.owner==a)).count():
					continue
				p=Permission(a, s, d, PERM_READ)
				p.superparent=s
				db.session.add(p)

			for d,e in ((ds,dd),(dw,dd),(ds,dw),(ds,dp),(dw,dw),(dw,dp),(dw,dk),(dk,dk),(ds,dt)):
				if Permission.q.filter(and_(Permission.new_discr==e.id,Permission.discr==d.id)).count():
					continue
				p=Permission(u, s, d, PERM_ADD)
				p.new_discr=e.id
				p.superparent=s
				db.session.add(p)

			# View templates
			for addon in self.addons:
				for cls in addon.__dict__.values():
					if not(isinstance(cls,type) and issubclass(cls,Object)):
						continue
					if cls.__name__ not in addon.__ALL__:
						continue
					if Permission.q.filter_by(discr=cls.cls_discr()).count():
						continue
					p=Permission(u, s, ds, PERM_ADMIN)
					p.new_discr=cls.cls_discr()
					p.superparent=s
					db.session.add(p)

					p=Permission(u, s, ds, PERM_ADD)
					p.new_discr=cls.cls_discr()
					p.superparent=s
					db.session.add(p)

			db.session.flush()

			def get_template(fn):
				with file(os.path.join(TEMPLATE_PATH,fn)) as f:
					try:
						data = f.read().decode("utf-8")
					except Exception:
						print >>sys.stderr,"While reading",fn
						raise

				try:
					t = Template.q.get_by(name=fn,parent=s)
				except NoResult:
					t = Template(name=fn,data=data,parent=s)
					t.owner = u
					db.session.add(t)
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

			db.session.flush()

			VerifierBase.register("register","pybble.login.verifier")
			db.session.flush()


			with file(os.path.join("doc","TOC.txt")) as f:
				try:
					data = f.read().decode("utf-8")
				except Exception:
					print >>sys.stderr,"While reading",fn
					raise
			
			try:
				w = WikiPage.q.get_by(name="Documentation",superparent=s)
			except NoResult:
				w = WikiPage("Documentation",data)
				w.owner=u
				w.parent=s
				w.superparent=s
				w.mainpage=True
				db.session.add(w)
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
				fn = fn[:-4]
				
				try:
					ww = WikiPage.q.get_by(name=fn,parent=w)
				except NoResult:
					ww = WikiPage(fn,data)
					ww.owner=u
					ww.parent=w
					ww.superparent=s
					ww.mainpage=False
					db.session.add(ww)
				else:
					ww.superparent=s
					ww.mainpage=False
					if ww.data != data:
						print "Warning: DocPage '%s' differs." % (fn,)
						if replace_templates:
							ww.data = data

			db.session.flush()
			for d in Discriminator.q.all():
				for detail,name in ((TM_DETAIL_SUBPAGE,"view"),
					(TM_DETAIL_DETAIL,"details"),
					(TM_DETAIL_HIERARCHY,"hierarchy"),
					(TM_DETAIL_RSS,"rss"),
					(TM_DETAIL_EMAIL,"email"),
					(TM_DETAIL_SNIPPET,"snippet")):
					try:
						data = open("pybble/templates/%s/%s.html" % (name,d.name.lower(),)).read().decode("utf-8")
					except (IOError,OSError):
						pass
					else:
						try:
							t = TemplateMatch.q.get_by(obj=s, discr=d.id, detail=detail)
						except NoResult:
							t = TemplateMatch(obj=s, discr=d.id, detail=detail, data=data)
							db.session.add(t)
						else:
							if t.data != data:
								print "Warning: AssocTemplate '%s/%s.html' differs." % (name,d.name.lower())
								if replace_templates:
									t.data = data
					db.session.flush()

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
						fn = "%s/%s" % (os.path.split(addon.__path__[0])[1],t)
						try:
							t = Template.q.get_by(name=fn,superparent=s)
						except NoResult:
							t = Template(name=fn,data=data)
							t.superparent = s
							t.owner = u
							db.session.add(t)
						else:
							if t.data != data:
								print "Warning: Template '%s' differs." % (fn,)
								if replace_templates:
									t.data = data
							if replace_templates:
								t.superparent = s
								t.owner = u
					db.session.flush()

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
								t = TemplateMatch.q.get_by(obj=s, discr=cls.cls_discr(), detail=t)
							except NoResult:
								t = TemplateMatch(obj=s, discr=cls.cls_discr(), detail=t, data=data)
								db.session.add(t)
							else:
								if t.data != data:
									print "Warning: AddOn-Template %s: '%s.%s.html' differs." % (addon.__name__, cls.__name__, n.lower())
									if replace_templates:
										t.data = data

			db.session.commit()
			print "Your root user is named '%s' and has the password '%s'." % (u.username, u.password)
		return action

	def show_database(self):
		def action():
			"""Show all database table definitions"""
			def foo(s, p=None):
				if not hasattr(s,"strip"):
					s=str(s)
				buf.write(s.strip()+";\n")

			buf = StringIO.StringIO()
			from sqlalchemy import create_engine
			gen = create_engine(os.getenv("DATABASE_TYPE",settings.DATABASE_TYPE)+"://", strategy="mock", executor=foo)
			if hasattr(gen.dialect,"schemagenerator"):
				gen = gen.dialect.schemagenerator(gen.dialect, gen)
			else:
				gen = SchemaGenerator(gen.dialect, gen)
			for table in metadata.tables.values():
				gen.traverse(table)
			print buf.getvalue()
		return action


	def trigger(self):
		def action(user=("u",""), site=("s",""), verbose=("v",False)):
			"""Process trigger records."""
			from pybble.models import Site,WantTracking,UserTracker,Tracker,User,Delete,Change
			from pybble import utils

			utils.local.request = Request({})

			siteq = Site.q
			if site:
				siteq = siteq.filter_by(name=site)
			
			for s in siteq:
				setup_code_env(s)
				if user:
					u = User.q.filter_by(site=s,name=user).value()
				else:
					u = None
				tq = Tracker.q.filter_by(site=s)
				if s.tracked:
					tq = tq.filter(Tracker.timestamp>s.tracked)
				if u:
					tq = tq.filter_by(owner=u)

				for t in tq.order_by(Tracker.timestamp):
					o=t.change_obj
					if o is None:
						print "ChangeObj??",t
						continue
					wq=WantTracking.q.filter(or_(WantTracking.discr==None,WantTracking.discr==o.discriminator))
					processed = set()
					while o:
						wantq=wq.filter_by(parent=o)
						if processed:
							wantq=wantq.filter(not_(or_(*( WantTracking.owner_id == i for i in processed))))

						inew = None
						imod = None
						idel = None
						for w in wantq:
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

							if UserTracker.q.filter_by(owner=w.owner, parent=t).count():
								continue
							ut=UserTracker(user=w.owner,tracker=t,want=w)
							db.session.add(ut)
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
				db.session.commit()

		return action

	def show(self):
		from pybble.models import TM_DETAIL_EMAIL, TM_DETAIL_RSS
		from pybble.render import jinja_env
		
		def action(obj=("o",""),user=("u",""), site=("s",""), detail=("d",TM_DETAIL_EMAIL), verbose=("v",False)):
			"""Show an object."""
			from pybble.models import Object,obj_get
			from pybble import utils

			utils.local.request = Request({})

			obj = obj_get(obj)
			if site:
				s = Site.q.get_by(name=site)
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
				db.session.execute(stmt)

			execfile(script, globals(),locals())

		return action

	def dispatch(self, environ, start_response):
		local.application = self
		local.session = db.session()
		local.session.rollback() # basic protection
		request = Request(environ)
		local.request = request
		local.url_adapter = adapter = url_map.bind_to_environ(environ)
		try:
			add_site(request)
			add_session(request)
			add_user(request)

			endpoint, values = adapter.match()
			handler = expose_map[endpoint]
			response = handler(request, **values)
			save_session(request,response)
			db.session.commit()
		except (NotFound,NoResult), e:
			from traceback import print_exc
			print_exc(file=sys.stderr)
			response = views.not_found(request, request.url)
			response.status_code = 404
		except AuthError, e:
			from traceback import print_exc
			print_exc(file=sys.stderr)
			response = views.not_allowed(request, e.obj,e.perm)
			response.status_code = 403
		except HTTPException, e:
			response = e
		try:
			add_response_headers(request,response)
		except Exception, e:
			print >>sys.stderr,repr(e)
			raise
		return ClosingIterator(response(environ, start_response),
							   [local_manager.cleanup])

	def __call__(self, environ, start_response):
		return self.dispatch(environ, start_response)


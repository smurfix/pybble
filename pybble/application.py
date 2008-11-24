# -*- coding: utf-8 -*-

from __future__ import with_statement
from werkzeug import Request, SharedDataMiddleware, ClosingIterator
from werkzeug.exceptions import HTTPException, NotFound
from pybble.utils import STATIC_PATH, local, local_manager, \
	 url_map, TEMPLATE_PATH, expose_map
from pybble.database import metadata, db, NoResult
from sqlalchemy.sql import and_, or_, not_

import pybble.models
from pybble.session import add_session, add_user, add_site, save_session

import StringIO
import settings
import sys,os

## Adapters
from pybble import views,login,confirm

class Pybble(object):

	def __init__(self, db_uri):
		local.application = self

		self.dispatch = SharedDataMiddleware(self.dispatch, {
			'/static':  STATIC_PATH
		})

	def init_database(self):
		def action():
			"""Initialize or update the database"""
			metadata.create_all(db.engine)
		return action
		
	def init_site_replace(self):
		return self.init_site(replace_templates=True)

	def init_site(self, replace_templates=False):
		def action(domain=("d","localhost:5000"),name=("n","Lokaler Debug-Kram")):

			"""Initialize a new site"""
			# ... or in fact the first one

			from pybble.models import Site,User,Object,Discriminator,Template,TemplateMatch,VerifierBase
			from pybble.models import obj_discr, TM_TYPE_PAGE
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

			for fn in os.listdir(TEMPLATE_PATH):
				if fn.startswith("."):
					continue
				with file(os.path.join(TEMPLATE_PATH,fn)) as f:
					try:
						data = f.read().decode("utf-8")
					except Exception:
						print >>sys.stderr,"While reading",fn
						raise

				try:
					t = Template.q.get_by(name=fn,parent=None)
				except NoResult:
					t = Template(name=fn,data=data)
					db.session.add(t)
				else:
					if t.data != data:
						print "Warning: Template '%s' differs.\n" % (fn,)
						if replace_templates:
							t.data = data
				

			domain=domain.decode("utf-8")
			try:
				s=Site.q.get_by(domain=domain)
			except NoResult:
				s=Site(domain,name=name)
				db.session.add(s)
			else:
				print u"%s found." % s

			try:
				u=User.q.get_one(and_(User.sites.contains(s), User.username==u"root"))
			except NoResult:
				u=User(u"root")
				u.verified=True
				u.email=settings.ADMIN
				u.sites.append(s)
				s.owner = u
				db.session.add(u)
			else:
				print u"%s found." % u

			try:
				a=User.q.get_one(and_(User.sites.contains(s), User.username==u""))
			except NoResult:
				a=User(u"", password="")
				a.verified=False
				a.owner = u
				a.superparent = s
				a.sites.append(s)
				db.session.add(a)
			else:
				print u"%s found." % a

			try:
				v = VerifierBase.q.get_by(name="register")
			except NoResult:
				v=VerifierBase(name="register",cls="pybble.login.verifier")
				db.session.add(v)
			else:
				print "%s found." % v

			try:
			    t = TemplateMatch.q.get_by(obj=s, discriminator=obj_discr(s), type=TM_TYPE_PAGE)
			except NoResult:
				t = TemplateMatch(obj=s, discriminator=obj_discr(s), type=TM_TYPE_PAGE, \
					data = open("pybble/main.html").read())
				db.session.add(t)

			db.session.commit()
			print "Your root user is named '%s' and has the password '%s'." % (u.username, u.password)
			print "Your anon user is named '%s' and has the password '%s'." % (a.username, a.password)
		return action

	def show_database(self):
		def action():
			"""Show all database table definitions"""
			def foo(s, p=None):
				buf.write(s.strip()+";\n")

			buf = StringIO.StringIO()
			from sqlalchemy import create_engine
			gen = create_engine(os.getenv("DATABASE_TYPE",settings.DATABASE_TYPE)+"://", strategy="mock", executor=foo)
			gen = gen.dialect.schemagenerator(gen.dialect, gen)
			for table in metadata.tables.values():
				gen.traverse(table)
			print buf.getvalue()
		return action


	def dispatch(self, environ, start_response):
		local.application = self
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
		except NotFound, e:
			response = views.not_found(request)
			response.status_code = 404
		except HTTPException, e:
			response = e
		try: save_session(request,response)
		except Exception: raise
		return ClosingIterator(response(environ, start_response),
							   [db.session.remove, local_manager.cleanup])

	def __call__(self, environ, start_response):
		return self.dispatch(environ, start_response)


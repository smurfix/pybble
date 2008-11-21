from __future__ import with_statement
from werkzeug import Request, SharedDataMiddleware, ClosingIterator
from werkzeug.exceptions import HTTPException, NotFound
from pybble.utils import STATIC_PATH, local, local_manager, \
	 url_map, TEMPLATE_PATH
from pybble.database import metadata, db, NoResult

import pybble.models
from pybble import views

import StringIO
import settings
import os

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
		
	def init_site(self):
		def action(domain=("d","example.org.invalid")):

			"""Initialize a new site"""
			# ... or in fact the first one

			from pybble.models import Site,User,Object,Discriminator,Template
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
				with file(os.path.join(TEMPLATE_PATH,fn)) as f:
					data = f.read().encode("utf-8")

				try:
					t = Template.q.get_by(name=fn,parent=None)
				except NoResult:
					t = Template(name=fn,data=data)
					db.session.add(t)
				else:
					if t.data != data:
						print "Warning: Template '%s' differs.\n" % (fn,)
				

			domain=domain.decode("utf-8")
			try:
				s=Site.q.get_by(domain=domain)
			except NoResult:
				s=Site(domain)
				db.session.add(s)
			else:
				print "%s found." % s

			try:
				u=User.q.get_one(User.sites.contains(s))
			except NoResult:
				u=User(u"root")
				u.verified=True
				db.session.add(u)
				u.sites.append(s)
			else:
				print "%s found." % u

			db.session.commit()
			print "Your root user is named '%s' and has the password '%s'." % (u.username, u.password)
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
		local.url_adapter = adapter = url_map.bind_to_environ(environ)
		try:
			endpoint, values = adapter.match()
			handler = getattr(views, endpoint)
			response = handler(request, **values)
		except NotFound, e:
			response = views.not_found(request)
			response.status_code = 404
		except HTTPException, e:
			response = e
		return ClosingIterator(response(environ, start_response),
							   [db.session.remove, local_manager.cleanup])

	def __call__(self, environ, start_response):
		return self.dispatch(environ, start_response)

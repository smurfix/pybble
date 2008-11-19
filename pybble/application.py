from sqlalchemy import create_engine
from werkzeug import Request, SharedDataMiddleware, ClosingIterator
from werkzeug.exceptions import HTTPException, NotFound
from pybble.utils import STATIC_PATH, Session, local, local_manager, \
     url_map
from pybble.database import metadata

import pybble.models
from pybble import views

import StringIO
import settings
import os

class Pybble(object):

    def __init__(self, db_uri):
        local.application = self
        self.database_engine = create_engine(db_uri, convert_unicode=True)

        self.dispatch = SharedDataMiddleware(self.dispatch, {
            '/static':  STATIC_PATH
        })

    def init_database(self):
        metadata.create_all(self.database_engine)
	
    def show_database(self):
	def foo(s, p=None):
	    buf.write(s.strip()+";\n")

	buf = StringIO.StringIO()
	gen = create_engine(os.getenv("DATABASE_TYPE",settings.DATABASE_TYPE)+"://", strategy="mock", executor=foo)
	gen = gen.dialect.schemagenerator(gen.dialect, gen)
	for table in metadata.tables.values():
	    gen.traverse(table)
	print buf.getvalue()


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
                               [Session.remove, local_manager.cleanup])

    def __call__(self, environ, start_response):
        return self.dispatch(environ, start_response)

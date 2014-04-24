#!/usr/bin/python
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

import sys
from ..core.db import db,db_engine,Base

from . import Manager,Command,Option
from ..core import config

from sqlalchemy import create_engine
from sqlalchemy.exc import ProgrammingError

from ..core.models import _all

class SchemaCommand(Command):
	def __call__(self,app):
		with app.test_request_context('/'):
			self.main()

	def __init__(self):
		super(SchemaCommand,self).__init__()
		self.add_option(Option("-x","--exec", dest="exe",action="store_true", help="Actually run the commands"))
		self.add_option(Option("-d","--diff", dest="diff",action="store_true", help="run 'dbdiff'"))

	def dump_intended(self, dest=sys.stdout):
		def dump(sql, *multiparams, **params):
				print(str(sql.compile(dialect=dump_engine.dialect)).strip()+";", file=dest)
		dump_engine = create_engine('mysql://', strategy='mock', executor=dump)
		Base.metadata.create_all(dump_engine)

	def dump_current(self, dest=sys.stdout):
		engine = db_engine()
		for k in Base.metadata.tables.keys():
			try:
				r = engine.execute("show create table `{}`".format(k))
			except ProgrammingError as err:
				print("# Table `{}` does not exist?".format(k), file=dest)
				pass
			else:
				for x in r:
					print(x[1]+";", file=dest)

	def __call__(self,app, help=False,exe=False,diff=False, **kwargs):
		if help:
			print("""\
If '--exec' is used: run the commands to bring the database up-to-date.
Else, print the commands to initially create the database.

If '--diff' is used: use "dbdiff" (which may emit spurious changes).
Else, use SQLAlchemy directly (which does not catch all differences).

--diff and --exe together cannot be used together yet.
""")
		if diff:
			from tempfile import NamedTemporaryFile
			f1 = NamedTemporaryFile()
			f2 = NamedTemporaryFile()
			self.dump_intended(f1)
			self.dump_current(f2)
			f1.flush()
			f2.flush()

			from ..core.utils import attrdict
			opt = attrdict()
			from ..utils.sql_diff import run_diff

			opt.verbose=False
			opt.do_update=False
			opt.db1file = f1.name
			opt.db2file = f2.name
			opt.db1=None
			opt.db2=None
			opt.skip_tables = ""
			opt.skip_flags = "ae" ## skip: a=field order e=DB engine i=index names
			opt.init=True
			opt.execstr=False

			run_diff(opt,())

		elif exe:
			engine = db_engine(echo=True)
			Base.metadata.create_all(engine)
		else:
			self.dump_intended()


#!/usr/bin/python
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

# config defaults.
# Do not edit; create a LOGIN.py file instead.
import sys
try:
	from LOGIN import *
except ImportError:
	print("Warning: you do not have a LOGIN.py file",file=sys.stderr)

__all__ = ('DEBUG', 'rpc_user','rpc_pass','cert','SECRET_KEY','rpc_url','rpc_port',
	'mysql_host','mysql_user','mysql_pass','mysql_admin_user','mysql_admin_pass','mysql_uri','mysql_admin_uri','mysql_database')
# DEBUG: Flag for debug output
# mysql_user, mysql_pass: mysql username and password
# mysql_host,mysql_db: mysql host and database name
# mysql_uri: mysql connect string (supersedes the above)
# rpc_user: Username for logging in to the RPC frontend
# rpc_pass: Password for logging in to the RPC frontend
# cert: SSL Certificate of the iProtect server
# SECRET_KEY: key to locally encrypt passwords etc.

if "DEBUG" not in globals():
	DEBUG = False
if "TRACE" not in globals():
	TRACE = False
#if not hasattr(LOGIN,"SECRET_KEY"):
#	LOGIN.SECRET_KEY = "development version"
#	print("WARNING: Set a secret key! Do not use in production!", file=sys.stderr)
if "mysql_host" not in globals():
	mysql_host = "localhost"
if "mysql_port" not in globals():
	mysql_port = 3306
if "mysql_database" not in globals():
	mysql_database = "pybble"

if "mysql_uri" not in globals():
	if "mysql_user" in globals() and "mysql_pass" in globals():
		mysql_uri = "mysql://%s:%s@%s:%s/%s" % (mysql_user,mysql_pass,mysql_host,mysql_port,mysql_database)
if "mysql_admin_uri" not in globals():
	if "mysql_admin_user" not in globals() and "mysql_user" in globals():
		mysql_admin_user = mysql_user
	if "mysql_admin_pass" not in globals() and "mysql_pass" in globals():
		mysql_admin_pass = mysql_pass
	if "mysql_admin_user" in globals() and "mysql_admin_pass" in globals():
		mysql_admin_uri = "mysql://%s:%s@%s:%s/%s" % (mysql_admin_user,mysql_admin_pass,mysql_host,mysql_port,mysql_database)

if "web_port" not in globals():
	web_port = 8080
if "debug_web_port" not in globals():
	debug_web_port = 58080

# load these extensions
if "addons" not in globals():
	addons = None

if __name__ == "__main__":
	import sys
	if len(sys.argv) > 1 and sys.argv[1] == "-s":
		p="%s=$( echo -ne %r )"
	else:
		p="%s=%r"
	for k in __all__:
		if k.startswith("_") or k.endswith("_"):
			continue
		v = globals()[k]
		if isinstance(k,unicode):
			k = k.encode("utf-8")
		if isinstance(v,unicode):
			v = v.encode("utf-8")
		print(p % (k,v))


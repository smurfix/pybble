# -*- coding: utf-8 -*-

DATABASE_TYPE="sqlite" # or mysql

# sqlite
DATABASE_FILE="/tmp/pybble.db"

# mysql
DATABASE_USER="test"
DATABASE_PASSWORD="fufu"
DATABASE_HOST="localhost"
DATABASE_NAME="testdb"

DATABASE_DEBUG=False
SERVER_DEBUG=True
SERVER_RELOAD=True

SESSION_COOKIE_NAME="sess"
SESSION_COOKIE_AGE=86400
SECRET_KEY="I won't tell you."
STATIC_EXPIRE=3600 # 1h

MAILHOST="intern.smurf.noris.de"
ADMIN="smurf@smurf.noris.de"

ADDONS = ("demo",)

### do not change
try:
	from localsettings import *
except ImportError:
	pass

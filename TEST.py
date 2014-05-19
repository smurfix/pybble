# -*- coding: utf-8 -*-

## This is a minimal config file for testing.

TESTING=True # this file only works in test mode

sql_driver="sqlite"
sql_database=":memory:" ## overridden when running tests
## 
SECRET_KEY="fbfzkar2ihf3ulqhelg8srlzg7resibg748wifgbz478"
#TRACE=True
#MEDIA_PATH="/var/tmp/pybble"
## set by the test run script
ADMIN_EMAIL="smurf@smurf.noris.de"

URLFOR_ERROR_FATAL=False

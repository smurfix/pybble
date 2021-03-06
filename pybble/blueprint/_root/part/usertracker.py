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

from flask import request, session

from pybble.core.models.tracking import UserTracker
from pybble.core.db import db
from pybble.render import render_template

from .._base import expose
expose = expose.sub("part.usertracker")

from datetime import datetime,timedelta
from time import time

###
### Tracking
###

@expose("/changes")
def view_all():
	user = request.user
	f = (UserTracker.user == user)
	last = session.get("chg_",None)
	if last and time()-last[0] < 2*60:
		pass
	else:
		session["chg_"] = (int(time()), user.feed_read)
		user.feed_read = datetime.utcnow()

	return render_template("changelist.html", changes=UserTracker.q.filter(f).order_by(UserTracker.id.desc())[0:30])
	

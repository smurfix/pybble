# -*- coding: utf-8 -*-
##BP

from flask import request

from pybble.render import render_template
from pybble.core.models.tracking import UserTracker
from pybble.core.db import db
from .._base import expose

from storm.locals import And,Desc
from datetime import datetime,timedelta
from time import time

###
### Tracking
###

@expose("/changes")
def view_all():
	user = request.user
	f = (UserTracker.owner_id == user.id)
	last = request.session.get("chg_",None)
	if last and time()-last[0] < 2*60:
		pass
#		if last[1]:
#			f = And(f,UserTracker.tracker.timestamp < last[1])
	else:
		request.session["chg_"] = (int(time()), user.feed_read)
		user.feed_read = datetime.utcnow()

	return render_template("changelist.html",
	                       changes=db.filter(UserTracker, f).order_by(Desc(UserTracker.id))[0:30])
	

# -*- coding: utf-8 -*-

from pybble.utils import current_request
from pybble.render import render_template, expose
from pybble.models import UserTracker
from sqlalchemy.sql import and_, or_, not_

from datetime import datetime,timedelta
from time import time

###
### Tracking
###

@expose("/changes")
def view_all(request):
	user = request.user
	f = (UserTracker.owner == user)
	last = request.session.get("chg_",None)
	if last and time()-last[0] < 2*60:
		if last[1]:
			f = and_(f,UserTracker.tracker.timestamp < last[1])
	else:
		request.session["chg_"] = (int(time()), user.feed_read)
		user.feed_read = datetime.utcnow()

	return render_template("changelist.html",
	                       changes=UserTracker.q.filter(f).order_by(UserTracker.id.desc()))
	

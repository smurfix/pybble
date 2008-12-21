# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, render_template, expose, render_my_template
from pybble.models import Site, WikiPage, TM_DETAIL_PAGE, Tracker
from pybble.views import view_oid

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from wtforms.validators import ValidationError
from sqlalchemy.sql import and_, or_, not_
from datetime import datetime

###
### Tracking
###

@expose("/changes")
def view_all(request):
	return render_template("changelist.html",
	                       changes=Tracker.q.filter_by(owner=request.user)\
	                                        .order_by(Tracker.timestamp.desc()))
	

# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, render_template, expose, render_my_template
from pybble.models import Site, WikiPage, TM_DETAIL_PAGE, Change
from pybble.views import view_oid

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from storm.locals import And
from wtforms.validators import ValidationError
from datetime import datetime


###
### Tracking
###

def viewer(request, obj, **args):
	n = db.filter(Change, And(Change.timestamp>obj.timestamp,
	                         Change.parent==obj.parent))\
	            .order_by(Change.timestamp)\
	            .first()
	p = db.filter(Change, And(Change.timestamp<obj.timestamp,
	                         Change.parent==obj.parent))\
	            .order_by(Desc(Change.timestamp))\
	            .first()
	return render_my_template(request, obj=obj, next=n, prev=p, detail=TM_DETAIL_PAGE, **args)


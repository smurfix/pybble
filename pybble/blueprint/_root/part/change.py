# -*- coding: utf-8 -*-

from werkzeug import redirect
from werkzeug.exceptions import NotFound
from pybble.utils import current_request, make_permanent
from pybble.render import url_for, render_template, expose, render_my_template
from pybble.core.models._const import TM_DETAIL_PAGE
from pybble.views import view_oid

from pybble.database import db,NoResult
from pybble.flashing import flash
from pybble.session import logged_in
from wtforms import Form, BooleanField, TextField, TextAreaField, \
	SelectField, PasswordField, HiddenField, validators
from storm.locals import And
from wtforms.validators import ValidationError
from datetime import datetime
from storm.locals import Desc


###
### Tracking
###

def viewer(request, obj, **args):
	return render_my_template(request, obj=obj, next=obj.next_change, prev=obj.prev_change, detail=TM_DETAIL_PAGE, **args)


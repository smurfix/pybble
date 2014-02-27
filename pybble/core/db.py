# -*- coding: utf-8 -*-

##BP

from flask.ext.mongoengine import MongoEngine
from .fields import ListField

db = MongoEngine()
db.ListField = ListField

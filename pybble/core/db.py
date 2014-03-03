# -*- coding: utf-8 -*-
##BP

from flask.ext.mongoengine import MongoEngine
from .fields import ListField,StructField

db = MongoEngine()
db.ListField = ListField
db.StructField = StructField

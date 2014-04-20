#!/usr/bin/python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
##
## This is part of Pybble, a WMS (Whatever Management System) based on
## Jinja2/Haml, Werkzeug, Flask, and Optimism.
##
## Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
## it is licensed under the GPLv3. See the file `README.md` for details
## as well as hopeful statements by the author.
##
## This paragraph is auto-generated and may self-destruct at any time.
## Please do not remove the next line, or insert any blank lines before it.
##BP

## first thing, for monkeypatching
import pybble

import logging

from flask.ext.script import Server

#from flask.ext.collect import Collect
#from quokka.core.db import db
#from quokka.ext.blueprints import load_blueprint_commands

from pybble.manager.main import RootManager
manager = RootManager()

if __name__ == '__main__':
	manager.run()

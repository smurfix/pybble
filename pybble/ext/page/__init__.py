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

## This is a prototypical Pybble extension.

## MIME types to register. May already be present.
MIME = (
    ## MIME type,subtype, file extension, name, description
    ('html','page',None,'Content page',"The 'boring' content part of a web page"),
)

## New data model(s). This can be
## * the name of a module, all of whose ObjectRef descendants will be imported
## * the path to an ObjectRef class
## * a list of paths to ObjectRef classes
MODEL = "pybble.ext.page.model.Page"

## New apps. Ditto, though more than one app is … strange.
APP = ()

## New blueprints. Ditto and somewhat more common.
BLUEPRINT = ("pybble.ext.page.blueprint.Blueprint",)

## Code to run, after everything is set up
## This typically adds additional permissions.
FIXTURE = ()

## New renderers. Pybble comes with Jinja and HAML, though you really shouldn't use these for user content.
RENDERER = ()

# Templates and static files are located in "templates" and "static"
# directories beside the app or blueprint they're associated with.


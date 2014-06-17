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

"""Setup caching

Establish data / cache file paths, and configurations,
bootstrap fixture data if necessary.

"""
from hashlib import md5
import sys

# dogpile cache regions.  A home base for cache configurations.
regions = {}

def md5_key_mangler(key):
    """Receive cache keys as long concatenated strings;
    distill them into an md5 hash.

    """
    return md5(key.encode('ascii')).hexdigest()

# configure the "default" cache region.
def configure(app):
    host = app.config['REDIS_HOST']
    if not host:
        return

    from dogpile.cache.region import make_region
    regions['default'] = make_region( key_mangler=md5_key_mangler if not app.testing else str
        ).configure(
            'dogpile.cache.redis',
            expiration_time=app.config['CACHE_EXPIRES'],
            arguments = {
                'host': host,
                'port': app.config['REDIS_PORT'],
                'db': app.config['REDIS_DB'],
                'password': app.config['REDIS_PASSWORD'],
                'redis_expiration_time': app.config['CACHE_EXPIRES']*2,
                'distributed_lock': not app.config['SINGLE_SERVER'],
                }
        )


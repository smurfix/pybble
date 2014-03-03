#!/usr/bin/env python
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

from setuptools import setup, find_packages

VERSION = (0, 2, 0)

def get_version(fname='pybble/version.py'):
    with open(fname) as f:
        for line in f:
            if line.startswith('__version__'):
                return eval(line.split('=')[-1])

__version__ = ".".join(map(str, VERSION))
__status__ = "Alpha"
__description__ = "Flexible & modular CMS powered by Flask and MongoDB"
__author__ = "Bruno Rocha <rochacbruno@gmail.com>"
__email__ = "quokka-developers@googlegroups.com"
__license__ = "MIT License"
__copyright__ = "Copyright 2013, Quokka Project / PythonHub.com"

kwargs = {}
try:
    from babel.messages import frontend as babel
    kwargs['cmdclass'] = {
        'extract_messages': babel.extract_messages,
        'update_catalog': babel.update_catalog,
        'compile_catalog': babel.compile_catalog,
        'init_catalog': babel.init_catalog,
    }
    kwargs['message_extractors'] = {
        'pybble': [
            ('**.py', 'python', None),
            ('**/templates/**.html', 'jinja2', {
                'extensions': (
                    'jinja2.ext.autoescape,'
                    'jinja2.ext.with_,'
                    'jinja2.ext.do,'
                )
            })
        ]
    }
except ImportError:
    pass

REQUIREMENTS = [i.strip() for i in open("requirements.txt").readlines()
                if not i.startswith("http")]

dependency_links = [i.strip() for i in open("requirements.txt").readlines()
                    if i.startswith("http")]

classifiers = [
    "Development Status :: 3 - Alpha",
    "Environment :: Web Environment",
    "Framework :: Flask",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GPLv3",
    "Natural Language :: English",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: POSIX :: Linux",
    "Programming Language :: JavaScript",
    "Programming Language :: Python :: 2.7",
    'Programming Language :: Python',
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    'Topic :: Software Development :: Libraries :: Python Modules'
]

try:
    long_description = open('README.md').read()
except:
    long_description = __description__

setup(name='pybble',
      version=__version__,
      description=__description__,
      long_description=long_description,
      classifiers=classifiers,
      keywords='pybble cms flask publishing mongodb',
      author=__author__,
      author_email=__email__,
      url='http://pybble.smurf.noris.de',
      download_url="https://github.com/smurfix/pybble/tarball/master",
      license=__license__,
      packages=find_packages(exclude=('doc', 'docs',)),
      package_dir={'pybble': 'pybble'},
      install_requires=REQUIREMENTS,
      dependency_links=dependency_links,
      include_package_data=True,
      test_suite='nose.collector',
      **kwargs)

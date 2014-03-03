The Pybble Thing
===============================================

### Flask and MongoDB powered web "whatever" manager
### (alpha version, work in progress)

<p align="center">
<img src="docs/logo_256.png" alt="Pybble WMS" />
</p>


Pybble is a flexible WMS ("Whatever Management System", which in contrast
to a CMS isn't (just) about Content). It builds on 
Jinja2/Haml, Werkzeug, Flask, MongoDB, and Optimism.

Pybble is Copyright © 2014 by Matthias Urlichs <matthias@urlichs.de>,
it is licensed under the GPLv3. See the file `LICENSE` for details.

Note that I would have liked to publish this code under the AGPL instead
(so that everybody will _have to_ share their extensions and other
interesting pybble-related code), but life is not perfect, so I'll merely
state my wish here that you in fact _do_ share your work. Whether you
ultimately do, or not, is up to you. Just don't forget not to send your
``localsettings.py`` file …


Rationale
==========

This is personal.

I manage a bunch of small semi-customized web servers (my sister's
paintings, my personal website, my very personal website, a photo club …).
They all ran on different platforms (Django, Drupal, …) and updating these
is a major hassle (Drupal can't do it automatically due to a bug).
In addition, I want to share some content, I want to create my own views
without futzing around with Drupal's view editor, I want a single
admin login for all of this, I want everything in either git or the
database. The list goes on.

I looked at Quokka, it has some neat ideas but its content structure
somehow doesn't want to fit to my brain.

I want small modules that actually do something.


Quick start
============

0. Prepare your system

You need a MongoDB instance.
Pybble runs on Python 2.7
You might want to install virtualenv.

1. Get Pybble

```bash
$ git clone https://github.com/smurfix/pybble.git
$ cd pybble
$ pip install -r requirements.txt
```

2. Define your MongoDB settings

```bash
$ $EDITOR local_settings.py
===============quokka/quokka/local_settings.py===============
MONGODB_SETTINGS = {'DB': 'your_mongo_db'}
DEBUG = True
=============================================================
```

3. Populate with sample data (optional)

```bash
$ python manage.py populate 

```

4. Create a superuser

```bash
$ python manage.py createsuperuser
you@email.com
P4$$W0Rd
```

5. Run

```bash
$ python run.py
```
6. Access on http://localhost:5000 
7. Admin on http://localhost:5000/admin

or by making your server reachable on other networks

Is it any good?
==============

[Yes!](https://news.ycombinator.com/item?id=3067434)



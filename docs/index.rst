:orphan:

Welcome to Pybble
=================

This documents the Pybble WMS.

Pybble is not a CMS (Content Management System). It does not presume to
know whatever it is that you want to manage, so it's a WMS: Whatever
Management System.

Unlike other frameworks which want you to set up a new instance for every
webspace, Pybble is a common box for (potentally) different Web apps which
share a common base. This base consists of site, config, user, and
access rights management. Sites are hierarchic. Users can be present on
different sites with individual access rights and parameters.

You should probably start with :ref:`installation` and ref:`setup`.
Next, read about the common :ref:`datastructure` which Pybble offers, and
build a personal web history application in our :ref:`tutorial`.

Pybble depends on `Flask`_ and a couple of its modules.

-   `Flask Documentation <http://flask.pocoo.org/docs`_

.. _Flask http://flask.pocoo.org/

.. include:: contents.rst.inc

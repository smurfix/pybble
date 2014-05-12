Pybble's History
================

In 2009 I wanted a web management system for myself. So I wrote one.
`Pybble`.

At that time there was `Werkzeug`, but no `Flask`. There also was `Storm`,
a somewhat-lightweight ORM system much like `SQLAlchemy` but easier to use
and a whole lot faster, albeit a bit less featureful and *much* less
documented. (Written by a Canonical employee.)

Since then, a bunch of things have happened.

* I did not have much time for `Pybble`.

* The people who co-used it for their website decided to switch to
  brain-damaged things written in `PHP`. (What else?) In fact, they
  switched twice, and then settled on `Drupal`.

* Canonical did not do anything with `Storm`. In particular, there were no
  new versions, no support, and no new documentation, which was sorely
  needed.

* I switched to Drupal for my own stuff.

* Drupal's idea of a multi-site multi-language content management system is
  very cool, but actually configuring such a thing is an exercise in
  frustration. You do X, your site's design breaks horribly; you undo X and
  the design _stays_broken_. This is not what I want.

* In 2013, I found an intractable bug in Drupal (drush will not start, and
  my website's users get to see random error messages) which absolutely
  *nobody* seems to be able to help me with.

* I wrote three quick-and-dirty web pages (using `Flask`) and discovered
  that I need almost-identical infrastructure, three times, which is a
  waste of effort.

Thus, I decided to bite the bullet and revive `Pybble`.

Why Pybble?
-----------

Two answers: Hackability and Discoverability.

Pybble is designed to be hackable. You can plug in your own data structures,
without modifying the Python base. (The templates are another matter …)

All data objects are linkable to all other data objects. This may be
overkill at first glance (who needs to attach a bunch of Wiki pages to a
Comment, instead of a bunch of Comments to a Wiki page?) but the point is
that you want to build your site the way you envision it, not the way the
data structure allows you to.

Pybble is discoverable. All object relations are explicit and
foreign-key-coded. All data objects are mirrored SQL tables -- none of these
pseudo-tables which certain other systems play with, to get around the fact
that SQL is not NoSQL.

Why not NoSQL?
--------------

No explicit relationships between first-class objects. Databases protect
you against deleting things that are still referenced.

No transactions. Sorry, but IMHO a web access which throws an error shall
have no impact on my data structures, much less a partial one.

On the other hand, let's face it: object inheritance and SQL really don't
work all that well together, and all options for that have a heap of
disadvantages. Pybble chooses the joined-table version because that has the
least redundancy WRT data storage, but any other way should in principle
work just as well.

If all else fails, a NoSQL back-end that can replace SQLAlchemy should not
be too difficult to write …


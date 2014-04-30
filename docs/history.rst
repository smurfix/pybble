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


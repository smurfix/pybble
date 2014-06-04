Pybble's History
================

In 2008/2009 I wanted a web management system for myself. So I wrote one.
`Pybble`.

At that time there was `Werkzeug`, but no `Flask`. There also was `Storm`,
a somewhat-lightweight ORM system much like `SQLAlchemy` but easier to use
and a whole lot faster, albeit a bit less featureful and *much* less
documented. (Written by a Canonical employee.) `Pybble` was based on an
object-inheritance model with globally unique IDs and at most three
foreign-key pointers, called "parent", "owner" and "superparent", which
could and frequently did link any object to any other object in the system.
(Needless to say, this flexibility came with a corresponding amount of
bugginess.)

Since then, a bunch of things have happened.

* I did not have much time for `Pybble`.

* The people who co-used it for their website decided to switch to
  brain-damaged things written in `PHP`. (What else?) In fact, they
  switched twice, and then settled on `Drupal`.

* Canonical did not do anything with `Storm`. In particular, there were no
  new versions, no support, and no new documentation, which was sorely
  needed.

* I switched to Drupal for my own web pages.

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

Thus, I decided to bite the bullet and revive `Pybble` …
except for a couple of minor changes.

Why Pybble?
-----------

Two answers: Hackability and Discoverability.

Pybble is designed to be hackable. You can plug in your own data structures,
without modifying the Python base. (The templates are another matter …)

Pybble is discoverable. All object relations are explicit and
foreign-key-coded. All data objects are backed by SQL tables -- none of
these pseudo-tables which certain other systems play with, to get around
the fact that SQL is not NoSQL.

Pybble comes with a tree-based object explorer that shows every
relationship. It can do foreign keys to any random object – you don't get 
SQL's integrity guarantee with these reference objects, but that doesn't
matter because Pybble doesn't delete anything, and neither would it change
index values. (Deletion is currently handled by setting a 'deleted' Boolean. 
TODO: write an external cleanup program which makes sure that all
references to an object are gone, or themselves deleted, before really
removing objects from the database.)

Pybble has an automatic built-in change tracker that does not depend on 
SQLAlchemy (much). So you can easily discover who did what, and undo
whatever Joe Spammer did to your system automatically.
(An undo system is TODO. But the data is there.)

Pybble is completely template-system agnostic. It ships with Jinja2
templates because I think they're nice – especially when you use HAML
syntax instead of XML – but in fact you can use anything else.

Why not NoSQL?
--------------

No transactions. Sorry, but IMHO a web access which throws an error shall
have no impact on my data structures, much less a partial one.

On the other hand, let's face it: object inheritance and SQL really don't
work all that well together, and all options for that have a heap of
disadvantages. Pybble chooses to forego database-assured relational
integrity when refering to any-table objects.


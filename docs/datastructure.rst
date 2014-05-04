Pybble's data
=============

Data structures in web frameworks are difficult. You want to be both
flexible *and* generic.

Pybble's approach is the one which is supported by `SQLalchemy`'s "linked
tables" inheritance model: everything interesting descends from `Object`,
which has three generic "parent" pointers, appropriately named `parent`,
`superparent` and `owner`.

The *parent* is the object which contains this one.
The *superparent* is the higher-level object which owns a collection of
parent-child trees.
The *owner* is the user who created an object.

For instance, consider a comment on a web page. The `owner` is the user who
created the comment; the `superparent` is the web page the comment is
attached to; the `parent` points to the comment this one is replying to, or
also to the web page if it directly addresses its content.

This essentially means that you can comment on anything. Or indeed that you
can attach anything to anything else, which does not always make sense.

However, this also means that you can have a generic command for exploring
your website's data structure, even if you add ten strange modules.

In theory, individual object models are responsible for checking that you
set their owner/parent/superparent to something that makes semantic sense
and/or doesn't crash the web app. In practice, well, none of that is
implemented yet.

An object's superparent is supposed to be immutable. This is not enforced
anywhere (yet), but Pybble require a restart if you ever change e.g. a 
site's app (pointed to as the site's superparent).

Websites
--------

The `site` object is the core of Pybble. It declares the root of one
particular URL.

The main question many new users have is "how do I tell my CMS what to
display on the front page"? The answer is: Templates.

Templates
---------

Pybble has templates. In fact, it has a lot of them. Templates are
distinguished by

* the information's destination (complete page; item in a page;
  short linked description of the item; email with the page's content …)

* what you want to do with the object (view, edit, delete …)

* which object types this template applies to (site, comment, user …)

* whether the template applies to the object it's attached to, or to 
  some object of type X below the attachee, or both

Thus you can have a sub-hierarchy with a completely different look&feel.

Static data
-----------

Pybble supports serving static data via a "big" web server. By default,
access to these is not controlled. The danger of random links is
mitigated in two ways:

* Pybble generates content-addressed file names. If you serve a file named
  `foo.pdf`, Pybble actually stores it (and links to it) as
  `/static/ab/_/foo-cdefghijklm.pdf`, where `c-k` are random letters or
  digits, and the path plus the `lm` end letters allow Pybble to recover
  the file's serial number and thus the internal object wich links to it.
  (This is not actually implemented, but the information is there if you
  need it.)

  Correction: `c-k` only seem random; in fact they're generated from the
  SHA1 checksum of the file's contents. (There is no seed included here
  because I wouldn't want to invalidate all the file names when you need to
  change the site's secret.)

  Anyway: if you teach your web server to *not* generate directories for
  /static (or whichever path prefix you use), people will be unable to
  enumerate your files, or to scan directories for content.

* You can teach your web server to check the `Referer`: header. This can be
  circumvented easily, but the main reason for random third-party linking
  (conserving one's own bandwidth on somebody else's dime) are thwarted
  quite well by this.

Navigation
----------

Let's face it: Everybody wants something different. Global menu with the
local site somehow marked? Local menu with "up a level" links? Breadcrumbs
(i.e. a list of the last ten pages the user has accessed before this one)?

Pybble does not enforce anything here. Template methods to list the site's
and the current page's sub-objects of a certain type are available; thus
you can create your own menu structure by way of a bit of Jinja coding.

Breadcrumbs
-----------

For any page, Pybble saves the time when a particular user last accessed
it. Thus, if you sort that list by descending timestamp and display the
last five or so somewhere on your pages, the user will probably like your
website.

TODO: If you don't allow a user to create breadcrumb objects, they won't
be.

TODO2: create session-tracked anonymous users, so that this works without
logging in. (Such users are also required for implementing a shop system.)

Users; Authentication
---------------------

Pybble has the usual "user" and "group" objects. Attaching users to
sessions and all that should be managed by `Flask-Login` but is not yet,
because when Pybble was originally written there was no `Flask`, much less
`Flask-Login`.

Authorization
-------------

There's a "permission" object. It says whether user A can do action B to
objects of type C, possibly if attached to objects of type D. The latter is
relevant when we ask "can the user add a comment to a wiki page".
The permission's parent is the object it grants access to; if it's not
found there, the system checks the parent, until it gets to the root
website, which has no parent. For `site` objects, it also checks the owner,
presumably because a website's owner is the superuser, who can do anything to
it anyway.

It also checks any "group" objects which the user may be a member of.
(Of course, as user ⇔ group is a many-to-many relationship, there's also a
"membership" object, which can also be used for other interesting ideas
like wwebpages ⇔ tags.)

Tracking
--------

Pybble can track changes. Not surprisingly, there's a Tracker object which
links new objects to the page they were created in (and their site). For
changes and deletions, additional Change and Delete objects are created
which record what happened and who did it, allowing you (in principle) to
undo any action. In practice this is not implemented yet. *Yet*.

This is especially cool for recovering from spammers. Again, it's not yet
implemented, but the data structures to tell Pybble "do as if this person
never existed" are present.

Object Deletion
---------------

Pybble doesn't delete objects, because (a) frankly it doesn't (yet) presume
to know what to do with the other objects which point to it, and (b) you
cannot undo deleting something if you don't have the data any more.

Instead, it clears the victim's owner/parent/superparent information, so
that it won't be found any more, and copies these pointers to a new Delete
object so that the deletion can be undone.

User notification and RSS
-------------------------

Users can attach a `WantTracking` object to anything in the system
(assuming they have permission to). A background job then creates
`UserTracking` objects which traverse the hierarchy, linking these
data structures to the actual `Tracking` object which describes a change,
thus (a) establishing a timeline and (b) demonstrate the need for all three
parent-object pointers.

It's a matter of a bit of template programming to create a RSS feed from
this. Or to send an email with the day's changes. This actually works,
though the user interface to describe these things needs a better design so
that Joe User can actually understand all of that. :-/


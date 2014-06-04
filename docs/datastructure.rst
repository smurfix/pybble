Pybble's data
=============

Data structures in web frameworks are difficult. You want to be both
flexible *and* generic.

Pybble's approach is rather simple: an object is one row in one SQL table.
Each kind of object gets its own table. There's an index table (`ObjType`)
which keeps track of all database-mapped classes, including itself.

References to specific classes are simply foreign keys. References to "any"
object are possible, but the SQL database des not enforce integrity.

Deleted entries are marked with s "Deleted" boolean which every table has.
The standard query simply ignores deleted entries. Physical cleanup is
TODO. Each object is linked to a "Tracker" object which records who created
it when; changes and deletions are handled similarly.

Pybble has a loose object hierarchy which is used fo looking up templates
and ACLs. Every object which participates in this hierarchy has a "parent"
field which ultimately links to the website it appears on, which itself
links to the Pybble root site.

Websites
--------

The `site` object is the core of Pybble. It declares the root of one
particular URL.

The main question many new users have is "how do I tell my CMS what to
display on the front page"? The answer is: Templates.

Templates
---------

Pybble templates are distributed across a bunch of data structures because,
well, SQL.

At the bottom there's the actual machinery which transforms some text
(like a Jinja template) to HTML (or RSS or whatever). Pybble calls that a
translator.

Since one such machine can work on many input formats and can spit out
equally many outputs, the next step is an adapter which associates a
concrete combination of input+output types to that translator.

The next step is the actual template, which contains the data (usually text)
that describes the frame around which the translator will mangle its input
to output.

Since real site hierarchies don't always conform in any easy way to
convenient places to attach a template, the next step is a TemplateMatch
object which links your site's objects to the templates to use.

The rendering process depends on whether you have a concrete object you'd
like to display. For instance, your site has a home page, so viewing that
looks like

	@expose('/')
	def show_home():
        return render_my_template(current_site)

On the other hand, when you don't have a convenient object, you can
directly show a template:

	@expose('/about')
	def show_about():
        return render_template('about')

In the first case, the template in question will be located by its input
and output MIME types; the second does a simple lookup by name.
The result consists of whatever the templating system emits, plus an
output MIME (pseudo) type.

The template can thus either produce your complete page, probably via the
templating system's inheritance methods, and tell Pybble that it produced
‘text/html’ – or it can emit somethign like a ‘html/subpage’ pseudo type.
Pybble will find a template to transform that into your complete webpage,
passing the original object along so you can do context sensitive menus
via the templating system.

HTML-Escaping
-------------

Pybble wants to be a secure system. Pybble's templating system(s) need to
be configured so that they auto-HTML-escape *everything*. The only
exceptions are form data (formalchemy has been convinced, in the author's
version, to tag its rendering output appropriately) and output from
templates that's embedded in another template; since most templating
systems don't use `markupsafe` for that, Pybble will add an appropriate
wrapper.

Feeding templates into Pybble
-----------------------------

With no templates at all, administering a website would be impossible, so
the initial template data have to come from the file system.

To facilitate this, the manager's 'populate' command understands a couple
of metadata in template files. They have to be at the immediate start of
the file; anything not in this format terminates parsing and will be fed to
the templating engine.

	##src pybble/site
	##dst html/subpage
	##typ template/jinja
	##named 0
	##weight 10000
	##inherit -
	##match root

This tells Pybble that this is an unnamed template which translates your
site to an HTML pagelet, using the Jinja template engine, and that it shall
be attached to the system's root.

`src `dst` and `typ` are MIME types; the source may use a wildcad subtype.

`named` is a Boolean denoting that the template shall be findable by name.

`match` is the datum the template is to be attached to and can be given
more than once, though so far the only recognized values are "root",
"superuser" and "parent" (which is different from "root" for templates that
come by way of a blueprint).

`weight` is the template's priority. Lower is better. Pybble auto-adds a
few points whenever it needs to take an indirection step so that you can
add a "show this, no matter what" page by giving it a weight of -1000 or so.

`inherit` defaults to "-" (or "None"); this affects the following "match"
entries and tells Pybble whether the template applies to the destination
only (False), to all of its children (True), or both (None).


Static data
-----------

Pybble supports serving static data via a "big" web server. By default,
access to these is not controlled. However,

* Pybble generates content-addressed file names. If you serve a file named
  `foo.pdf`, Pybble actually stores it (and links to it) as
  `/static/ab/_/foo-cdefghijklm.pdf`, where `c-k` are random letters or
  digits, and the path plus the `lm` end letters allow Pybble to recover
  the file's serial number and thus the internal object wich links to it.
  (This is not actually implemented, but the information is there if you
  need it.)

  Actually, `c-k` only seem random; in fact they're generated from the
  SHA1 checksum of the file's contents.

  This means that, if you teach your web server to *not* generate
  directory indices for /static (or whichever path prefix you use),
  files you don't link to are not discoverable. Also, a file's URL changes
  every time its content changes, which is very helpful if you upload a new
  version of jQuery to your site and want your clients to use it right
  away, not sometime next year when the hard disk with their cached copy
  dies. (Some web caches are well-known for their blatant disregard of
  Expires: headers.)

* You can teach your web server to check the `Referer`: header. This can be
  circumvented easily, but the main reason for random third-party linking
  (conserving one's own bandwidth on somebody else's dime) is thwarted
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

Users; Authentication
---------------------

Pybble has the usual "user" and "group" objects. Attaching users to
sessions and all that should be managed by `Flask-Login` but is not yet,
because when Pybble was originally written there was no `Flask`, much less
`Flask-Login`.

The "user" table of course has a password column. Passwords are hashed
with your site secret, so if you need to change that, all logins become
invalid.

Authorization
-------------

There's a "permission" object. It says whether user A can do action B to
objects of type C, possibly creating an object of type D. The latter is
relevant when we ask "can the user add a comment to a wiki page".

The permission's parent is the object it grants access to; if it's not
found there, the system checks the parent, until it gets to the root
website, which has no parent.

It also checks any "group" objects which the user may be a member of.

As user ⇔ group is a many-to-many relationship, there's a generic
"membership" object, which can also be used for other ideas.
Webpages ⇔ tags comes to mind.

Tracking
--------

Pybble tracks all changes. Not surprisingly, there's a Tracker object which
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
(assuming they have permission to do so). A background job then creates
`UserTracking` objects which link these to the actual `Tracking` object
which describes a change, thus establishing a user-specific timeline.

It's a matter of a bit of template programming to create a RSS feed from
this timeline. Or to send an email with the day's changes. This actually works,
though the user interface to describe these things needs a better design so
that Joe User can actually understand all of that. :-/

The `WantTracking` object's `user` pointer is generic, so you can attach it
to any page you want a generic RSS feed to appear on.

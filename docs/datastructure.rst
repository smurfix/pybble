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

An object's superparent is supposed to be immutable (except for setting it
to None when 'deleting' the object).
This is not enforced anywhere (yet), but Pybble require a restart if you
ever change e.g. a site's app (pointed to as the site's superparent).

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

Since one such machine might be able to work on many inputs and can spit
out equally many outputs, the next step is an adapter which associates a
concrete combination of input+output types to that translator.

The next step is the actual template which contains the data (usually text)
that describes the frame around which the translator will mangle its input
to output.

Since real site hierarchies don't always conform in any easy way to
convenient places to attach a template, the next step is a TemplateMatch
object which links your site's objects to the templates to use.

With that, let's do a walk-through of how Pybble displays your site's
/about page; we assume that your code is simply

	@expose('/about')
	def show_about():
        return render_template('about')

This is the easy case, since the lookup is performed by name and you don't
have an object to display. Pybble therefore uses an input type of
‘pybble/_empty’ and searches for a template which can transform that to
‘text/html’, starting at your site object. Your site probably won't have
such a translator, so it looks again on the `parent` page, which is likely
to be the system root. That has a special low-priority translator attached
which knows that the usual site structure is to have an inner content and a
layout; the inner content has a type of ‘html/subpage’. (This is hardcoded,
except for the "html" part which can be anything.)

Thus, that translator looks for a template that transforms ’pybble/_empty’ to
’html/subpage’ and which is (a) attached to your site, (b) named 'about'.
Let's assume that you have created one. After interpreting that template,
Pybble has something of type ’html/subpage’; it now re-enters the process
with that.

This time, search proceeds 


It basically looks uses the object attached to the URL
for a template which 

A Pybble template gets some input (for instance, a Pybble object) and
textual data in some form (e.g. a Jinja template), and emits output
(a HTML subpage).

So this will transform your homepage into that homepage's content.
The surrounding framework (menu structure and whatnot) is generated in
another template: the usual way is to have a default template associated
with your website ("translating" from `pybble/*` to `text/html`), which
contains a "translate this object to `html/subpage` (this is not a "real"
MIME type).

To sum this up, a template has an input format (pybble/site),
an output format (html/subpage), some chunk of text you can edit
(maybe just configuration parameters, or a whole Jinja template),
maybe some chunk of cached data you can't edit, and a translator which
understands a couple of MIME types and emits the appropriate output.

Pybble keeps track of all of this by way of MIME types; some real, some
not. It also has special association objects; thus you can teach it to use
an entirely different look-and-feel for the text and the image part of your
website.

Feeding templates into Pybble
-----------------------------

With no templates at all, administering a website would be impossible, so
the initial template data have to come from the file system.

To facilitate this, the manager's 'populate' command understands a couple
of metadata in template files. They have to be at the immediate start of
the file; anything not in this format terminates parsing.

	##src pybble/site
	##dst html/subpage
	##typ text/jinja
	##named 0
	##inherit -
	##match root

This tells Pybble that this is an unnamed template which translates your site
to an HTML pagelet, using the Jinja template engine, and that it shall be
attached to the system's root.

`src `dst` and `typ` are MIME types; the source may use a wildcad subtype.
`named` is a Boolean denoting that the template shall be findable by name.
`match` is the datum the template is to be attached to and can be given
more than once, though so far the only recognized values are "root" and
"superuser".
`inherit` defaults to "-" alias None; it affects the following matches and
says whether the template applies to the attached to the destination only
(False), to all of its children (True), or both (None).


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

* TODO: Some static content needs to be generated+cached; if you have a
  SASS template but want to emit CSS, it's a good idea to store the CSS
  output somewhere instead of generating it anew every time somebody wants
  it.

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

The "user" table of course has a password column. Passwords are hashed
with your site secret, so if you need to change that, all logins become
invalid.

The LEGACY_PASSWORDS setting controls whether somebody can log in if their
password is stored non-hashed (it will be hashed as soon as the user logs
in). This is useful if you ever need to use SQL to change a password, but
dangerous if somebody who does not know your site secret should gain write
access to the database .

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


Models may have a couple of attributes which control an initial set of
permissions when a new site is created. The default is:

    _site_perm=None
    _anon_perm=None
    _admin_perm=PERM_ADMIN

    _site_add_perm=()
    _anon_add_perm=()
    _admin_add_perm=()

These are, respectively, for registered users, anonymous users, and
administrators. The first set controls the rights to existing records, the
second lists which objects this model may be added to.

If a model shall be directly accessible via an URL, it needs to participate
in Pybble's object tree, i.e. it needs an element named "parent". This can
be a property. Alernately, if you already have an element with that name,
you can use an alias:

    _alias = {'parent', 'page'}


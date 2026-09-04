"""The ``do_*`` steps of the import pipeline, each driven by its own command-line option.

`opus_import.cli` runs the requested subset in a fixed order: first `do_cart` and
`do_django` clean up the cart and cache tables, which has to happen before the permanent
tables are rebuilt because a cart row can reference them; then `do_import` performs the
observation import; then the auxiliary tables `do_param_info`, `do_partables` and
`do_table_names`, which are derived from the permanent tables and so must follow it;
then `do_update_mult_info`, `do_validate`, a second `do_cart` attempt if the first was
deferred, and finally `do_dictionary`. With ``--drop-permanent-tables`` the leading
cleanup is skipped and `do_import` performs it instead, after the drop.

Several options are not steps of their own: the work for ``--drop-permanent-tables``,
``--analyze-permanent-tables`` and ``--delete-import-bundles`` is done inside
`do_import`.

`do_import` is large enough to live in five modules rather than one. ``do_import.py``
holds the main loop (`do_import_steps`) and the per-bundle driver (`import_one_bundle`);
the ``do_import_<part>.py`` modules hold its internals and are **not** steps of their
own, so nothing outside `do_import` runs them as one:

* `do_import_tables` -- creating, deleting and copying the ``obs_`` tables;
* `do_import_mult` -- reading, caching and writing the ``mult_`` tables;
* `do_import_index` -- importing every observation in one primary index file;
* `do_import_obs` -- computing one row of one observation table.

Import each step from its own module (``from opus_import.steps import do_cart``); this
module deliberately re-exports nothing.
"""

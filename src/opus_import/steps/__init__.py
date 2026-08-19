"""The ``do_*`` steps of the import pipeline, each driven by its own command-line option.

`opus_import.cli` runs the requested subset in a fixed order: first `do_cart` and
`do_django` clean up the cart and cache tables, which has to happen before the permanent
tables are rebuilt because a cart row can reference them; then `do_import` performs the
observation import; then the auxiliary tables `do_param_info`, `do_partables` and
`do_table_names`, which are derived from the permanent tables and so must follow it;
then `do_update_mult_info`, `do_validate`, a second `do_cart` attempt if the first was
deferred, and finally `do_dictionary`.

Several options are not steps of their own: `--drop-permanent-tables`,
`--analyze-permanent-tables` and `--delete-import-bundles` are all handled inside
`do_import`.

Import each step from its own module (``from opus_import.steps import do_cart``); this
module deliberately re-exports nothing.
"""

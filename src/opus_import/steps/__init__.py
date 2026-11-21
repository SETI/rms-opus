"""The ``do_*`` steps of the import pipeline, each driven by its own command-line option.

`opus_import.cli` runs the requested subset in a fixed order: first `do_import` performs
the observation import; then finalization's steps, `do_indexes`, `do_duplicate_ids`,
`do_finalize_mult`, the auxiliary tables `do_param_info`, `do_partables` and
`do_table_names`, which are derived from the imported tables and so must follow it, and
`do_cart` and `do_django`, which recreate the cart and reset the search tables; then
`do_update_mult_info`, `do_validate`, `do_dictionary` and, last, `do_schema_version`.
The developer guide's chapter on the import steps gives what forces each part of the
order.

Several options are not steps of their own: the work for ``--scorched-earth``,
``--delete-bundles``, ``--register-bundles`` and ``--requeue`` is done inside `do_import`,
and ``--analyze-tables`` inside `do_import_tables`. `do_register` registers bundles in the
bundle registry for `do_import`, and `do_recover` deletes a queue importer's bundle under
its registry row's lock, for the importer itself, ``--requeue`` and the coordinator's
recovery of a lost importer.

The rest run outside the sequence, each alone: `do_carry_over`, for
``--carry-over-sessions-from``, and `do_generation` and `do_generation_purge`, for the
generation commands. `do_generation` also registers each writer of a schema and records
the pending generation's state for the steps of the sequence.

`do_import` is large enough to live in several modules rather than one. ``do_import.py``
holds the main loop (`do_import_steps`) and the per-bundle driver (`import_one_bundle`);
the ``do_import_<part>.py`` modules hold its internals and are **not** steps of their
own, so nothing outside `do_import` runs them as one:

* `do_import_tables` -- creating the ``obs_`` tables and deleting from them;
* `do_import_mult` -- reading, caching and writing the ``mult`` rows;
* `do_import_index` -- importing every observation in one primary index file;
* `do_import_pool` -- computing an index's rows in a pool of workers and replaying them;
* `do_import_obs` -- computing one row of one observation table.

Import each step from its own module (``from opus_import.steps import do_cart``); this
module deliberately re-exports nothing.
"""

.. _dev_guide_import_steps:

The Import Steps
================

:mod:`opus_import.steps` holds the step modules. Most are steps -- each driven by its own
command-line option -- and the rest are the internals of the largest step,
:mod:`~opus_import.steps.do_import`, which is big enough to live in several files. This
chapter walks them all.

:ref:`dev_guide_import_overview` gives the shape of a run; :ref:`dev_guide_import_running` gives
the options. Nothing here is optional reading if you are changing the pipeline: the
order the steps run in is forced by foreign keys and by what each one needs to already
exist, and getting it wrong produces a database that looks fine and is not.

The order, and what forces it
-----------------------------

.. mermaid::
    :zoom:

    flowchart TD
        SE["do_import:<br/>--scorched-earth, --delete-bundles"]
        I[do_import:<br/>the observation import]
        R{every bundle in the<br/>registry done?}
        K[do_indexes:<br/>the secondary keys]
        DU[do_duplicate_ids:<br/>one copy of each OPUS ID]
        FM[do_finalize_mult:<br/>prune, override and rank the mult values]
        P[do_param_info]
        PT[do_partables]
        TN[do_table_names]
        C[do_cart:<br/>recreate the empty cart table]
        DJ[do_django:<br/>reset user_searches and search_results,<br/>flush the web cache]
        A[analyze the tables]
        UM[do_update_mult_info]
        V[do_validate]
        D[do_dictionary]
        SV[do_schema_version]

        SE --> I --> R
        R -->|yes| K --> DU --> FM --> P --> PT --> TN --> C --> DJ --> A --> UM --> V --> D --> SV
        R -->|"no: --finalize refuses"| X[exit with failure]

* **The erase and the deletes come first**, inside
  :func:`~opus_import.steps.do_import.do_import_steps`: ``--scorched-earth`` so that no
  ``mult`` row survives and the ids start again, and ``--delete-bundles`` so that
  an import in the same invocation does not resume a bundle being removed.
* **Finalization refuses after the import and before its first step**: ``--finalize``
  exits with failure while any bundle in the bundle registry is not ``done``
  (:ref:`dev_guide_import_steps_registry`), so a refused finalization changes nothing
  and an import in the same invocation can still finish the registry first.
* **The keys come right after the import**, and the foreign keys after every other key,
  because a fresh import loads its tables without them; the duplicate step follows,
  because it finds the copies through the key on ``opus_id``.
* **The mult step comes after the duplicate step and before the auxiliary tables**: the
  duplicate step's deletions can leave a value that no observation holds, and
  ``partables`` reads the ``mult`` rows.
* **The auxiliary tables come after the import** because each is derived from which
  observation tables exist and from their schemas.
* **The cart and search tables come after the import** because ``cart`` carries a
  foreign key onto ``obs_general``, which must exist first; a schema without it logs an
  error and gets no cart.
* **The tables are analyzed after them**, so that the statistics count every table's
  rows.
* **The dictionary comes after them** because nothing else depends on it.
* **The schema version comes last** because its row is what makes the schema
  servable, so it is written only once everything else, validation included, has run.

The steps
---------

.. _dev_guide_import_steps_do_cart:

opus_import.steps.do_cart
~~~~~~~~~~~~~~~~~~~~~~~~~

Creates the empty ``cart`` table the web application fills as users select products.
Option: ``--create-cart``, part of ``--finalize``.

:func:`~opus_import.steps.do_cart.create_cart` drops ``cart`` and creates it again from
``cart.json``. There is nothing to import into it, and it starts empty on every run.
``cart`` has a foreign key onto ``obs_general``, so it cannot be created before
``obs_general`` exists, which is why it runs after the import, in the finalization
sequence; on a schema without ``obs_general`` it logs an error and creates nothing. The
foreign key cascades on delete (:ref:`dev_guide_table_schemas`), so deleting a bundle,
on either write path or under ``--delete-bundles``, deletes the cart rows that name its
observations rather than being refused.

.. _dev_guide_import_steps_do_carry_over:

opus_import.steps.do_carry_over
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Carries the sessions and carts of the schema being served over into the schema a deploy
promotes. Option: ``--carry-over-sessions-from SCHEMA``, which runs alone and is outside
the sequence above; ``deploy_new_code_and_database.sh`` runs it while the web service is
stopped (:ref:`user_guide_deployment_carry_over`).

:func:`~opus_import.steps.do_carry_over.carry_over_sessions` calls
:meth:`~opus_import.importdb.super.ImportDBSuper.carry_over_sessions` and logs what it
copied. The MySQL implementation runs one transaction, committed at its end and rolled
back on any failure, so a failure leaves the target's two tables as they were. In it, it
reads the source's ``django_session`` and counts its ``cart``, so a source without them
fails before anything is written; empties the target's ``cart`` and ``django_session``
with ``DELETE`` (``TRUNCATE`` would commit at once), so a second run gives the same
result; and runs two ``INSERT ... SELECT`` statements: the sessions whose
``expire_date`` is later than ``UTC_TIMESTAMP()`` (Django stores it in UTC) and that own
a cart row in the source, then each source cart row joined to the target's ``obs_general`` by ``opus_id`` and to the
copied sessions by its session. The rows are written with the target's own
``obs_general_id``, ``opus_id`` and session key, and only the columns every release's
``cart`` shares are named, so the copy does not depend on either schema's character sets
or on a column one release's ``cart`` has and another's lacks. A cart row's own ``id`` is
not copied. The cart rows the source held and the target did not take, because their
session expired or their observation is gone, are logged as dropped. A source name that
is not a plain identifier is refused, and logged with the reason, before any statement.

Only the sessions that own a cart row are copied because nothing else a visitor would
miss is kept in a session: ``grep -rn "request.session\[" src/opus_app`` finds the
``has_session`` marker and ``cum_download_size``, the running total that caps one
session's downloads. The served schema keeps a session for every caller of the public
API that sends no cookie, for as long as a session lasts, and copying those would
lengthen the time the web service is stopped.

The command line refuses the option with any other step and when ``SCHEMA`` is the
schema it writes into, compared without regard to case as a server with
``lower_case_table_names`` set compares them, before the database is opened, since
emptying the target would then empty the source.

.. _dev_guide_import_steps_do_django:

opus_import.steps.do_django
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Empties the tables the web application stores its searches in, and empties its cache.
An import changes what a search returns, so every stored search's results are out of date
once it finishes.

:func:`~opus_import.steps.do_django.reset_search_tables` drops ``user_searches`` and
``search_results`` (:data:`~opus_import.steps.do_django.SEARCH_TABLES`) and creates each
again, empty, from its schema file. The new ``user_searches`` starts its ids above the
highest id the old one held
(:meth:`~opus_import.importdb.super.ImportDBSuper.set_next_id`), so a search number a
web worker still remembers from before the reset matches no row, rather than matching a
different search. Option: ``--reset-search-tables``, part of ``--finalize``, which runs
it after ``--create-cart``. Deploying a new database runs it too, alongside
``--import-dictionary``, so that searches made while the staged installation was being
tried out are not served.

**Then it empties the web application's cache.** The cache maps each search to its number
and holds answers computed from the old data, so none of it is valid after the reset. The
step runs :data:`~opus_import.steps.do_django.CACHE_FLUSH_COMMAND`, which is ``python -m
opus_app.clear_django_cache`` under this interpreter, in a separate process, because the
cache is configured by the web application's settings; it needs only the ``OPUS_CONFIG``
the import already has. If that process exits with a nonzero status, the step fails
with :exc:`~opus_import.steps.do_django.CacheFlushError`. A simulated run, whose database
is read-only, skips it.

**Without memcached** there is no shared cache to empty. The separate process falls back
to its own local memory, empties that, and succeeds, and each web worker keeps its own
cache until it is restarted (:ref:`dev_guide_webapp_caching`).

.. _dev_guide_import_steps_do_import:

opus_import.steps.do_import
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The observation import. Option: ``--import``, which ``--do-it-all`` implies. It also
owns the work for two options that are **not** steps of their own -- ``--scorched-earth``
and ``--delete-bundles`` -- because each has to happen at a particular point in this
sequence.

**The path.** An invocation that imports bundles first reads the target schema's state
(:func:`~opus_import.steps.do_import.choose_import_path`) and logs one line naming the
path it takes, the schema and its version
(:ref:`dev_guide_import_write_paths` gives the reasons):

* **no** ``schema_version`` **row, and none of the secondary keys finalization adds** on
  any observation table -- an empty schema, or one a fresh import is part way through,
  since a full import runs one invocation per bundle group: the **fresh import**. Each
  observation table is created with only the keys a load needs
  (:ref:`dev_guide_import_db_keys`);
* **one row, holding this release's version, in the** ``ready`` **or** ``appending``
  **state**: the **append**, into the tables with their keys in place;
* **a row of another version, more than one row, or another state**: refused, with a
  fatal message naming ``opus_import --scorched-earth --yes``, since a schema is
  re-imported under the release that will serve it;
* **no version row but such a key**: a finalization that was interrupted. The import is
  refused with a fatal message naming ``--finalize``. A finalization-only invocation
  completes it, since every finalization step is idempotent; ``--scorched-earth --yes``
  starts over.

A refusal comes before anything is written, and the invocation exits with failure.
:mod:`opus_import.cli` chooses before its first write; an invocation that erases the
schema first chooses after the erase.

:func:`~opus_import.steps.do_import.do_import_steps` is the whole sequence, and it runs
whether or not ``--import`` was given, because it is where the erase and the deletes
live. In order:

1. Reset :attr:`~opus_import.context.ImportContext.import_has_bad_data`, and expand the
   bundle descriptors into a list of bundle ids.
2. **Erase the schema**, under ``--scorched-earth``, which :mod:`opus_import.cli` has
   already refused without ``--yes``. It logs the warning
   ``** DELETING EVERY OPUS TABLE IN SCHEMA <schema> **`` and drops every table the
   import creates (:func:`~opus_import.steps.do_import_tables.delete_all_opus_tables`).
   This has to happen first, so that no ``mult`` row survives, the mult fields are
   numbered again from 1, the bundles are numbered again and the first one's id range
   starts again from 0, and each field's mult ids start again from 0.
3. **Delete the named bundles**, under ``--delete-bundles``: each one's rows from every
   observation table, then their rows in the bundle registry
   (:func:`~opus_import.bundle_registry.unregister_bundles`). It runs on any schema
   state, and refuses, before deleting anything, a named bundle another process holds
   ``importing``. A schema whose version row is this release's version and ``ready`` is set to
   ``appending`` before the first delete, as an append sets it, since the deletion changes
   a finished schema; no other state is changed.
4. **Return bundles to the queue**, under ``--requeue``
   (:func:`~opus_import.steps.do_import.requeue_bundles`): every named bundle must be
   ``failed``, or ``importing`` under no queue importer (``process_id`` NULL, as a plain
   ``--import`` leaves one), or nothing changes and the invocation fails. A queue
   importer's bundle is left to recovery, which checks the importer's lock under the
   bundle's row lock. Each is taken from the state it was read in as the invocation's
   own hold, under a new ``started_at`` (from ``importing`` only while ``process_id`` is
   still NULL), deleted from every observation table, and set ``pending`` only while
   that hold stands; a bundle another process took after the states were read is left
   to it, with nothing deleted, and the invocation fails.
5. Stop here unless ``--register-bundles``, ``--import`` or ``--join`` was given.
6. **Choose the path**, as above, if :mod:`opus_import.cli` has not.
7. Under ``--register-bundles``, **register the named bundles** in their order
   (:ref:`dev_guide_import_steps_registry`) and stop. A bundle already registered keeps
   its state, so a rerun keeps what is ``done`` and moves nothing another process holds;
   on the append path the version row is set to ``appending`` only when a bundle was
   added.
8. Under ``--join``, **import from the queue** until no bundle is ``pending``
   (:func:`~opus_import.steps.do_import.import_from_queue`, below) and stop.
9. **Register the bundles**, returning those already registered and ``done`` or
   ``failed`` to ``pending``, and refusing, before anything is written, a named bundle
   another process holds ``importing``, with a message naming the ``--requeue`` that
   returns it once that process has stopped. On the
   append path the bundles are every bundle the registry holds that is ``pending`` or
   ``failed`` and is not named, in registration order, followed by the named bundles,
   and the version row is then set to ``appending``; on a fresh import they are the
   named bundles. A bundle OPUS skips is never registered.
10. **Import each bundle.** It is moved to ``importing`` -- a bundle another process
    took meanwhile is an error, and is left to that process -- and
    :attr:`~opus_import.context.ImportContext.bundle_has_errors` is cleared; it is deleted
    from every observation table
    (:func:`~opus_import.steps.do_import_tables.delete_bundle_from_obs_tables`) with
    foreign key checks on, so ``cart``'s cascading foreign key removes the cart rows that
    name its observations; it is imported through
    :func:`~opus_import.steps.do_import.import_one_bundle` with the checks off
    (:meth:`~opus_import.importdb.super.ImportDBSuper.foreign_keys_unchecked`), which
    validation's orphan count stands in for; and it is marked ``done``, or ``failed``
    when it logged an error, unless ``--ignore-errors``. Deleting first is what makes
    importing a bundle again, in the same invocation or a later one, replace it rather
    than load a second copy. A bundle whose import fails stops the loop, leaving the ones
    after it ``pending``, unless ``--ignore-errors``.

Any error at all makes the function return False once the loop ends, unless
``--ignore-errors``, and the invocation exits with failure. Neither path finalizes. A
failed fresh import leaves a schema with no version row and a failed append leaves one
``appending``, and a web application that loads either refuses to serve it, as both
deploy scripts refuse to promote it.

**The queue.** Under ``--join``,
:func:`~opus_import.steps.do_import.import_from_queue` first records the importer in
``import_process`` and takes its lock on a connection of its own
(:func:`~opus_import.import_processes.start_importer`): it raises the idle limit of that
connection to a year, inserts the ``running`` row, reads its ``process_id`` back, takes
the lock without waiting, and only then commits, and logs ``Importer <process_id>``. It then
claims a bundle (:func:`~opus_import.bundle_registry.claim_bundle`), logs ``Claimed
bundle <bundle>``, deletes and imports it as above, and marks it ``done``
(:func:`~opus_import.bundle_registry.finish_claimed_bundle`); it then claims the next,
and logs ``No pending bundle is left to claim; this importer exits`` when none is left,
recording itself ``exited`` before it frees its lock. A claim is one transaction: a
locking read, through the registry's key on ``(state, size_estimate, bundle_number)``
scanned from its highest entry, of the first ``pending`` row no other session holds
(``FOR UPDATE SKIP LOCKED``), then the move to ``importing`` naming the importer in
``process_id``, committed only while the importer holds its lock.
Under ``READ COMMITTED`` the read locks only the row it returns, so several importers
claiming at once each take a different bundle, the largest left, and none waits for
another. Positional bundle descriptors limit the bundles claimed, and ``--exclude-bundles``
keeps it off the bundles it names. A claim that finds nothing takes and releases
registration's lock, so it waits for a registration in progress, whose new rows the
locking read passes over until they commit, and claims once more before the importer
exits. Before the first claim, an importer whose schema has no registry waits the same
way, reads the table names from the server again
(:meth:`~opus_import.importdb.super.ImportDBSuper.forget_table_names`), and fails with a
message naming ``--register-bundles`` if there is still none. A bundle whose import
raises or logs an error has its rows deleted while it is still ``importing`` under the
importer, its registry row held on a second connection, so no claim and no plain
``--import`` takes it meanwhile, and is then marked ``failed`` in that same hold
(:func:`~opus_import.steps.do_recover.release_bundle`); the importer goes on, the bundle is never claimed again, and the importer exits with failure
at the end. Under the
test-only fault ``OPUS_IMPORT_FAULT=hold_after_claim:<seconds>`` an importer sleeps
that long after each claim commits (:ref:`the import's fault sites
<dev_guide_testing_faults>`).

Each chunk of rows an importer loads runs under the bundle's guard
(:class:`~opus_import.import_processes.BundleGuard`): its first statement advances the
bundle's ``rows_done`` only while the registry names the importer as importing it, the
importer's ``progress_at`` advances beside it, and before the commit the lock connection
confirms it holds the lock. Should either fail, the chunk is rolled back and the importer
aborts its bundle (:func:`~opus_import.steps.do_import.abort_bundle`) and exits with
failure naming its lock. An abort, a failure, and the delete before each import delete
the bundle's rows while a second connection holds the bundle's registry row and has
checked that it still names the importer
(:func:`~opus_import.steps.do_recover.release_bundle`); a coordinator's recovery of a
lost importer's bundle does the same, after checking again that the importer's lock is
free (:func:`~opus_import.steps.do_recover.recover_lost_importers`). Every bundle delete
reads the schema's tables from the server first, so it reaches a table another importer
created after this connection opened. After one interrupt an importer claims nothing new
once its bundle is done; a second, wherever it lands, aborts every bundle the registry
has ``importing`` under the importer, and any later one is only counted, so nothing
interrupts the abort. A
plain ``--import`` takes no lock: its bundles keep ``process_id`` NULL, and only its
``obs_general`` chunks carry ``rows_done``, matching no importer.

:func:`~opus_import.steps.do_import.import_one_bundle` is the per-bundle driver
described in :ref:`dev_guide_import_per_bundle`. It resets the per-bundle caches, skips
a bundle OPUS deliberately ignores
(:func:`~opus_import.steps.do_import_tables.opus_imports_bundle`), looks the bundle up
in ``BUNDLE_INFO``, takes the bundle's registered id range
(:func:`~opus_import.bundle_registry.bundle_ids`), finds the primary index files
(:func:`~opus_import.primary_index.locate`) and imports each one. A bundle that needs
more observation ids than its range holds fails, the error naming the bundle, its
capacity and the rows its labels declared. Under the
test-only fault ``OPUS_IMPORT_FAULT=log_error:<bundle>`` it logs one error inside that
bundle and carries on (:ref:`the import's fault sites <dev_guide_testing_faults>`).

.. _dev_guide_import_steps_registry:

The bundle registry: opus_import.bundle_registry and opus_import.steps.do_register
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:mod:`opus_import.bundle_registry` is the import's record of its work: one table,
``import_bundle``, holding a row per bundle with its number, its id range and its state
(:ref:`dev_guide_database_schema_import_bundle`). The states are also the work queue the
importers draw from.

**Registration.** :func:`~opus_import.steps.do_register.register_bundles` registers
bundles in the order given, which is the import order. It holds a server-wide named lock
(``GET_LOCK`` on the name :func:`opus_import.importdb.lock_name` gives the schema and
``register``) for its whole length, so two registrations never interleave. Under the lock
it first creates the registry and the mult tables where the schema lacks them, since a
table's creation commits on its own, and then, in one transaction:

* adds each bundle the registry lacks, as ``pending``, with the next ``bundle_number``,
  a ``size_estimate`` and an id range: ``id_capacity`` is a hundred times the size
  estimate, room for a bundle that has grown and for an index row that gives several
  observations, and ``first_id`` is where the last registered range ends, so the ranges
  ascend in ``bundle_number`` order. A range that would pass ``obs_general.id``'s
  largest value refuses the registration;
* leaves the bundles it holds as they are, unless the caller asks for them back, which
  ``--import`` does: a ``done`` or ``failed`` one returns to ``pending``, and an
  ``importing`` one refuses the registration;
* numbers every mult field ``mult_field`` lacks
  (:func:`~opus_import.mult_fields.ensure_mult_fields`) and writes the rows and groups of
  every pinned field from its ``mult_options``
  (:func:`~opus_import.steps.do_import_mult.register_pinned_fields`).

The size estimate is the row count the bundle's primary index labels declare
(:func:`~opus_import.primary_index.declared_rows`). A PDS3 index file is its own label,
and a PDS4 index's label is the ``.xml`` file beside it; either is read by
``pdstable.PdsTable`` with ``defer_load=True``, which reads the label and not the table,
so the count is the rows of the table the import reads. For a PDS4 index with no label,
as some OPUS reads are, the count is the index's own rows. A bundle OPUS imports with no
``BUNDLE_INFO`` entry, no primary index file, or a label ``pdstable`` cannot read, such
as one without ``ROWS``, refuses the whole registration, naming the bundle and the
label, before anything is written.

**Why registration order fixes every id.** A bundle's observations take ``first_id``
and the ids after it, in the order they are computed
(:class:`~opus_import.bundle_registry.BundleIds`), so ids depend only on the labels and
the registration order, never on which process imports a bundle or when. A bundle
already registered keeps its number and range, since its rows are deleted before it is
written again; one deleted with ``--delete-bundles`` loses its row, and is registered
afresh, after every other, when it is next imported. ``opus_import_all --prepare``
registers its whole list before any importer starts, so that importers running at once
take the numbers its order gives.

**Every move between states is conditional** on the state the bundle is expected to be
in, by an ``UPDATE`` whose condition names it
(:meth:`~opus_import.importdb.super.ImportDBSuper.conditional_update`), so that two
processes never both hold one bundle. A queue importer takes a bundle only from
``pending`` (:func:`~opus_import.bundle_registry.claim_bundle`), and ``--import`` takes
one it names from any state but ``importing``
(:func:`~opus_import.bundle_registry.start_bundle`); a bundle goes from ``importing`` to ``done`` or
``failed`` only while it is still ``importing`` under the ``started_at`` the process
wrote when it took it (:func:`~opus_import.bundle_registry.finish_bundle`), so a bundle
``--requeue`` returned to the queue and another process took is never finished, or
deleted, by the process that held it before; that process logs an error instead. Besides a queue importer's abort and a recovery, only
``--requeue`` moves an ``importing`` bundle back to ``pending``, and only one no queue
importer holds: it takes the bundle from ``failed`` or ``importing`` as a hold of its
own, and returns it under that hold once its rows are deleted. The hold is
``started_at``, to the second, so a bundle requeued and taken again within the second it
was first taken is the one case it cannot tell apart.

A bundle moves through these states:

``pending``
    Registered for import and not yet started.

``importing``
    Being deleted and loaded. Moving to it stamps ``started_at`` and starts
    ``rows_done`` again, which every committed chunk of the bundle's ``obs_general`` rows
    advances, in the chunk's own transaction.

``done``
    Imported without logging an error, or under ``--ignore-errors``. ``finished_at`` is
    stamped.

``failed``
    Its import failed, or logged an error. ``finished_at`` is stamped.

**A bundle OPUS skips is never registered.**
:func:`~opus_import.steps.do_import_tables.opus_imports_bundle` is False exactly when
the bundle's ``BUNDLE_INFO`` entry exists and has no instrument class (``grep -n
"'instrument_class': None" src/opus_import/config_bundle_info.py`` lists them; the
``GALILEO`` and ``COCIRS`` shorthands expand to some), and both the import's skip and
registration (:func:`~opus_import.steps.do_register.registrable_bundles`, which logs
``Ignoring registration of <bundle>`` at debug level) call it, so no row waits for an
import that will never come.

**What a bundle's errors do.** A bundle has errors when its import fails or anything
logs an error while it runs: every site that marks the run as having produced bad data
(:meth:`~opus_import.context.ImportContext.mark_bad_data`) also sets
:attr:`~opus_import.context.ImportContext.bundle_has_errors`, which is cleared at the
start of each bundle. Without ``--ignore-errors`` such a bundle is ``failed``, the loop
stops at a bundle whose import fails, and the invocation exits with failure. With it,
the bundle is ``done`` despite its errors and the loop goes on: ``--ignore-errors`` is
how a debugging run reaches ``ready`` with errors.

**An unfinished registry is never finalized or marked ready.**
:func:`~opus_import.bundle_registry.unfinished_bundles` lists every bundle that is not
``done``. While it lists any, ``--finalize`` refuses to run, before its first step, so
nothing is changed, and ``--write-schema-version`` refuses to write ``ready``, neither
inserting the version row nor changing ``appending`` to ``ready``. Each refusal is a
fatal message naming every such bundle with its state, and saying to import them again
or remove them with ``--delete-bundles``; the invocation exits with failure and the
version row stays as it is, so a failed append followed by its closing invocations stays
``appending``. :mod:`opus_import.cli` checks after the invocation's own deletes and
import, which can finish the registry. With the table absent, or every bundle ``done``,
neither step is refused. ``opus_import_all --finish`` gives its own account of the same
refusal before it runs any of its invocations.

**The registry is the one record of an append in flight.** The invocation that names an
append's bundles sets the version row ``appending``: a plain ``--import``, which also
returns those bundles to ``pending``, or ``--register-bundles`` before several
``--join`` importers, which registers the ones that are new and does so only when there
are any. A bundle already ``done`` is imported again by a plain ``--import`` naming it. A failed append leaves the schema
``appending``, the bundle it was on ``importing`` or ``failed`` and the bundles after it
``pending``. The next ``--import`` on the append path resumes every bundle that is
``pending`` or ``failed`` and is not named, in registration order, before the ones it
names, which keep their named order, and logs the list; because each bundle is deleted
before it is written, the rerun is clean. A bundle left ``importing`` is resumed only
once ``--requeue`` returns it to ``pending``, since the registry cannot tell a process
that stopped from one still importing. A fresh import resumes nothing on its own: a
failed bundle is imported again by naming it. A failed bundle's rows stay until it is
next imported, which deletes them first, or until ``--delete-bundles`` deletes them and
its registry row; a queue importer deletes them itself.

``--scorched-earth`` drops ``import_bundle`` with every other table the import creates.

.. _dev_guide_import_steps_create_indexes:

opus_import.steps.do_indexes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Adds the secondary keys a fresh import left out. Option: ``--create-indexes``, the first
step of ``--finalize``.

:func:`~opus_import.steps.do_indexes.create_indexes` compares, for every observation
table, the keys
:func:`~opus_import.table_keys.add_secondary_indexes` derives from its schema with the
keys the server reports (:meth:`~opus_import.importdb.mysql.ImportDBMySQL.read_table_keys`),
**by kind and ordered columns, never by name**, since the server names an unnamed key
itself, after its first column and with a numeric suffix when that name is taken. Only the missing keys are added, so the step is
idempotent: after an interruption it adds what is left, and on a finished schema it
logs that every table has every key and does nothing -- which is what it finds after an
append into tables that already have them, while a table the append created is keyed
here. It then adds them in three phases:

1. **The plain keys**, grouped per table into ``ALTER TABLE ... ADD KEY ..., ADD KEY
   ...`` statements, run for different tables at once over ``[import] index_workers``
   connections (:meth:`~opus_import.importdb.super.ImportDBSuper.build_indexes`), as
   :mod:`opus_import.cli` resolved it against the ceiling
   (:ref:`dev_guide_import_running_parallelism`) -- ``"max"`` is the ceiling itself. The
   list includes a plain key on every foreign-key column no other key leads, so the
   index each foreign key needs already exists, and adding the foreign key does not have
   to create it, one table at a time. No packaged schema has such a column: every
   observation table's ``obs_general_id`` leads its primary key or, in
   ``obs_surface_geometry_target``, a plain key the table is created with.
2. **The foreign keys**, one at a time with ``foreign_key_checks`` off, after every
   plain key: with the checks off, adding a foreign key is an in-place change that does
   not read the rows already there, and each one takes an exclusive lock on
   ``obs_general``. Because nothing then checks those rows, validation counts the
   orphans instead (:ref:`dev_guide_import_steps_do_validate`).
3. **ANALYZE** of every table that gained a key.

**Memory and temporary space.** Before each statement, the connection's sort buffer
(``innodb_ddl_buffer_size``, where the server has it) is sized to the estimated sort of
the largest key the statement builds (the estimate below), because a buffer far larger
than the sort costs time on every index. The server holds a whole buffer for each index
it is building at once -- every index the statement adds, up to the server's
``innodb_ddl_threads`` -- so the size is never above a quarter of the server's buffer
pool divided by ``index_workers`` and by that many indexes, and the builds running at
once hold at most a quarter of the pool together. Nor is it below the server's own
setting, unless that is above the same ceiling. The sorts write to the server's own temporary directory unless ``[import]
server_tmpdir`` names another -- a directory on the database server's host, never the
import's ``scratch_dir``. Each key's temporary space is estimated as
``rows x (key bytes + primary key bytes + 10) x 1.3``, with the rows the server counts
once the table has been analyzed, which the step does first. When the database server
runs on the same computer as the import (its host is ``localhost``, ``127.0.0.1`` or
``::1``) and ``server_tmpdir`` is given and its free space can be read, that free space
(or the data directory's, if less) is a budget the statements running at once must fit
together: a table's keys are split into as many statements as it takes, a statement
waits until it fits beside the ones running, and a key whose own estimate exceeds the
whole budget is refused with an error naming it. Otherwise each table's keys go in one
statement, and the total estimate is logged.

Each statement's and each table's wall-clock go into ``--timing-json``, as
``create_indexes:<table>:<keys>`` and ``create_indexes:<table>``, with each foreign key
as ``create_indexes:<table>:<key>``.

.. _dev_guide_import_steps_do_duplicate_ids:

opus_import.steps.do_duplicate_ids
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keeps one copy of each OPUS ID. It has no option of its own: ``--finalize`` runs it,
after the keys, and skips it when adding the keys failed, since it finds the copies by
``obs_general.opus_id``, which only those keys index. OPUS IDs are compared as the
column's collation compares them, so two that differ only in case are the same ID.

Two bundles can produce the same OPUS ID -- Galileo SSI does, and so can a calibrated
bundle and its raw counterpart -- and ``obs_general.opus_id`` has a plain key, not a
unique one, so both copies load side by side; no import looks for them while it loads.
:func:`~opus_import.steps.do_duplicate_ids.delete_duplicate_opus_ids` finds every OPUS
ID with more than one ``obs_general`` row, **keeps the row with the highest id**, and
deletes the others' rows from every observation table by ``obs_general_id``, children
first. A bundle's ids come from its registered range and the ranges ascend in
registration order, so the copy kept is the one from the bundle registered later, which
on a full import is the later bundle in import order. Importing a bundle again does not
change which copy that is, since the bundle keeps its number and range; that is why
bundles that share OPUS ids are deleted and imported again together. The same holds on a
fresh import and an append alike, and whatever the order several importers claim and
finish the bundles in. This step is the only place a duplicate between
bundles is settled, and an append invalidates it, so the ``--finalize`` after every
append runs it again.

Each deleted copy is logged at info level when it came from a different bundle than the
copy kept, and as a **warning** when it came from the same bundle, which is a fault in
that bundle's data. The step runs with foreign-key checks on, so ``cart``'s cascading
foreign key removes a cart row that names a deleted copy rather than leaving it
orphaned, and ends by checking that no OPUS ID has two rows; a failure keeps the
invocation from marking the schema ready, as a validation failure does.

.. _dev_guide_import_steps_do_finalize_mult:

opus_import.steps.do_finalize_mult
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Finalizes the mult fields (:ref:`dev_guide_database_schema_mult`). It has no option of its
own: ``--finalize`` runs :func:`~opus_import.steps.do_finalize_mult.finalize_mult` after
the duplicate step and before the auxiliary tables. An append invalidates it, since a
bundle replaced or added can stop or start using any value, so the ``--finalize`` after
every append runs it again. It has three parts, in this order:

1. **Delete the values no observation holds.** In every field whose ``pinned`` is 0, the
   ``mult`` rows whose id no observation column holds are deleted.
   :func:`~opus_import.steps.do_finalize_mult.referenced_mult_ids` finds the ids in use:
   it reads each observation table once, through an unbuffered cursor
   (:meth:`~opus_import.importdb.mysql.ImportDBMySQL.stream_select`), and collects every
   mult column's distinct ids, reading a ``mult_list`` column's ids out of its JSON list
   in the same scan. A pinned field keeps every row its list gives, since the list is
   the intended set of choices; the absent value the import adds to a pinned field whose
   list has none, under
   :data:`~opus_import.steps.do_import_mult.PINNED_ABSENT_ID`, is deleted once no
   observation holds it. A deleted id is never handed out again: a new value takes the
   next id of the field's counter, ``mult_field.last_id``, which only goes up.
2. **Apply the overrides.**
   :func:`~opus_import.steps.do_finalize_mult.apply_mult_overrides` writes each column's
   ``mult_overrides`` over its field's stored rows, so an override wins over the label
   the import gave a value. An override sets any of ``label``, ``display``, ``grouping``
   and ``pin`` of the row whose value it names. A ``grouping`` the field has no group for
   gains a ``mult_group`` row with no pin. An override that names a value the field does
   not hold is logged as a warning and skipped. Then every ``mult_group`` row that no
   ``mult`` row of its field names is deleted
   (:func:`~opus_import.steps.do_finalize_mult.delete_empty_groups`), so a group an
   override empties goes in the same run.
3. **Rank every field.** :func:`~opus_import.steps.do_finalize_mult.rank_mult_fields`
   computes every value's ``disp_rank`` and every group's ``group_rank`` by the rules of
   :mod:`opus_import.mult_rank`, and writes only the rows whose rank changes. A column
   with a unit gives the rules its unit parser, so when every ordinary value parses, the
   values sort by the number they hold.

The step always returns True: nothing in it fails the step. ``--update-mult-info``
(:ref:`dev_guide_import_steps_do_update_mult_info`) applies the overrides and ranks the
fields it touched with the same functions.

.. _dev_guide_import_steps_table_swap:

Rebuilding a table by swap: opus_import.table_swap
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The three auxiliary tables and the dictionary are rebuilt on a schema the web
application may be serving -- the code-only deploy rebuilds all of them on the live
database -- so none of them is ever dropped and refilled in place. Each step builds its
table as ``<table>__new``, fills it while the live table goes on answering, and swaps it
in with one ``RENAME TABLE`` that moves the live table aside to ``<table>__old`` and the
new one into its place. MySQL applies the whole statement atomically, so a reader finds
each table as it was or as it now is, never missing and never partly filled. The
``__old`` table is dropped afterwards.

:func:`~opus_import.table_swap.rebuild_tables_by_swap` is the one entry point. It takes a
set of tables, parents first, and a fill function, and:

1. drops any ``__new`` or ``__old`` table an interrupted rebuild of the same set left,
   children before parents;
2. creates every ``__new`` table, empty, from its packaged schema, with any foreign key
   from one table of the set to another pointed at the other's ``__new`` table;
3. calls the fill, which writes every row into the ``__new`` tables. A fill that returns
   False drops them again and leaves the live tables as they were;
4. analyzes each ``__new`` table. The server's persistent statistics for a table
   created empty say it has no rows, the rename carries them across, and nothing
   recomputes them soon after a bulk fill, so a table swapped in unanalyzed goes live
   with statistics that mislead the optimizer -- at fixture scale, validation against
   such a ``param_info`` took over a third longer;
5. swaps the whole set in with one rename
   (:meth:`~opus_import.importdb.mysql.ImportDBMySQL.rename_tables_atomically`), then
   drops the ``__old`` tables.

The dictionary is the set that needs step 2: ``contexts`` and ``definitions`` swap
together, and the foreign key from ``definitions__new`` onto ``contexts__new`` follows
the rename onto the live ``contexts``. The key name the server generated follows it too.

The rename waits for any transaction open on the tables it names. Each attempt lowers
the session's ``lock_wait_timeout`` to ``SWAP_LOCK_WAIT_TIMEOUT_S`` seconds, so a rename
queued behind a long reader does not in turn hold up every reader queued behind it; a
timed-out attempt is logged at info level and tried again, up to
``SWAP_RENAME_ATTEMPTS`` times, and the session's own value is restored afterwards.

.. _dev_guide_import_steps_do_param_info:

opus_import.steps.do_param_info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``param_info``, the table that tells the web application what the search form
contains. Option: ``--create-param-info``.

Its public functions: :func:`~opus_import.steps.do_param_info.fill_param_info` writes
the rows into ``param_info__new``, and :func:`~opus_import.steps.do_param_info.do_param_info`
is the step, which rebuilds the table by swap
(:ref:`dev_guide_import_steps_table_swap`).

One row per entry that describes a category's field, read out of the **packaged
schema** of every category in order of name (:func:`~opus_import.surface_geometry.category_names`):
every ``obs_`` table in the schema but ``obs_surface_geometry_target``, and in its place
the surface geometry selector category, ``obs_surface_geometry_name``, and one category
per body the table holds (:func:`~opus_import.surface_geometry.stored_targets`). A
category's entries are those whose ``pi_category_name`` is the category: a body's are the
template's with the body's name filled in, and the selector's is the template's
``target_name``. The order is the order of the rows' ids, so the bodies' rows come before
the selector's, as their names sort before it. A column with no ``param_info`` row is
invisible to users no matter what the import wrote into it. The row copies the ``pi_*``
keys across, and three of them are read without a default --
``pi_disp_order``, ``pi_display`` and ``pi_display_results`` -- so a column that carries
``pi_category_name`` and omits one of those fails the build rather than defaulting.

Two validations happen here rather than at the schema:

* a ``pi_form_type`` naming a unit id :func:`opus_support.units.is_valid_unit_id` does
  not recognize fails the build;
* a ``pi_ranges`` naming an entry that is not in ``param_info_ranges.json`` fails it
  too.

Nothing is written until every column has been read, so a failed build leaves
``param_info__new`` empty rather than half filled -- but the build stops at the **first**
fault, so one run reports only that one. A failed build is not swapped in: the live table
keeps what the previous run wrote. A failed build also keeps the invocation from marking the
schema ready and makes it exit with failure, as a validation failure does
(:ref:`dev_guide_import_steps_do_validate`).

This step must follow the import, because which ``obs_`` tables exist is what decides
which schemas it reads, and an append that adds a table invalidates it.

.. _dev_guide_import_steps_do_partables:

opus_import.steps.do_partables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``partables``, which maps a value a user can search for onto the table of further
search parameters that value makes relevant -- choosing the Cassini mission reveals the
Cassini mission table. Option: ``--create-partables``.

Its public functions, in the same shape as :mod:`~opus_import.steps.do_param_info`'s:
:func:`~opus_import.steps.do_partables.fill_partables` and
:func:`~opus_import.steps.do_partables.do_partables`.

A row is ``(trigger_tab, trigger_col, trigger_val, partable)``. The rows are
**generated** from the configuration maps, in four groups:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Group
     - Rows
   * - Missions
     - One per entry of ``MISSION_ID_TO_MISSION_TABLE_SFX``, triggering on
       ``obs_general.mission_id``.
   * - Instruments
     - One per entry of ``INSTRUMENT_ID_TO_MISSION_ID``, triggering on
       ``obs_general.instrument_id``. An instrument id beginning ``HST`` points at
       ``obs_mission_hubble`` instead of an instrument table, because Hubble has no
       per-instrument tables -- everything is in the mission table.
   * - Spacecraft
     - One per entry of ``INST_HOST_ID_TO_MISSION_ID``, triggering on
       ``obs_general.inst_host_id``.
   * - Surface geometry targets
     - One per body ``obs_surface_geometry_target`` holds
       (:func:`~opus_import.surface_geometry.stored_targets`), triggering on
       ``obs_surface_geometry_name.target_name`` and revealing the body's category,
       ``obs_surface_geometry__<target>``.

Every group stores a ``mult`` row's id as the trigger value, because that is what the
column it triggers on holds. The web side tests the two kinds differently: an
``obs_general`` trigger fires when every observation the search finds holds its id, and
a surface geometry trigger fires when its body is one of the bodies the search selects,
whether the search names the body by its label or by its value. That difference is the
one thing to know before adding a trigger of a new kind.

Because the first three groups are generated, a mission or instrument that was never
imported still gets a row.

.. _dev_guide_import_steps_do_table_names:

opus_import.steps.do_table_names
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Builds ``table_names``, which names and orders the "Constraints" categories the search
form and the Details tab are divided into. Option: ``--create-table-names``.

Its public functions:
:func:`~opus_import.steps.do_table_names.build_table_names_rows`,
:func:`~opus_import.steps.do_table_names.fill_table_names` and
:func:`~opus_import.steps.do_table_names.do_table_names`.

:func:`~opus_import.steps.do_table_names.build_table_names_rows` is the authority on
what a category is called and what order the categories come in. It is a pure function
-- it takes a "does this table exist?" callable and the surface geometry bodies -- so
that the documentation build and the tests can ask the same question without a
database. :func:`~opus_import.steps.do_table_names.fill_table_names` reads the bodies
from the rows ``obs_surface_geometry_target`` holds
(:func:`~opus_import.surface_geometry.stored_targets`), the same derivation
``param_info`` and ``partables`` use, so the three agree; the code-only deploy rebuilds
all three on the served schema the same way.

**The set of tables is written out by hand there, not derived from the schemas**, with
two generated groups. The order it emits is:

1. ``obs_general`` -- "General Constraints", written unconditionally.
2. ``obs_pds``, ``obs_type_image``, ``obs_wavelength``, ``obs_profile``, each if it
   exists; the selector category ``obs_surface_geometry_name`` if
   ``obs_surface_geometry_target`` exists; ``obs_surface_geometry`` if it exists.
3. One category per surface geometry body, ``obs_surface_geometry__<target>``, in order
   of encoded name, labeled from the decoded name.
4. ``obs_ring_geometry``, if it exists.
5. One per mission table that exists, **generated** by looping
   ``MISSION_ID_TO_MISSION_TABLE_SFX``.
6. One per instrument table that exists, **generated** by looping
   ``INSTRUMENT_ID_TO_MISSION_ID``. A Hubble instrument's row is written with
   ``display`` set to ``N``, for the same reason as in ``partables``.

``obs_files`` is deliberately absent: it holds one row per file rather than per
observation, and users never search it. So is ``obs_preview``: its one column is the
preview images' JSON, which the results pages, the image API calls and the Detail page
read and no user searches or shows.

A surface geometry category's row names the table its rows are in, ``physical_table``,
and a body's category the body's id, ``target_name``, which is how the web application
reads the category (:ref:`dev_guide_database_schema`).

The consequence for :ref:`dev_guide_import_extending`: **a new mission or instrument
needs no change here**, because groups 5 and 6 generate its row already, and adding one
by hand would give the table a second row and a second display position. A table of a
*new kind* -- neither a mission nor an instrument table, as ``obs_wavelength`` is --
does need a row, or it has no section and its fields are invisible.

.. _dev_guide_import_steps_do_update_mult_info:

opus_import.steps.do_update_mult_info
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Writes the presentation the table schemas give the mult fields over the stored ``mult``
rows, so that editing a schema renames a value or reorders a list without a re-import.
Option: ``--update-mult-info``. **No aggregate option implies it**; the code-only deploy
gives it (:ref:`user_guide_deployment_rename_mult_value`).

:func:`~opus_import.steps.do_update_mult_info.update_mult_info` works in three parts:

1. **The pinned lists.** For each column with ``mult_options`` whose field has rows in
   this database, every entry is checked against the stored rows first. An entry whose
   id the field stores with the same value writes its ``label``, ``pin``, ``display``
   and ``grouping`` over that row; an entry neither of whose id or value the field
   stores is inserted, id and value with it; and each entry's group pin is written to
   its ``mult_group`` row. An entry whose id the field stores under another value, or
   whose value it stores under another id, is an error: writing it would change what
   the observations holding the id mean, or break the field's unique key part way
   through. **If any entry is in error, the step writes nothing**, logs each one, and
   returns False, which makes the invocation exit with failure once its other steps
   have run. A pinned field with no rows is left alone: no observation in this database
   uses it.
2. **The overrides.** Every column's ``mult_overrides`` are applied, by
   :func:`~opus_import.steps.do_finalize_mult.apply_mult_overrides`, and the groups left
   with no value are deleted.
3. **The ranks.** Every field either part changed is ranked again, by
   :func:`~opus_import.steps.do_finalize_mult.rank_mult_fields`.

It never changes the ``id`` or the ``value`` of a stored row: the id is what the
``obs_`` rows already hold, and the value is what a row means rather than how it is
shown. So no observation row changes.

A ``mult_options`` entry that :func:`~opus_import.import_util.read_mult_option` refuses
-- one that does not carry exactly the seven values
:class:`~opus_import.import_util.MultOption` names, or whose pin is not an integer --
raises :exc:`TypeError`. That is a fault in the packaged schema, and stopping is better
than writing a row built from values that landed in the wrong columns.

.. _dev_guide_import_steps_do_validate:

opus_import.steps.do_validate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Checks the invariants no database constraint can express. Option: ``--validate``.
**Nothing here changes the database**:
the tables are already written, and an import that produced them is not undone by a
validation error. Every check runs and logs each failure at error level, so one run
reports them all.

**A failure keeps the schema from being served.** When a check logged an error, the
invocation does not run ``--write-schema-version`` even if it was asked to, logging an
error instead, and exits with failure once its other steps have run, so
``opus_import_all`` stops before its own version step. ``--ignore-errors`` on
the same invocation overrides both, for a debugging run; ``opus_import_all`` never passes
it to its finishing steps.

The checks, in this order:

:func:`~opus_import.steps.do_validate.validate_param_info`
    Every user-visible column of every ``obs_`` table has a ``param_info`` row. A list
    of exemptions covers the columns that legitimately have none: ``id``,
    ``obs_general_id``, anything beginning ``d_``, any column that has a ``d_``
    companion, ``opus_id`` outside ``obs_general``, anything beginning ``mult_``,
    ``bundle_id`` outside ``obs_pds``, ``instrument_id`` outside ``obs_general``, and
    the whole of ``obs_files``. A column is looked up under its table's name, except in
    ``obs_surface_geometry_target``: its ``target_name`` under the selector category,
    ``obs_surface_geometry_name``, and every other column under the first body's
    category, which describes them as every body's does; with no body there is none,
    and those columns are not checked. It then looks for a duplicated
    ``(category_name, disp_order)`` among displayed parameters and for a duplicated
    ``slug``. Both duplicate scans use a subquery that skips its first match, so they
    report a value shared by three or more rows and stay silent about one shared by
    exactly two.

:func:`~opus_import.steps.do_validate.validate_nulls`
    Reports a column declared to allow NULLs in which no NULL was found, at **info**
    level rather than as an error: it is an observation about the schema rather than a
    fault in the data. ``obs_surface_geometry_target`` is counted once, over every body's
    rows.

:func:`~opus_import.steps.do_validate.validate_min_max_order`
    For every ``X1``/``X2`` pair, reports rows where ``X2 < X1``, listing the first
    hundred OPUS IDs. A ``LONG`` field is skipped, because a longitude range wraps and
    its low end legitimately exceeds its high end, and so is a column whose
    ``param_info`` form type is NULL. A missing ``X2``, an absent
    ``param_info`` row, or more than one, is an error; the row is looked up under the
    category ``validate_param_info`` uses. A table other than ``obs_general`` names a bad
    row by the OPUS ID of the ``obs_general`` row it joins.

:func:`~opus_import.steps.do_validate.validate_filter_wavelength_consistency`
    For every table with a ``filter_name`` or ``combined_filter`` column, checks that
    all observations sharing a filter agree about that filter's nine wavelength
    columns. ``obs_instrument_coiss`` is grouped by camera as well as by filter,
    because its two cameras carry filters of the same name. Reported as a warning.

:func:`~opus_import.steps.do_validate.validate_orphans`
    Counts, for every observation table other than ``obs_general`` and for ``cart``,
    the rows whose ``obs_general_id`` names no ``obs_general`` row, by an anti-join. A
    foreign key added with the checks off, as finalization adds them, never reads the
    rows already there, so this is the check that it holds. Any orphan is an error.

:func:`~opus_import.steps.do_validate.validate_pds_bundle_ids`
    Counts the ``obs_pds`` rows whose ``bundle_id`` differs from their ``obs_general``
    row's. ``obs_pds.bundle_id`` is the public bundle field, written beside
    ``obs_general.bundle_id``, which the per-bundle delete selects by, so a search by
    bundle and the delete would otherwise see different bundles. Any such row is an
    error.

:func:`~opus_import.steps.do_validate.validate_previews`
    Counts the ``obs_general`` rows with no ``obs_preview`` row, by an anti-join. The
    import writes one for every observation, and the results pages read an
    observation's preview images from it. Any such row is an error.

:func:`~opus_import.steps.do_validate.validate_unique_opus_ids`
    Groups ``obs_general`` by ``opus_id`` and reports any OPUS ID more than one row
    carries, with how many there are and the first ten. ``opus_id`` carries a plain key,
    and the duplicate step of ``--finalize`` is what leaves one row per OPUS ID, so a
    schema that has not been through it can hold two. Any shared OPUS ID is an error.

.. _dev_guide_import_steps_do_dictionary:

opus_import.steps.do_dictionary
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fills ``contexts`` and ``definitions``, which is where every tooltip in the user
interface comes from. Option: ``--import-dictionary``. Only the schema version comes
after it.
:ref:`dev_guide_dictionary` describes the two tables and where their content comes from.

Its public functions:
:func:`~opus_import.steps.do_dictionary.fill_contexts` and
:func:`~opus_import.steps.do_dictionary.fill_definitions` fill ``contexts__new`` and
``definitions__new``, and :func:`~opus_import.steps.do_dictionary.do_dictionary` is the
step.

The step rebuilds the two tables as one set by swap
(:ref:`dev_guide_import_steps_table_swap`): both are filled before either is swapped in,
and one rename swaps both, so a reader never finds the dictionary missing, partly filled
or with one table new and the other old. The definitions fill also writes the mult
tooltip contexts into ``contexts__new``, which is why the two fill functions share it.

The definitions builder collects every fault before writing anything; the contexts
builder stops at the first malformed line. Either way nothing is written and the live
tables keep what the previous run wrote. A failed dictionary import is logged,
keeps the invocation from marking the schema ready, and makes it exit with failure, as a
validation failure does (:ref:`dev_guide_import_steps_do_validate`).

.. _dev_guide_import_steps_do_schema_version:

opus_import.steps.do_schema_version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Marks the schema finished. Option: ``--write-schema-version``, which nothing
implies: it is the last step of every sequence that finishes a database, after the
validation. It creates the one-row ``schema_version`` table when it is absent, and then,
by what the row holds:

* **no row**: inserts :data:`~opus_import.schema_version.SCHEMA_VERSION` in the
  ``ready`` state;
* **this version,** ``appending``: changes the state to ``ready``, logged at info level;
* **this version,** ``ready``: nothing, logged at debug level;
* **another version, or more than one row**: refuses. It logs an error, leaves the
  table as it is, and the run **exits non-zero**. A schema another release imported is
  re-imported under this one, never restamped.

Before any of that, :mod:`opus_import.cli` refuses the step, with a fatal message and a
non-zero exit, while any bundle in the bundle registry is not ``done``
(:ref:`dev_guide_import_steps_registry`), and when a finishing step of the same
invocation failed, unless ``--ignore-errors``; either way the row is left as it is.

It is the only writer of ``ready``. ``--finalize``, ``--import-dictionary``
and ``--do-it-all`` leave the row alone, so a schema they finished is not served until
this step runs; an append sets it to ``appending`` and leaves it so.
``--scorched-earth`` drops the table before any other, so an erase that stops part way
leaves no version row behind.
:ref:`dev_guide_database_schema_version` describes the table and who reads it.

The internal modules
--------------------

These are the internals of :mod:`~opus_import.steps.do_import`. **They are not steps**:
no command-line option runs one on its own, and nothing outside ``do_import`` calls
them as a unit.

.. _dev_guide_import_steps_do_import_tables:

opus_import.steps.do_import_tables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Creating the ``obs_`` and mult tables, deleting from them, and dropping every table the
import creates. The mult tables are ``mult``, ``mult_field`` and ``mult_group``.

The teardown and build orders are forced by foreign keys, and both are stated here once
so no caller has to work them out:

* **Teardown** -- every ``obs_`` table except ``obs_general``, then ``cart``, then
  ``obs_general``, then the mult tables.
* **Build** -- the other way round.

The mult tables come last on teardown and first on build by the pipeline's own
convention (an ``obs_`` row holds a ``mult`` row's id), not because a constraint forces
it. Deleting a bundle leaves its ``mult`` rows in place; finalization deletes the values
no observation holds (:ref:`dev_guide_import_steps_do_finalize_mult`).

Its functions:

:func:`~opus_import.steps.do_import_tables.lookup_vol_info`
    The first ``BUNDLE_INFO`` entry whose regular expression matches the whole bundle
    id, or None.

:func:`~opus_import.steps.do_import_tables.opus_imports_bundle`
    Whether OPUS imports a bundle: False exactly when its ``BUNDLE_INFO`` entry exists
    and has no instrument class, True otherwise, a bundle with no entry included. The
    import's skip and the bundle registry both call it
    (:ref:`dev_guide_import_steps_registry`).

:func:`~opus_import.steps.do_import_tables.create_tables_for_import`
    Creates the mult tables if the schema lacks them
    (:func:`~opus_import.mult_fields.create_mult_tables`), then every table a bundle
    needs that the schema lacks. It returns the schemas it read and the table names in
    order, which is what the index importer walks.

.. _dev_guide_import_steps_scorched_earth:

:func:`~opus_import.steps.do_import_tables.delete_all_opus_tables`
    **Scorched earth**: drops every table the import creates, leaving Django's own
    (``opus_manage migrate``'s ``django_*`` and ``auth_*`` tables, ``django_session``
    among them). The tables are named by two constants, so nothing outside them is ever
    dropped, not even a table of no known name:
    :data:`~opus_import.steps.do_import_tables.OPUS_TABLE_PREFIXES` (``obs_``, which
    catches every observation table however many there are, and ``mult_``, which
    catches ``mult_field`` and ``mult_group``) and
    :data:`~opus_import.steps.do_import_tables.OPUS_TABLE_NAMES`, the other tables by
    exact name -- ``schema_version``, ``mult``, ``cart``, ``import_bundle``, the auxiliary
    tables, the dictionary's, ``user_searches``, ``search_results``, and the ``__new``
    and ``__old`` tables
    an interrupted swap can leave (:ref:`dev_guide_import_steps_table_swap`). A step that
    creates a table outside the prefixes adds its name there. The drop order is the one
    the foreign keys allow: ``schema_version`` first, so an erase that stops part way
    leaves a schema nothing serves or promotes; every ``obs_`` table but
    ``obs_general``; ``cart``; ``obs_general``; ``definitions`` and its swap tables,
    which reference ``contexts``; every other exact name but ``mult``; and ``mult``,
    then every ``mult_`` table, last.

:func:`~opus_import.steps.do_import_tables.delete_bundle_from_obs_tables`
    Deletes one bundle from every observation table, every other table before
    ``obs_general``, in chunks. First every other table loses its rows in the bundle's
    registered id range above the highest ``obs_general`` id in that range: rows of
    observations whose ``obs_general`` rows were never loaded, which a run that stopped
    partway through an index leaves, since each table is loaded once a transaction's
    worth of its rows wait; the bundle's ids, handed out again from the start of its
    range, would otherwise collide with them. No other bundle's rows lie in the range,
    so an importer loading another bundle at the same time loses nothing. Then the bundle's ``obs_general`` ids are read
    ``[import] transaction_rows`` at a time through ``obs_general``'s ``bundle_id`` key,
    and for each chunk every other table's rows of those observations go in one
    statement per table that joins ``obs_general`` on ``obs_general_id``
    (:meth:`~opus_import.importdb.super.ImportDBSuper.delete_joined_rows`), selecting
    by the bundle and the chunk's range of ids -- for ``obs_files``, every file of each
    observation, and for ``obs_surface_geometry_target``, every body's row of each,
    through the key on ``obs_general_id`` it is created with -- followed by the chunk's
    ``obs_general`` rows. Each statement is its
    own transaction, so none holds a whole large bundle's undo, and none reads rows
    outside its range -- which matters on a fresh import, whose tables have no other
    key to find a bundle's rows by until finalization. The connection checks foreign
    keys while it deletes, so ``cart``'s cascade removes the
    cart rows that name the bundle's observations.

:func:`~opus_import.steps.do_import_tables.analyze_all_tables`
    Runs the backend's analyze over every ``obs_`` table and the mult tables, for
    ``--analyze-tables``, which :mod:`opus_import.cli` runs after the auxiliary, cart
    and search tables. ``cart`` and the auxiliary tables are not analyzed; each auxiliary
    table is analyzed by its swap.

.. _dev_guide_import_steps_do_import_index:

opus_import.steps.do_import_index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Importing every observation one primary index file describes.
:ref:`dev_guide_import_one_index` walks it; this section names its parts.

:func:`~opus_import.steps.do_import_index.import_one_index`
    The whole of it: read the primary index, resolve ambiguous rows, discover and
    cross-reference the associated metadata files, compute every row through
    :func:`~opus_import.steps.do_import_pool.compute_index`, then load what is left of
    the ``obs_`` rows. Each ``mult`` row the index adds is inserted as its value is met,
    by :func:`~opus_import.steps.do_import_mult.update_mult_table`, during the serial
    computation or a pool's replay, so it is written before any ``obs_`` row that holds
    its id. It returns False, abandoning the index, when a pool worker failed; the
    index's ``obs_`` rows are then deleted, and the ``mult`` rows it added stay, for
    finalization to delete those no observation holds.

:class:`~opus_import.steps.do_import_index.IndexState`
    What every row of the index is computed from, built once the metadata is assembled
    and the tables are created: the obs instance, the metadata dictionary it reads, a
    copy of that dictionary as it stands before the first row
    (:attr:`~opus_import.steps.do_import_index.IndexState.base_metadata`), the table
    schemas and their order, the PDS version, and the index rows. A pool's workers inherit
    it by ``fork``.

:func:`~opus_import.steps.do_import_index.import_index_row`
    Computes every table's rows for one index row and hands each to a row emitter, in the
    order the tables are walked. **It first clears the metadata dictionary and refills it
    from** ``base_metadata``, so what a row computes depends on that row alone and not on
    the rows computed before it in the same process -- which is what lets any process
    compute any row. It is the one row function, run by the serial loop and by every pool
    worker alike.

:class:`~opus_import.steps.do_import_index.TableRowSink`
    Where the import's own process sends each finished row, by table. A table's rows are
    loaded as soon as ``[import] transaction_rows`` of them are waiting
    (:meth:`~opus_import.importdb.super.ImportDBSuper.bulk_load_rows`), so the import
    holds at most that many rows of a table at once rather than a whole index's. A
    surface geometry row arrives under its body's category and waits with
    ``obs_surface_geometry_target``'s rows
    (:func:`~opus_import.surface_geometry.physical_table`).
    :meth:`~opus_import.steps.do_import_index.TableRowSink.finish` loads what is still
    waiting, table by table in the order walked. Tables therefore load in no fixed order relative to one
    another during the index, which the foreign keys tolerate because a bundle loads with
    their checks off (:ref:`dev_guide_import_steps_do_import`). An index that fails
    partway is taken back by
    :meth:`~opus_import.steps.do_import_index.TableRowSink.discard`, which deletes every
    table's rows from the first one the sink loaded to the end of the bundle's range: by
    ``id`` in ``obs_general``, which numbers its own rows, and by ``obs_general_id`` in
    every other table, with ``obs_general`` after the tables whose rows refer to it. Ids
    are handed out in ascending order from the bundle's own range, which no other
    process writes, so those are exactly the index's rows, and a failed index leaves
    none. The mult values it added stay, and finalization deletes those no observation
    holds.

:func:`~opus_import.steps.do_import_index.get_opus_products_rows_for_filespec`
    The ``obs_files`` rows for one observation: one row per file of one product type at
    one version, carrying where it lives, how big it is, its checksum, and the ordering
    the results page shows the product types in. It leaves out two kinds of file -- a
    shared index or summary file that does not list this observation, and a PDS3 file
    whose shelf metadata is missing (with a warning, because its size and checksum are
    unknown). A file that is not the current version is never checked by default. Each
    row's ``file_number`` is its position in the list, from 1, which with the
    observation's id is the table's primary key and keeps the observation's files in
    that order.

.. _dev_guide_import_steps_do_import_pool:

opus_import.steps.do_import_pool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computing an index's rows in a pool of forked processes. **Many processes compute, one
writes**: the workers compute, and only the import's own process touches the database
or the log.

:func:`~opus_import.steps.do_import_pool.compute_index` is the entry point. With
:attr:`~opus_import.context.ImportContext.workers` at 1, or an index of fewer rows than
:attr:`~opus_import.context.ImportContext.worker_rows`, it runs the row function over
every row in the import's own process, handing each row straight to the sink. A platform
without the ``fork`` start method computes the same way, and says so on an info line.
Otherwise it computes in a pool:

* **The pool is created once per index**, after the index's metadata is assembled and its
  tables are created, with the ``fork`` start method named explicitly. The state the
  rows are computed from is installed in a module global before the pool exists, so the
  workers inherit it -- the context, the
  :class:`~opus_import.steps.do_import_index.IndexState`, the row function -- and nothing
  is pickled to a worker but a task: a ``(start, end)`` range of row numbers,
  ``worker_rows`` long.
* **Each worker runs the same row function** as the serial loop, over its range, with a
  :class:`~opus_import.deferred.Capture` installed on its context
  (:attr:`~opus_import.context.ImportContext.capture`). Everywhere the code would ask
  the database for something or write a message, it records an event on the capture
  instead, each event carrying the index row number and primary file specification the
  worker was at (:mod:`opus_import.deferred`):

  - a new row id (:func:`~opus_import.import_util.next_table_id`) is a
    :class:`~opus_import.deferred.LocalId`, numbered from zero per table within the task;
  - a mult column's value (:func:`~opus_import.steps.do_import_mult.update_mult_table`) is
    recorded with its arguments and stands in the row as a
    :class:`~opus_import.deferred.MultRef`;
  - a ``mult_list`` column holding either is a :class:`~opus_import.deferred.DeferredJson`,
    the list before it is turned into JSON;
  - a computed row, an :class:`~opus_import.context.ImportLog` call, a Python warning,
    and a call of a ``pdsfile`` class's own logger are each recorded as they happen.

  A placeholder is not validated in
  :func:`~opus_import.steps.do_import_obs.import_observation_table`; an id has nothing to
  check.
* **The import's process takes results in index order**, keeping a bounded number of
  tasks queued ahead of the one it is replaying
  (:data:`~opus_import.steps.do_import_pool.TASKS_AHEAD_PER_WORKER` per worker), and
  **replays each task's events where the serial loop would have made them**. A
  replay takes a block of ``obs_general`` ids from the bundle's range
  (:attr:`~opus_import.context.ImportContext.bundle_ids`), one for each id the task
  numbered, and a zero-based :class:`~opus_import.deferred.LocalId` becomes the block's
  first id plus its number; each recorded mult value goes through
  :func:`~opus_import.steps.do_import_mult.update_mult_table` in the serial order, so it
  gets the id the serial loop gives it; each log call is made on ``ctx.log`` with the
  recorded position, so the non-repeating variants deduplicate in the import's process
  exactly as they do serially; each Python warning is issued again with its class and
  location, against the registry of the module it came from, so the import's process's
  own filters decide whether it is shown -- a warning shown once per location is shown
  once however many workers met it -- and ``pdsfile`` calls go to the real logger. Each row then goes to the sink with every value final. **The
  tables, their ids, the mult ids and the log are therefore the same whatever the
  number of workers.**
* **A worker's failure abandons the index**: the import's process logs an error naming
  the range of rows and the index file, replays nothing after it, and
  :func:`~opus_import.steps.do_import_index.import_one_index` returns False. It first
  deletes the rows the sink had already loaded
  (:meth:`~opus_import.steps.do_import_index.TableRowSink.discard`), so none of the
  index's ``obs_`` rows stays; the ``mult`` rows it added stay, for finalization to delete
  those no observation holds.

**What a worker does with what it inherited.** A worker exits by ``os._exit``, so nothing
it inherited is ever closed or flushed on its way out, and its initializer is the only
place it deals with it:

* every database connection the import's process had open is let go of without a byte
  sent on it (:func:`~opus_import.importdb.super.close_inherited_connections`): every
  :class:`~opus_import.importdb.super.ImportDBSuper` instance registers itself when
  created, and the worker closes each one's socket descriptor with :func:`os.close`,
  which leaves the import's session untouched, then keeps the instance referenced for the
  rest of its life, so the driver's destructor never sends its quit message on a
  descriptor number the worker may since have reused. The worker's context has no
  database at all;
* on Linux it asks the kernel (``prctl(PR_SET_PDEATHSIG, SIGKILL)``) to kill it when the
  import's process dies, and exits at once if that process died before the request.
  Elsewhere a worker outlives a killed import's process; a worker that kept an inherited
  socket open would keep the import's session alive after it, which is what closing them
  prevents;
* Python warnings and the ``pdsfile`` classes' loggers are redirected onto the task's
  capture, since the worker shares the import's log files.

**Test-only faults.** Under ``OPUS_IMPORT_FAULT=stall_worker:<seconds>`` every task
first sleeps for that many seconds, so a test can find the pool's workers alive; under
``OPUS_IMPORT_FAULT=fail_worker:<row>`` the task holding that index row, numbered from
zero, fails (:ref:`the import's fault sites <dev_guide_testing_faults>`).

.. _dev_guide_import_steps_do_import_obs:

opus_import.steps.do_import_obs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Computing one row of one observation table. :ref:`dev_guide_import_one_row` walks the
dispatch and the validation; the three functions are:

:func:`~opus_import.steps.do_import_obs.import_observation_table`
    Walks a table's schema, obtains each column's value, checks it, replaces an
    enumerated value with the id of its ``mult`` row, and assembles the row. It returns
    None only when a group column's field method returned something that is not a mult
    specification, which is not recoverable -- the whole observation is discarded.

:func:`~opus_import.steps.do_import_obs.field_function_name`
    The naming rule of :ref:`dev_guide_import_one_row`. The tests resolve the hierarchy
    against the schemas *through this function* rather than restating the rule, so
    changing it here changes what they check.

:func:`~opus_import.steps.do_import_obs.import_run_field_function`
    Calls the method and turns a missing method or an exception into a logged error and
    a None value.

.. _dev_guide_import_steps_do_import_mult:

opus_import.steps.do_import_mult
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reading, caching and writing the ``mult`` rows that hold the enumerated values of the
``obs_`` columns (:ref:`dev_guide_database_schema_mult`). Its public functions:
:func:`~opus_import.steps.do_import_mult.read_mult_field` reads one mult field into the
run's cache, :func:`~opus_import.steps.do_import_mult.mult_table_lookup_id` finds an
existing value's id without adding one,
:func:`~opus_import.steps.do_import_mult.update_mult_table` finds or adds a value and
returns the id an ``obs_`` column stores, and
:func:`~opus_import.steps.do_import_mult.register_pinned_fields` writes the pinned
fields' rows for bundle registration.

**Naming.** :func:`~opus_import.import_util.mult_field_name` gives a column's field
name: the column's ``mult_field`` key when it has one, otherwise ``<table>.<column>`` in
lower case -- ``obs_general.planet_id``. :mod:`opus_import.mult_fields` holds the
field ids: :func:`~opus_import.mult_fields.ensure_mult_fields`, which bundle
registration runs, creates the mult tables if the schema lacks them and gives every
field ``mult_field`` lacks the next id; an import reads them
(:func:`~opus_import.mult_fields.read_mult_fields`); and
:func:`~opus_import.mult_fields.packaged_mult_columns` lists the columns of the packaged
``obs_*.json`` schemas that hold mult ids. A column holds mult ids when its
``pi_form_type`` is a group type and it is not marked ``put_mults_here``
(:func:`~opus_import.mult_fields.is_mult_column`).

**Caching.** Every field is read once per bundle into the context's cache, so importing
an index of a hundred thousand rows does not query for the same value a hundred thousand
times. No value is deleted or given another id before finalization, so a value the cache
holds is always right, even while other importers add values to the field. The cache
lives in the import's own process: in a pool worker,
:func:`~opus_import.steps.do_import_mult.update_mult_table` reads and changes nothing,
and records its arguments for the import's process to resolve
(:ref:`dev_guide_import_steps_do_import_pool`). Two context fields track it:

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Context field
     - Lifetime and meaning
   * - :attr:`~opus_import.context.ImportContext.mult_fields`
     - Every field's ``mult_field`` row, keyed by qualified name, read once a run.
   * - :attr:`~opus_import.context.ImportContext.mult_table_cache`
     - Each field read during this bundle, keyed by qualified name, as a
       :class:`~opus_import.steps.do_import_mult.MultFieldCache`. The returned cache
       *is* the cache: adding to it is how a value is added. Cleared per bundle.

**Reading a field.** A field's rows are read from ``mult`` and its groups from
``mult_group``, so a bundle sees every value the bundles before it added, on a fresh
import and an append alike; a field with no rows yet starts the cache empty, and the
import fills it as it meets values.

**A pinned field's rows are registration's.** For a column that pins its values with
``mult_options``, bundle registration lays the list over the stored rows
(:func:`~opus_import.steps.do_import_mult.lay_options_over`;
:func:`~opus_import.import_util.read_mult_option` reads each entry): an entry whose id
is stored with the same value relabels that row, an entry neither of whose id or value
is stored is a new row, and an entry whose id is stored under another value, or whose
value is stored under another id, is an error, logged once a run, that leaves the stored
row as it is. It writes the rows and groups that changes, and sets the field's
``last_id`` to the highest id it holds. No import writes a pinned field's rows, except
the absent value below.

**Keying and id assignment.** A field's cache finds a value through a dictionary keyed
by :func:`~opus_support.collation.collation_key`, the form of the value the server's
collation compares, so a value the unique key ``(field_id, value)`` would call a
duplicate finds the row already there, and a lookup costs the same however many values
the field holds. The key is not the collation in full, so a value the dictionary does
not find is asked of the server (``SELECT ... WHERE field_id = %s AND value = %s``,
compared by the server's own collation) before it is given an id, and the server's row
is kept in the cache under the value's key.
A value is stored as a string, and an absent value (None) as the empty string. A value
the field lacks takes the next id of the field's counter, ``mult_field.last_id``, which
holds the highest id handed out in the field, or -1 before the first, so a field's first
value is 0. The id is taken in a short transaction of its own
(:meth:`~opus_import.importdb.super.ImportDBSuper.increment_counter`, run again on a
deadlock), which locks the counter's row for one statement and reads no ``MAX``. A
value that would need an id above
:data:`~opus_import.steps.do_import_mult.MAX_MULT_ID` (the largest ``smallint
unsigned``) raises :exc:`~opus_import.steps.do_import_mult.MultIdOverflowError`, whose
message names the field.

**A value the field already holds** keeps its stored row. In an unpinned field, when
the incoming label, display, pin, grouping or group pin differs from the stored one and
the column's ``mult_overrides`` does not name the value, the stored row stays and a
warning, logged once a run, names the field, the value and both presentations, and
points at ``mult_overrides`` as the way to change the stored presentation.

**A value outside a pinned list** is an error, logged once a run, which fails the
bundle. The row is given the id of the field's absent value, so a run with
``--ignore-errors`` carries on. A list with no absent value has one added, labeled
``N/A``, under :data:`~opus_import.steps.do_import_mult.PINNED_ABSENT_ID`, the largest
id, which no ``mult_options`` entry may give; so a value a later release adds to the list
never lands on it, and finalization deletes it once no observation holds it.

**No order is computed here.** The import stores each value's ``pin`` as the obs class
or the schema gives it, and finalization ranks every field
(:ref:`dev_guide_import_steps_do_finalize_mult`).

**Writing.** A new value is written the moment it is met, in a second short transaction
that also writes its group when the field lacks it, by an insert that leaves a group
another importer wrote first as it is; the transaction is run again on a deadlock or a
lock wait timeout, and a value is never stored without its group. A new row is inserted,
never upserted. When the insert meets the field's
unique key on ``(field_id, value)``, another importer stored the value first, since the
server was asked for it just before: its row is read back and its id used, and the id
taken is left unused, a gap in the field's ids that nothing depends on. With one importer
no id is left unused, so a field's ids are those the serial import gives. Any other
failure stops the import with a fatal message naming the field, the value and the id.
Nothing here touches a row's ``disp_rank``. A bundle that is deleted leaves its values
in ``mult``, where an observation of another bundle may hold them too; finalization
deletes the ones no observation holds.

API reference
-------------

:doc:`api_opus_import`

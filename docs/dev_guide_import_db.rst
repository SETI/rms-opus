.. _dev_guide_import_db:

The Import Database Layer and Shared Helpers
============================================

Two modules sit underneath every step. :mod:`opus_import.importdb` is the only way the
pipeline talks to a database, and :mod:`opus_import.import_util` is where the helpers
the steps and the obs classes share live.

.. _dev_guide_import_db_importdb:

opus_import.importdb
--------------------

One module per database brand, behind one abstract interface.
:func:`opus_import.importdb.get_db` is the only way the pipeline opens a database: it
dispatches on the brand named in the configuration and returns an
:class:`~opus_import.importdb.super.ImportDBSuper`, **so no step module names a brand**.
MySQL is the only brand implemented.

The package's whole public surface is two names: :func:`~opus_import.importdb.get_db`
and :exc:`~opus_import.importdb.super.ImportDBError`, the one exception the layer
raises. A failed database operation always aborts the import.

.. mermaid::

    classDiagram
        class ImportDBSuper {
            <<abstract>>
            +conn
            +log_sql
            +tables_created
            +convert_raw_to_namespace()
            +convert_namespace_to_raw()
            +table_exists()
            +read_rows()
            +quote_identifier()*
            +table_names()*
            +table_info()*
            +create_table()*
            +drop_table()*
            +analyze_table()*
            +insert_row()*
            +insert_rows()*
            +update_row()*
            +upsert_row()*
            +upsert_rows()*
            +delete_rows()*
            +copy_rows_between_namespaces()*
            +general_select()*
            +find_column_max()*
            #_execute()
            #_execute_and_fetchall()*
            #_enter()
            #_exit()
        }
        class ImportDBMySQL {
            +default_engine
            +mysql_version
            implements every abstract member
        }
        class ImportDBPostgreSQL {
            <<abstract>>
            a stub: inherits every
            NotImplementedError unchanged
        }
        class ImportDBError {
            Exception
        }

        ImportDBSuper <|-- ImportDBMySQL
        ImportDBSuper <|-- ImportDBPostgreSQL
        ImportDBMySQL ..> ImportDBError : raises

Namespaces
~~~~~~~~~~

The layer is where the import/permanent split of
:ref:`dev_guide_import_two_namespaces` is implemented. A ``Namespace`` is one of
``'import'``, ``'perm'`` or ``'all'``, and **every** method takes one plus a *raw* table
name.

:meth:`~opus_import.importdb.super.ImportDBSuper.convert_raw_to_namespace` prepends the
configured prefix for ``'import'`` and returns the name unchanged for ``'perm'`` and
``'all'``; with no prefix configured, the two namespaces are literally the same tables.
:meth:`~opus_import.importdb.super.ImportDBSuper.convert_namespace_to_raw` is the
inverse. ``'all'`` is accepted only where reading both makes sense.
:func:`~opus_import.steps.do_django.drop_cache_tables` is the only step that uses it; the
MySQL constructor also passes it when priming its table-name cache.

Because every method converts the name itself, **no step module ever builds a prefixed
name**. That is the property to preserve when adding one.

The abstract contract
~~~~~~~~~~~~~~~~~~~~~

:class:`~opus_import.importdb.super.ImportDBSuper` declares 27 members. Eleven are
implemented in the base class because they are the same for any brand; the other sixteen
raise :exc:`NotImplementedError` and are what a brand supplies. Like the obs hierarchy,
this is an abstract class by convention rather than through :mod:`abc`.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Abstract member
     - Contract
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.quote_identifier`\ ``(s)``
     - Return a name quoted for use as an identifier.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.table_names`\ ``(namespace, prefix=None)``
     - The tables in a namespace, optionally filtered by one prefix or several. **An
       implementation must sort them**, because a caller handing out row ids while
       iterating this would otherwise produce a different database on a different
       machine.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.table_info`\ ``(namespace, raw_table_name)``
     - The table's columns as the database currently defines them, in the same shape a
       packaged schema has.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.create_table`\ ``(namespace, raw_table_name, schema, ignore_if_exists=True)``
     - Create a table from an OPUS table schema. Returns True if it created one, False
       if it was already there.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.drop_table`\ ``(namespace, raw_table_name, ignore_if_not_exists=True)``
     - Delete a table.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.analyze_table`\ ``(namespace, raw_table_name)``
     - Recompute the table's key distribution statistics.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.insert_row` / :meth:`~opus_import.importdb.super.ImportDBSuper.insert_rows`
     - Insert one row, or many.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.update_row`\ ``(namespace, raw_table_name, row, where, where_params=None)``
     - Assign new values to the rows a WHERE clause selects.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.upsert_row` / :meth:`~opus_import.importdb.super.ImportDBSuper.upsert_rows`
     - Insert, updating any row whose key is already present. The key column is written
       on an insert and never assigned on an update.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.delete_rows`\ ``(namespace, raw_table_name, where=None, where_params=None)``
     - Delete the rows a WHERE clause selects.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.copy_rows_between_namespaces`\ ``(src, dest, raw_table_name, where=None, where_params=None)``
     - Copy one table's rows from one namespace to the same table in another. Both
       tables must have the same columns in the same order, which they do because both
       are created from the same OPUS table schema.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.general_select`\ ``(cmd, param_list=None)``
     - Run a query the caller assembled and return every row.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.find_column_max`\ ``(namespace, raw_table_name, column_name)``
     - The largest value in a column.
   * - ``_execute_and_fetchall(cmd, func_name, param_list=None)``
     - Execute one query and return every row of its result.

The eleven concrete members are the constructor, the two namespace converters and
their two predicates, :meth:`~opus_import.importdb.super.ImportDBSuper.table_exists`, :meth:`~opus_import.importdb.super.ImportDBSuper.read_rows`, ``_execute``, the warning
collector ``_make_warning_handler``, and the ``_enter``/``_exit`` pair. The two
converters do carry a ``raise NotImplementedError`` for a namespace value that is not
one of the three, which is unreachable for a valid one.

Read-only runs
~~~~~~~~~~~~~~

``--read-only`` sets a flag on the connection, and every mutating call passes
``mutates=True`` down to ``_execute``. A read-only run therefore **still executes
non-mutating statements** -- it really reads the database -- and logs each mutating one
with a ``[SIM]`` marker instead of running it. Log messages branch on the flag too, so a
dropped table reads as ``[SIM] Dropped table`` rather than ``Dropped table``.

Warnings
~~~~~~~~

``_enter`` and ``_exit`` bracket every database operation. At the outermost one,
``_enter`` clears the record of executed statements and installs a handler that collects
Python warnings; ``_exit`` reports any warnings together with the statements that
produced them, so a warning read out of a log names the SQL that caused it. Nesting is
tracked, so an inner operation does not clear an outer one's record.

MySQL: ImportDBMySQL
~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.importdb.mysql.ImportDBMySQL`

The one implemented brand. It renders the OPUS table schemas as MySQL DDL and builds the
statements that read and write rows. Four things about it are worth knowing before
changing anything.

**Identifiers are validated, then quoted.** Every table, column and alias is matched
against ``[A-Za-z0-9_]+`` before it is wrapped in backticks. Backticks quote an
identifier but do **not** escape a backtick inside one, so validating the name is what
keeps a computed identifier from ending the quoting early. Every identifier OPUS uses --
from the schemas, from the configuration, from a bundle id -- fits that shape.

**Values are always parameters**, including None, which the driver renders as SQL NULL.
The DDL is the one exception: a column's default and its enum option list are formatted
straight into the ``CREATE TABLE``, which is safe only because both come from the table
schemas packaged with :mod:`opus_import` and never from input. Three statement builders
here interpolate a caller's ``where`` fragment and carry an explicit note saying so, and a
fourth does in the base class; each is for trusted callers, and only the values inside
such a fragment are bound.

**The upsert needs MySQL 8.0.19.** ``ON DUPLICATE KEY UPDATE`` has to name each row's
new value indirectly, because one statement carries many rows, and the row alias MySQL
8.0.19 added is how: ``AS new`` names the row being inserted, so ``new.col`` is that
row's value for that column. The older ``VALUES(col)`` spelling is deprecated as of
8.0.20. **This is what puts the server floor at 8.0.19**, which the README and
:ref:`dev_guide_installation` both state. Two details guard the edges: MySQL requires the
alias to differ from the table name, so a table called ``new`` gets the alias
``new_row`` instead (compared without regard to case, because MySQL folds identifiers
for this check); and the alias is emitted only alongside the clause that reads it,
because a row of nothing but the key has nothing to assign.

Both :meth:`~opus_import.importdb.super.ImportDBSuper.insert_rows` and :meth:`~opus_import.importdb.super.ImportDBSuper.upsert_rows` write in packets of 1000 rows.

**Connecting.** The constructor connects without naming a database and then issues
``USE``; an unknown-database error makes it **create the schema** and retry, which is
why an import into a new schema needs no ``CREATE DATABASE`` first. It then primes a
cache of every table name, reads the server version, and sets a strict SQL mode --
failing the run if it cannot. It does **not** close the connection: there is no close
method, no destructor and no context manager, and each statement is run through its own
cursor and committed immediately.

The driver is imported defensively, so the module still imports without ``mysqlclient``
installed and a package-wide sweep -- Sphinx autodoc, or a test collection -- does not
fail on it. An instance built without the driver forces itself read-only and discards
every statement rather than running it, so it reports no tables and reads no rows. **It
is not a simulation anything can be driven through.**

The type mapping
~~~~~~~~~~~~~~~~

:meth:`~opus_import.importdb.super.ImportDBSuper.create_table` is where a schema's ``field_type`` becomes a MySQL
type, and :meth:`~opus_import.importdb.super.ImportDBSuper.table_info` is the reverse. :ref:`dev_guide_table_schemas` lists the mapping.
An unrecognized type raises :exc:`NotImplementedError` rather than being guessed at, in
both directions.

PostgreSQL: ImportDBPostgreSQL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:class:`opus_import.importdb.postgresql.ImportDBPostgreSQL`

Nothing here is implemented. The class inherits every
:exc:`NotImplementedError` stub unchanged and defines only a constructor, and
:func:`~opus_import.importdb.get_db` has no branch that returns it. The module exists so
that the brand abstraction has a second brand to point at, and so that adding one is a
matter of filling this in and adding a branch. :mod:`opus_app.settings` carries the
matching placeholder on the Django side.

.. _dev_guide_import_db_import_util:

opus_import.import_util
-----------------------

The helpers the steps and the obs classes share. Two of them hold state that outlives a
call and is deliberately never cleared: :class:`~opus_import.import_util.NoDupLogger`'s
record of what it has already said, and
:func:`~opus_import.import_util.cached_tai_from_iso`'s conversion cache.

Types
~~~~~

:data:`~opus_import.import_util.IndexRow`
    One row of a PDS index table, keyed by column name.

:data:`~opus_import.import_util.TableSchema`
    One OPUS table's definition: its columns, in schema order.

:class:`~opus_import.import_util.MultOption`
    One entry of a column's ``mult_options`` list, as a named tuple rather than a
    positional one. Building one from the JSON list makes a wrong-length entry raise
    :exc:`TypeError` at the point of construction rather than being mis-assigned later.
    The ``aliases`` column is deliberately absent, because no schema pins one.

Bundle expansion and PDS table reading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~opus_import.import_util.yield_import_bundle_ids`
    Expands the command line's bundle descriptors into concrete bundle ids in import
    order: ids, bundleset names, and the mission and instrument shorthands. Every
    descriptor is validated as a PDS3 path and then as a PDS4 one, and every bad one is
    logged before the run exits, so one invocation reports all of them. A New Horizons
    bundleset yields its calibrated bundle before its raw one; see
    :ref:`dev_guide_import_obs_classes` for what that is for and why it changes nothing
    today. Anything named by ``--exclude-bundles``, and
    any name containing a dot, is dropped.

:func:`~opus_import.import_util.safe_pdstable_read`
    Reads a PDS index table. For PDS3 it delegates to
    :func:`~opus_import.import_util.safe_pdstable_read_pds3`; for PDS4 it reads the file
    as a bare CSV, because the PDS4 index files OPUS reads carry no label, and infers
    each column's type by trying the whole column as integers, then as floats, then as
    stripped strings.

:func:`~opus_import.import_util.safe_pdstable_read_pds3`
    Reads a PDS3 label and table through ``pdstable``, applying whichever
    :data:`~opus_import.instruments.PDSTABLE_REPLACEMENTS` entry matches the file name.
    A :exc:`KeyboardInterrupt` is re-raised; any other exception is logged and returns
    a pair of Nones. A read that produced Python warnings is treated as a failure.

:func:`~opus_import.import_util.safe_column`
    Reads a value from a ``pdstable`` column honoring the companion mask column, which
    is how a PDS "missing" value becomes None. An absent column is None too. With no
    index, a column any of whose mask elements is set reads as None entirely.

:func:`~opus_import.import_util.log_accumulated_warnings`
    Reports the Python warnings collected on the context since the last report, replaces
    the list with a fresh one, and marks the run as having produced bad data.

Table names
~~~~~~~~~~~

:func:`~opus_import.import_util.table_name_obs_mission` and :func:`~opus_import.import_util.table_name_obs_instrument`
    ``obs_mission_<suffix>`` and ``obs_instrument_<id>``, both lowercased. Each asserts
    that the id is in the corresponding :mod:`opus_import.config_data` map, so a typo
    fails immediately rather than producing a table nobody fills.

:func:`~opus_import.import_util.table_name_mult`
    ``mult_<table>_<column>``, both lowercased.

:func:`~opus_import.import_util.table_name_param_info` and :func:`~opus_import.import_util.table_name_partables`
    The two auxiliary tables' names, which are constants rather than computed. They exist
    so that no step spells either name itself.

:func:`~opus_import.import_util.encode_target_name` and :func:`~opus_import.import_util.decode_target_name`
    A target name is not a legal SQL identifier, so it is encoded: lowercased, with
    ``/`` becoming three underscores and a space becoming four. The decoder reverses the
    two underscore runs -- **but not the lowercasing**, which is why the display label
    is title-cased afterwards.

:func:`~opus_import.import_util.table_name_for_sfc_target` and :func:`~opus_import.import_util.slug_name_for_sfc_target`
    The two forms a surface geometry target takes: the table-name suffix, and the slug
    the web application's search parameters embed. The slug form has a warning attached
    -- changing it means changing ``getSurfacegeoTargetSlug`` in the front end's
    ``utils.js`` too.

Schemas
~~~~~~~

``TABLE_SCHEMA_DIR`` and ``DICTIONARY_DATA_DIR``
    The two packaged data directories, as :mod:`importlib.resources` traversables. Every
    read of a table schema or of the context tree goes through one of them, which is what
    lets an installed OPUS find them without a checkout.

:func:`~opus_import.import_util.table_schema_files`
    The packaged ``table_schemas`` entries whose file name matches a glob, **sorted by
    name**, so that an import run's order does not depend on the file system's directory
    order. They come back as :mod:`importlib.resources` traversables, not paths, which
    is what lets an installed OPUS find them without a checkout.

:func:`~opus_import.import_util.read_schema_for_table`
    Reads and parses one schema, stripping the import prefix from the name first. It is
    the only place the ``<TARGET>``/``<SLUGTARGET>`` substitution happens, and the
    substitution is plain text applied before the JSON is parsed. A name with no schema
    file returns None, which is how a bundle ends up with only the tables its instrument
    has columns in.

:func:`~opus_import.import_util.find_max_table_id`
    The larger of the maximum ``id`` in the two namespaces, or -1 when the table exists
    in neither or is empty in both. **Both** namespaces, which is what makes a
    re-import hand out ids above everything already present.

Logging
~~~~~~~

:class:`~opus_import.import_util.NoDupLogger`
    A ``pdslogger`` wrapper that logs each message once. It exists for ``rms-pdsfile``'s
    own warnings, of which an import produces hundreds of thousands. The record of what
    has been said is a **class-level set shared by every instance and never cleared**, so
    a message is logged once per process; it is a set rather than a list because it
    never shrinks and is searched on every call.

:func:`~opus_import.import_util.log_error`, :func:`~opus_import.import_util.log_warning`, :func:`~opus_import.import_util.log_info`, :func:`~opus_import.import_util.log_debug`
    The step modules' spelling of the four levels. Each delegates to the matching
    :class:`~opus_import.context.ImportLog` method, so both spellings are one
    implementation. ``log_error`` is the one that marks the run as having produced bad
    data.

:func:`~opus_import.import_util.log_nonrepeating_error` and :func:`~opus_import.import_util.log_nonrepeating_warning`
    Logged the first time this run produces the message and ignored after that. Neither
    takes formatting arguments, unlike the four above.

:func:`~opus_import.import_util.log_unknown_target_name`
    Reports a ``TARGET_NAME`` the target tables do not describe, naming the file to
    edit.

Miscellaneous
~~~~~~~~~~~~~

:func:`~opus_import.import_util.cached_tai_from_iso`
    An ISO time as seconds past the J2000 epoch, TAI. An index row's times repeat across
    the rows of one observation, so the last 64 conversions are kept.

:func:`~opus_import.import_util.safe_join`
    :func:`os.path.join` with backslashes normalized to forward slashes. PDS file
    specifications are compared as text throughout the pipeline and on the web side, so
    a Windows backslash in one would not match the same path built anywhere else.

API reference
-------------

:doc:`api_opus_import`

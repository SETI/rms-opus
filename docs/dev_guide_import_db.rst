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

The package's whole public surface is :func:`~opus_import.importdb.get_db`,
:func:`~opus_import.importdb.lock_name`, which names a server-wide lock belonging to one
schema (:meth:`~opus_import.importdb.super.ImportDBSuper.named_lock`), and
:exc:`~opus_import.importdb.super.ImportDBError`, the exception the layer raises. Its
subclass, :exc:`~opus_import.importdb.super.RollbackError`, is a failed transaction whose
rollback failed too. A failed database operation always aborts the import, except the
ones :ref:`dev_guide_import_db_transactions` describes as run again or handled by their
caller.

.. mermaid::
    :zoom:

    classDiagram
        class ImportDBSuper {
            <<abstract>>
            +conn
            +log_sql
            +bulk_load
            +scratch_dir
            +transaction_rows
            +tables_created
            +JOINED_PARENT_ALIAS
            +table_exists()
            +read_rows()
            +transaction()
            +retrying()
            +failures_expected()
            +open_sibling_connection()
            +build_indexes()
            +foreign_keys_unchecked()
            +quote_identifier()*
            +table_names()*
            +forget_table_names()*
            +table_info()*
            +create_table()*
            +drop_table()*
            +rename_tables_atomically()*
            +analyze_table()*
            +insert_row()*
            +insert_rows()*
            +bulk_load_rows()*
            +update_row()*
            +conditional_update()*
            +upsert_row()*
            +upsert_rows()*
            +delete_rows()*
            +delete_joined_rows()*
            +general_select()*
            +stream_select()*
            +find_column_max()*
            +read_table_keys()*
            +add_keys_statement()*
            +add_fulltext_key_statement()*
            +read_ngram_token_size()*
            +add_foreign_key_statement()*
            +add_foreign_keys()*
            +key_space_bytes()*
            +index_space_budget()*
            +run_ddl()*
            +close()*
            +socket_descriptor()*
            +named_lock()*
            +increment_counter()*
            +lock_first_row()*
            +insert_rows_keeping_existing()*
            +is_retryable_error()*
            +is_duplicate_key_error()*
            #_prepare_index_session()*
            #_size_index_sort()*
            #_set_foreign_key_checks()*
            #_execute()
            #_execute_and_fetchall()*
            #_operation()
            #_enter()
            #_exit()
        }
        class ImportDBMySQL {
            +default_engine
            +mysql_version
            +bulk_load_path
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
        class RollbackError {
            ImportDBError
        }

        ImportDBSuper <|-- ImportDBMySQL
        ImportDBSuper <|-- ImportDBPostgreSQL
        ImportDBError <|-- RollbackError
        ImportDBMySQL ..> ImportDBError : raises

.. _dev_guide_import_db_foreign_key_checks:

Table names and foreign key checks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every method takes a table's name as the schema holds it. There is one set of tables,
the one the web application reads, whichever write path an import takes
(:ref:`dev_guide_import_write_paths`), so no method adds a prefix or any other qualifier
to a name, and neither does any step.

:meth:`~opus_import.importdb.super.ImportDBSuper.foreign_keys_unchecked` is a context
manager that turns the connection's foreign key checks off while its body runs and back
on however the body ends. The brand supplies ``_set_foreign_key_checks(enabled)``, which
the MySQL brand implements as ``SET SESSION foreign_key_checks``. With the checks off a
write is not checked against the foreign keys and **a delete cascades nothing**, so the
import turns them off for two things only: loading a bundle, whose orphans validation
counts instead (:ref:`dev_guide_import_steps_do_validate`), and adding foreign keys in
finalization, which is then an in-place change that does not read the rows already there
(:meth:`~opus_import.importdb.super.ImportDBSuper.add_foreign_keys`). Every delete -- a
bundle's before it is loaded, ``--delete-bundles``, the duplicate step -- runs with the
checks on, so that ``cart``'s cascading foreign key removes the cart rows it would
otherwise orphan.

.. _dev_guide_import_db_keys:

Keys on a fresh import
~~~~~~~~~~~~~~~~~~~~~~

:mod:`opus_import.table_keys` reads a schema's keys as
:class:`~opus_import.table_keys.TableKey` values -- a kind, the columns in order and,
for a foreign key, what it references and what it does on delete -- which compare by
those and never by name, because the server names an unnamed key itself.
:meth:`~opus_import.importdb.mysql.ImportDBMySQL.create_table` always creates a table
whose name begins ``obs_`` or ``mult_``
(:data:`~opus_import.table_keys.KEY_FILTERED_TABLE_PREFIXES`) with **the keep set**,
:func:`~opus_import.table_keys.create_time_keys`, exactly: the primary key, every unique
key, every ``{"constraint": ...}`` entry (rendered raw, as always), and the keys the
per-bundle delete reads: the ``bundle_id`` key of ``obs_general``, the one table it
selects by ``bundle_id`` (:func:`~opus_import.table_keys.is_bundle_keyed_table`), and in
every other observation table a plain key on ``obs_general_id`` alone where the table
declares one. Every other observation table is reached by joining ``obs_general`` on
``obs_general_id``, which leads its primary key -- or, in
``obs_surface_geometry_target``, whose primary key starts with ``target_name``, the
plain key on ``obs_general_id`` it is created with -- and ``obs_pds``'s ``bundle_id``
key waits for finalization like any other plain key. It does so on both write paths, so a table first
created by an append is keyed by the ``--finalize`` that follows, as every table of a
fresh import is. ``mult_field`` and ``mult_group`` declare only a primary key and unique
keys, so the keep set is every key they have. A table of neither kind, ``mult`` among
them, is created with every key its schema declares,
table-level ``foreign_key``, ``primary_key``, ``unique`` and ``key`` entries included
(:ref:`dev_guide_table_schemas`), which is how ``cart`` has its cascading foreign key,
and ``search_results`` its keys over two columns, from the start.

:func:`~opus_import.table_keys.add_secondary_indexes` is the complement over those
tables: the declared keys the keep set leaves out, ``FULLTEXT`` keys first, then plain
keys, and foreign keys last, plus a plain key on each foreign-key column no B-tree key
leads, so the index each foreign key needs already exists when the foreign key is added.
Finalization's ``--create-indexes`` adds what it lists
(:ref:`dev_guide_import_steps_create_indexes`). Both read the same column entries, so
the two can never disagree; a unit test checks that they partition the keys of every
schema whose name begins ``obs_`` or ``mult_``, and that the keep set holds every key
the delete reads.

.. _dev_guide_import_db_siblings:

Sibling connections and the index build
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:meth:`~opus_import.importdb.super.ImportDBSuper.open_sibling_connection` opens a second
connection to the same schema, configured as the first, **with no logger**: ``_enter`` and ``_exit`` swap the process-wide :func:`warnings.showwarning`,
which is not safe to do from several threads at once, so a sibling reports nothing and
the connection that opened it logs on its behalf.

:meth:`~opus_import.importdb.super.ImportDBSuper.build_indexes` runs statements that add
keys, each table's in order on one connection, for **different tables at once** across
up to ``workers`` siblings, one per thread, or one table at a time on the connection
itself when ``serial`` asks for it or there is one worker. Each connection is prepared
first (``_prepare_index_session``: the MySQL brand records the server's
``innodb_ddl_buffer_size``, the connection's share of the sort memory and
``innodb_ddl_threads``, and points ``innodb_tmpdir`` at ``[import] server_tmpdir`` when
that is set), and before each statement sizes its sort memory to the statement's largest
key, its share divided among the indexes the statement builds at once
(``_size_index_sort``). Under a space budget a statement waits until its estimate fits
beside the statements already running, and one larger than the whole budget is refused
before anything runs. A failed statement stops its own table; the other tables finish,
and the failures are raised together as one
:exc:`~opus_import.importdb.super.ImportDBError` once every table is done. The
parent logs each table's duration as it finishes.

The abstract contract
~~~~~~~~~~~~~~~~~~~~~

:class:`~opus_import.importdb.super.ImportDBSuper` declares the whole database interface.
Some members are implemented in the base class because they are the same for any brand;
the rest raise :exc:`NotImplementedError` and are what a brand supplies. Like the obs
hierarchy, this is an abstract class by convention rather than through :mod:`abc`.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Abstract member
     - Contract
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.quote_identifier`\ ``(s)``
     - Return a name quoted for use as an identifier.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.table_names`\ ``(prefix=None)``
     - The tables in the schema, optionally filtered by one prefix or several. **An
       implementation must sort them**, because a caller handing out row ids while
       iterating this would otherwise produce a different database on a different
       machine.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.forget_table_names`\ ``()``
     - Make the next ``table_names`` read the names from the server again, for a table
       another process may have created since a cached read.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.table_info`\ ``(table_name)``
     - The table's columns as the database currently defines them, in the same shape a
       packaged schema has.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.create_table`\ ``(table_name, schema, ignore_if_exists=True)``
     - Create a table from an OPUS table schema, with the keys
       :ref:`dev_guide_import_db_keys` describes. Returns True if it created one, False
       if it was already there.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.drop_table`\ ``(table_name, ignore_if_not_exists=True)``
     - Delete a table.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.rename_tables_atomically`\ ``(renames, *, lock_wait_timeout_s, attempts)``
     - Rename several tables in one statement that takes effect all at once, for the
       swap (:ref:`dev_guide_import_steps_table_swap`).
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.analyze_table`\ ``(table_name)``
     - Recompute the table's key distribution statistics.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.insert_row` / :meth:`~opus_import.importdb.super.ImportDBSuper.insert_rows`
     - Insert one row, or many.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.bulk_load_rows`\ ``(table_name, rows)``
     - Write many rows the fastest way the server allows, at most
       ``transaction_rows`` to a transaction, checking that every row arrived unchanged;
       or as ``insert_rows`` does where the server allows nothing faster. The
       observation rows go through it (:ref:`dev_guide_import_db_bulk_load`).
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.update_row`\ ``(table_name, row, where, where_params=None)``
     - Assign new values to the rows a WHERE clause selects.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.conditional_update`\ ``(table_name, row, where, where_params)``
     - The same, returning how many rows changed: 0 when the clause, the condition the
       change depends on, selected none, and -1 in a read-only run. Every move between
       the bundle registry's states is one.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.insert_rows_keeping_existing`\ ``(table_name, key_name, rows)``
     - Insert rows, leaving alone any whose key a stored row holds, while a value a
       column cannot hold still fails; the ``mult_group`` insert.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.increment_counter`\ ``(table_name, column, key_column, key)``
     - Add one to a counter column of one row and return the new value as this
       connection set it, locking only that row until the transaction ends; raise when
       no row has the key. A read-only run returns the stored value advanced by every
       addition the run has made (``_simulated_count``). ``mult_field.last_id`` is the
       one counter.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.lock_first_row`\ ``(table_name, column, where, where_params, order_by)``
     - Lock the first row a WHERE clause selects in descending ``order_by`` order,
       passing over rows another session has locked, and return one column of it, or
       None; the bundle claim.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.named_lock`\ ``(name)``
     - A context manager holding a server-wide named lock while its body runs, waiting
       for it first. The lock belongs to the connection, so it survives the body's
       commits; a release that fails after a failed body does not replace the body's
       exception.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.is_retryable_error`\ ``(exc)`` / :meth:`~opus_import.importdb.super.ImportDBSuper.is_duplicate_key_error`\ ``(exc)``
     - Whether a failure, the driver's error or an ``ImportDBError`` raised from one, is
       a deadlock or a lock wait that timed out; or a duplicate primary or unique key.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.upsert_row` / :meth:`~opus_import.importdb.super.ImportDBSuper.upsert_rows`
     - Insert, updating any row whose key is already present. The key column is written
       on an insert and never assigned on an update.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.delete_rows`\ ``(table_name, where=None, where_params=None, *, all_rows=False)``
     - Delete the rows a WHERE clause selects. With no clause it deletes nothing and
       raises, so a clause that came out empty cannot empty the table; ``all_rows=True``
       is the one way to delete every row.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.delete_joined_rows`\ ``(table_name, join_column, parent_table, parent_column, where, where_params)``
     - Delete a table's rows whose ``join_column`` names a parent row a WHERE clause
       selects, by joining the parent; the parent rows stay. The clause names the
       parent's columns qualified by
       :attr:`~opus_import.importdb.super.ImportDBSuper.JOINED_PARENT_ALIAS`, and every
       value in it is a placeholder. The per-bundle delete reaches a child's rows through
       ``obs_general`` this way.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.general_select`\ ``(cmd, param_list=None)``
     - Run a query the caller assembled and return every row.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.stream_select`\ ``(cmd, param_list=None)``
     - Run a query the caller assembled and yield its rows as the server sends them,
       through an unbuffered cursor, so a scan of a large table never holds the whole
       result in memory. The caller reads every row before it issues another statement
       on the connection. Finalization's mult step reads the observation tables this
       way.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.find_column_max`\ ``(table_name, column_name)``
     - The largest value in a column.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.read_table_keys`\ ``()``
     - Every table's keys as the server reports them, as
       :class:`~opus_import.table_keys.TableKey` values.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.add_keys_statement`\ ``(table_name, keys)`` / :meth:`~opus_import.importdb.super.ImportDBSuper.add_fulltext_key_statement`\ ``(table_name, key)`` / :meth:`~opus_import.importdb.super.ImportDBSuper.add_foreign_key_statement`\ ``(table_name, key)``
     - One statement that adds plain keys to a table, one ``FULLTEXT`` key, or one
       foreign key.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.read_ngram_token_size`\ ``()``
     - The server's ``ngram_token_size``, which the ``FULLTEXT`` keys are built with.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.add_foreign_keys`\ ``(statements)``
     - Add foreign keys one at a time without checking the rows already there.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.key_space_bytes`\ ``(table_name, schema, key)`` / :meth:`~opus_import.importdb.super.ImportDBSuper.index_space_budget`\ ``(server_tmpdir)``
     - A key build's estimated temporary space, and the budget the builds running at
       once share, or None for none.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.run_ddl`\ ``(cmd)`` / :meth:`~opus_import.importdb.super.ImportDBSuper.close`
     - Run one statement that changes a table's definition; close the connection.
   * - :meth:`~opus_import.importdb.super.ImportDBSuper.socket_descriptor`\ ``()``
     - The file descriptor of the connection's socket, or None with no open connection,
       so a forked pool worker can close it without a word sent on it
       (:ref:`dev_guide_import_db_inherited`).
   * - ``_set_foreign_key_checks(enabled)``
     - Turn the connection's foreign key checks on or off, for
       :meth:`~opus_import.importdb.super.ImportDBSuper.foreign_keys_unchecked`.
   * - ``_prepare_index_session(workers, server_tmpdir)``
     - Set a connection's session up for building indexes.
   * - ``_size_index_sort(sort_bytes, key_count)``
     - Size a connection's sort memory for the next statement that builds indexes, from
       its largest key's estimated sort and how many indexes it builds.
   * - ``_execute_and_fetchall(cmd, func_name, param_list=None)``
     - Execute one query and return every row of its result.

The concrete members are the constructor,
:meth:`~opus_import.importdb.super.ImportDBSuper.open_sibling_connection`,
:meth:`~opus_import.importdb.super.ImportDBSuper.build_indexes`,
:meth:`~opus_import.importdb.super.ImportDBSuper.foreign_keys_unchecked`,
:meth:`~opus_import.importdb.super.ImportDBSuper.table_exists`,
:meth:`~opus_import.importdb.super.ImportDBSuper.read_rows`,
:meth:`~opus_import.importdb.super.ImportDBSuper.transaction`,
:meth:`~opus_import.importdb.super.ImportDBSuper.retrying`,
:meth:`~opus_import.importdb.super.ImportDBSuper.failures_expected`, ``_execute``,
``_simulated_count``, the warning collector ``_make_warning_handler``, and
``_operation`` with the ``_enter``/``_exit`` pair it runs.

.. _dev_guide_import_db_transactions:

Transactions, retries and isolation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several import processes can write one schema at once
(:ref:`dev_guide_import_steps_registry`), so every import connection sets its session to
``READ COMMITTED`` as it connects: a locking read locks only the rows it returns and
takes no gap locks.

Outside a transaction each statement commits as it runs.
:meth:`~opus_import.importdb.super.ImportDBSuper.transaction` makes every statement the
body runs through the instance join one transaction instead, committed when the body
returns and rolled back when it raises; transactions do not nest, and a bulk load, which
commits each chunk itself, does not belong in one. When the rollback fails as well, the
connection is in doubt, and
:exc:`~opus_import.importdb.super.RollbackError` is raised, naming both failures and
raised from the body's.

:meth:`~opus_import.importdb.super.ImportDBSuper.retrying` runs a body as one such
transaction, and runs it again when it fails with an error
:meth:`~opus_import.importdb.super.ImportDBSuper.is_retryable_error` accepts -- a
deadlock, or a lock wait that timed out -- after the next pause of
:data:`~opus_import.importdb.super.RETRY_SLEEPS`; the attempt after the last pause is the
final one. A failure its caller says it handles (``expected``), such as the duplicate key
a mult value's insert reads back, is raised at once, unlogged. Any other failure, the
final attempt's, and a ``RollbackError`` always, is logged as fatal with the last
statement run and raised. The body may run more than once, so it reads what it needs
inside itself. While it runs,
:meth:`~opus_import.importdb.super.ImportDBSuper.failures_expected` keeps the write
methods from logging their own failures as fatal, since ``retrying`` decides which one
is.

.. _dev_guide_import_db_inherited:

Connections a pool worker inherits
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Every :class:`~opus_import.importdb.super.ImportDBSuper` adds itself, as it is
constructed, to a module-level weak set of the instances this process has created. A
forked pool worker (:ref:`dev_guide_import_steps_do_import_pool`) inherits every open
connection's socket, and
:func:`~opus_import.importdb.super.close_inherited_connections` is how it lets go of
them: for each instance in the set it closes the descriptor
:meth:`~opus_import.importdb.super.ImportDBSuper.socket_descriptor` returns with
:func:`os.close`, which sends nothing on the socket, so the session the import's process
holds is untouched; and it keeps the instance referenced for the rest of the worker's
life, so the driver's destructor never runs and never sends its quit message on a
descriptor number the worker may since have reused. A worker that kept the socket open
would keep the import's session alive after the import's process died. A brand that does
not implement :meth:`~opus_import.importdb.super.ImportDBSuper.socket_descriptor` never
connected, and is passed over.

Read-only runs
~~~~~~~~~~~~~~

``--read-only`` sets a flag on the connection, and every mutating call passes
``mutates=True`` down to ``_execute``. A read-only run therefore **still executes
non-mutating statements** -- it really reads the database -- and logs each mutating one
with a ``[SIM]`` marker instead of running it. A read-only run's bulk loads take the
``INSERT`` path, so they write no scratch file, and it leaves ``local_infile`` and
``sql_log_bin`` alone; it sets the session's ``sql_mode`` as every connection does. Log
messages branch on the flag too, so a
dropped table reads as ``[SIM] Dropped table`` rather than ``Dropped table``. A
read-only run against a schema the server does not have fails as it connects rather
than creating the schema.

What a read-only import would have written and later reads back is kept in the run
instead. A bundle registration writes no registry row, and keeps the row it would have
added in :attr:`~opus_import.context.ImportContext.planned_ranges`, so a bundle the
registry lacks takes its observation ids from the range it would have been given.
:meth:`~opus_import.importdb.super.ImportDBSuper.increment_counter` logs its ``UPDATE``
and returns the stored counter advanced by the run's own additions, so a new mult value
takes the id it would have. ``--join`` is refused with ``--read-only``: an importer whose
claims are never written would claim the same bundle for ever.

Warnings
~~~~~~~~

Every database operation runs its body inside ``with self._operation(name):``, which
calls ``_enter`` before it and ``_exit`` after it, however the body ends. At the
outermost one, ``_enter`` clears the record of executed statements and installs a
process-wide handler that collects Python warnings; ``_exit`` reports any warnings
together with the statements that produced them, so a warning read out of a log names
the SQL that caused it, and puts the previous handler back. Nesting is tracked, so an
inner operation does not clear an outer one's record. Because ``_exit`` runs on a raise
too, an operation that fails leaves neither the handler installed nor the nesting stack
unbalanced.

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
schemas packaged with :mod:`opus_import` and never from input. A bulk load's values
travel in a scratch file rather than in the statement, written by
:func:`~opus_import.importdb.mysql.load_data_text` with the escapes the statement
reads; only the file's name is a parameter. Some statement builders
here interpolate a caller's ``where`` fragment and carry an explicit note saying so, as
does one in the base class; each is for trusted callers, and only the values inside
such a fragment are bound.

**The upsert needs MySQL 8.0.19.** ``ON DUPLICATE KEY UPDATE`` has to name each row's
new value indirectly, because one statement carries many rows, and the row alias MySQL
8.0.19 added is how: ``AS new`` names the row being inserted, so ``new.col`` is that
row's value for that column. The older ``VALUES(col)`` spelling is deprecated as of
8.0.20. **This is what puts the server floor at 8.0.19**, which the README and
:ref:`user_guide_installation` both state. Two details guard the edges: MySQL requires the
alias to differ from the table name, so a table called ``new`` gets the alias
``new_row`` instead (compared without regard to case, because MySQL folds identifiers
for this check); and the alias is emitted only alongside the clause that reads it,
because a row of nothing but the key has nothing to assign.

Both :meth:`~opus_import.importdb.super.ImportDBSuper.insert_rows` and
:meth:`~opus_import.importdb.super.ImportDBSuper.upsert_rows` write in packets of
1000 rows.

**Connecting.** The constructor connects without naming a database and then issues
``USE``; an unknown-database error makes it **create the schema** and retry, which is
why an import into a new schema needs no ``CREATE DATABASE`` first. A read-only
connection never creates it: an unknown database fails the run, with a fatal message
naming the schema. It then primes a
cache of every table name, reads the server version, and sets a strict SQL mode and the
``READ COMMITTED`` isolation level -- failing the run if it cannot do either. Last, it sets the session up for the import's writes:
it chooses the bulk-load path (below), and where the server keeps a binary log it issues
``SET sql_log_bin = 0``, so the import's rows are not written to it a second time. An
account without the privilege for that gets one info line naming ``--skip-log-bin`` and
the grant instead, and the import goes on. The import's own connection is never closed
explicitly -- there is no destructor and no context manager -- and each statement is run
through its own cursor and committed immediately, except inside
:meth:`~opus_import.importdb.super.ImportDBSuper.transaction`, where the statements
commit together when the transaction ends; the index build closes the sibling
connections it opens.

The driver is imported defensively, so the module still imports without ``mysqlclient``
installed and a package-wide sweep -- Sphinx autodoc, or a test collection -- does not
fail on it. An instance built without the driver forces itself read-only and discards
every statement rather than running it, so it reports no tables and reads no rows. **It
is not a simulation anything can be driven through.**

.. _dev_guide_import_db_bulk_load:

The bulk load
~~~~~~~~~~~~~

:meth:`~opus_import.importdb.mysql.ImportDBMySQL.bulk_load_rows` writes the observation
rows: every ``obs_`` table's rows, ``obs_files``' among them. :class:`~opus_import.steps.do_import_index.TableRowSink` loads a table
each time ``[import] transaction_rows`` of its rows wait, and the rest at the end of
:func:`~opus_import.steps.do_import_index.import_one_index`. Each chunk runs under the
bundle's guard (:class:`~opus_import.import_processes.BundleGuard`, a
:class:`~opus_import.importdb.super.LoadGuard`): the chunk is one transaction, on the
``INSERT`` path as well, whose first statement advances the bundle's ``rows_done`` in the
bundle registry and whose commit an importer drawing from the queue makes only while it
holds its lock. The ``mult`` rows
are not loaded: each is inserted the moment its value is met
(:ref:`dev_guide_import_steps_do_import_mult`), because its value must never be written
over another row's.

**The text.** The rows are written as the text ``LOAD DATA`` reads by default: fields
separated by tabs, rows ended by newlines, ``\N`` for NULL, and a backslash before each
tab, newline, carriage return, NUL or backslash in a value. The statement names those
rules beside ``CHARACTER SET utf8mb4``, which is required because it reads the file in
the schema's character set and ignores ``SET NAMES``. Never CSV: quoting rules differ
between readers, and these escapes do not.
:func:`~opus_import.importdb.mysql.load_data_text` renders each value the way
``insert_rows`` would have sent it, so the two paths store the same thing: a float by its
``repr``, which names the exact double; a boolean as ``1`` or ``0``; and anything else,
a JSON string included, as its text. A test in the import suite writes the same rows both
ways into two tables and compares what the server stored.

**Chunks and scratch files.** The rows go in chunks of at most ``[import]
transaction_rows`` (100,000 by default), each loaded and committed as one transaction,
so a killed import rolls back at most one chunk and the server holds at most one chunk's
undo. Each chunk is written to a file of its own, made by :func:`tempfile.mkstemp` in
``[import] scratch_dir`` (the system temporary directory by default) with the table's
name as its prefix, so two imports sharing the directory never write or load each
other's file. The rows are written to it one at a time from the list the import built,
never copied into a second one, and the file is deleted when its load ends, whether the
load succeeded or not.

**The check.** ``LOAD DATA LOCAL`` behaves as though ``IGNORE`` were given, even under
``STRICT_ALL_TABLES``: a row whose primary or unique key is already present is skipped,
and a value its column cannot hold is converted, each with a warning rather than an
error. So after every load the server's counts for the statement are read -- the
connection's info string, ``Records``, ``Deleted``, ``Skipped`` and ``Warnings`` -- and a
load that read fewer rows than its file holds, skipped any, or warned at all is rolled
back and raised as :exc:`~opus_import.importdb.super.ImportDBError`, with the first
warning's text from ``SHOW WARNINGS``. That check is the only thing that makes a key
reject a duplicate on this path. The counts belong to the connection's last statement,
so another connection loading into the same tables at the same time cannot change them.

**The path, and the fallback.** The connection is opened with ``local_infile`` allowed
when ``[import] bulk_load`` is true, which is the default. The constructor then reads
the server's ``local_infile``; if it is off, the import turns it on with ``SET GLOBAL
local_infile = ON`` where the account may, and otherwise writes with ``INSERT``
statements, as ``insert_rows`` does. A load the server or the connection refuses later
(errors 1148, 2068 or 3948) does the same, from that chunk on. The import log says which
path each invocation took, on a line beginning ``Bulk load path:``, with the reason when
it is the ``INSERT`` path; that and the statement an operator would run are logged at
info level, because a warning would read as a defect in the import rather than in the
server's settings. :ref:`user_guide_installation_prereqs` lists the server settings an
import benefits from.

The type mapping
~~~~~~~~~~~~~~~~

:meth:`~opus_import.importdb.super.ImportDBSuper.create_table` is where a schema's
``field_type`` becomes a MySQL type, and
:meth:`~opus_import.importdb.super.ImportDBSuper.table_info` is the reverse.
:ref:`dev_guide_table_schemas` lists the mapping. An unrecognized type raises
:exc:`NotImplementedError` rather than being guessed at, in both directions.

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
    positional one: ``id``, ``value``, ``label``, ``pin``, ``display``, ``grouping`` and
    ``group_pin``. Building one from the JSON list makes a wrong-length entry raise
    :exc:`TypeError` at the point of construction rather than being mis-assigned later.

:func:`~opus_import.import_util.read_mult_option`
    Builds a :class:`~opus_import.import_util.MultOption` from one ``mult_options``
    entry, and raises :exc:`TypeError` when the entry does not carry exactly seven
    values, when its ``pin`` is not an integer, or when its ``group_pin`` is neither an
    integer nor null. A string such as ``"010"`` is refused rather than converted.

Bundle expansion and PDS table reading
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:func:`~opus_import.import_util.yield_import_bundle_ids`
    Expands the command line's bundle descriptors into concrete bundle ids in import
    order: ids, bundleset names, and the mission and instrument shorthands. Every
    descriptor is validated as a PDS3 path and then as a PDS4 one, and every bad one is
    logged before the run exits, so one invocation reports all of them. A New Horizons
    bundleset's listing is reversed, so its calibrated bundle is yielded before its raw
    one; see :ref:`dev_guide_import_obs_classes` for what that is for and what else it
    reorders. Anything named by ``--exclude-bundles``, and any name containing a dot,
    is dropped.

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

:func:`~opus_import.import_util.mult_field_name`
    The qualified name of the mult field holding a column's values: the column's
    ``mult_field`` key when its schema entry has one, otherwise ``<table>.<column>`` in
    lower case, such as ``obs_general.planet_id``.

:func:`~opus_import.import_util.encode_target_name` and :func:`~opus_import.import_util.decode_target_name`
    A target name is not a legal SQL identifier, so it is encoded: lowercased, with
    ``/`` becoming three underscores and a space becoming four. The decoder reverses the
    two underscore runs -- **but not the lowercasing**, which is why the display label
    is title-cased afterwards.

:func:`~opus_import.import_util.table_name_for_sfc_target` and :func:`~opus_import.import_util.slug_name_for_sfc_target`
    The two forms a surface geometry target takes: the suffix of its category's name,
    ``obs_surface_geometry__<target>``, and the slug the web application's search
    parameters embed. The slug form carries a warning about
    the front end; see :ref:`dev_guide_import_obs_target_template`.

Schemas
~~~~~~~

:data:`~opus_import.schema_files.TABLE_SCHEMA_DIR` and ``DICTIONARY_DATA_DIR``
    The two packaged data directories, as :mod:`importlib.resources` traversables. Every
    read of a table schema or of the context tree goes through one of them, which is what
    lets an installed OPUS find them without a checkout. The first is defined in
    :mod:`opus_import.schema_files`, which imports nothing of the import's own
    dependencies, so the web application reads the schemas through it too
    (:func:`~opus_import.schema_files.packaged_fulltext_columns`).

:func:`~opus_import.import_util.table_schema_files`
    The packaged ``table_schemas`` entries whose file name matches a glob, **sorted by
    name**, so that an import run's order does not depend on the file system's directory
    order. They come back as :mod:`importlib.resources` traversables, not paths, which
    is what lets an installed OPUS find them without a checkout.

:func:`~opus_import.import_util.read_schema_for_table`
    Reads and parses one schema, matching the table's name without regard to case. A
    surface geometry body's category reads as the ``obs_surface_geometry_target``
    template with the body filled in: it is the only place the
    ``<TARGET>``/``<SLUGTARGET>`` substitution happens, and the substitution is plain
    text applied before the JSON is parsed. A name with no schema
    file returns None, which is how a bundle ends up with only the tables its instrument
    has columns in.

:func:`~opus_import.import_util.next_table_id`
    Hands out the next observation id, from the bundle's registered range
    (:attr:`~opus_import.context.ImportContext.bundle_ids`): the range's first id, then
    one more each time. ``obs_general`` is the only table that asks. In a pool worker it
    returns a :class:`~opus_import.deferred.LocalId` instead, which the import's process
    rebases onto the real id (:ref:`dev_guide_import_steps_do_import_pool`). A ``MAX_ID``
    column takes its ids from it.

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

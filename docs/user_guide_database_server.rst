.. _user_guide_database_server:

Configuring the Database Server
===============================

OPUS runs against MySQL with nothing but a user allowed to create and drop databases and
tables (:ref:`user_guide_installation_prereqs`), but a server left at MySQL's defaults
imports slowly and searches from disk. This chapter is the settings that matter to OPUS,
what each one does for it, and how to tell whether the indexes the database carries are
the ones its traffic reads.

One server can import and serve at once, or the import can run on one server and the
database be copied to another that serves it, which the deploy chain's ``database/``
scripts do (:ref:`user_guide_deployment`).
Each setting below says which of those it is for. Settings go in the ``[mysqld]``
section of the server's option file. Those marked **startup only** take effect when the
server restarts; every other one can also be changed while it runs, with ``SET
PERSIST``, which keeps the value across restarts.

.. _user_guide_database_server_memory:

Memory: the buffer pool
-----------------------

``innodb_buffer_pool_size`` is the setting that decides how a search performs. InnoDB
reads every row and index page through the buffer pool, and a page that is not in it is
read from disk while the request waits. A search is a scan of the observation tables or
of their indexes, so a pool that holds them answers from memory and one that does not
answers at the speed of the disk.

**Size it from the database you have, not from a rule of thumb.** The size of each table
of an imported database, data and indexes together, is::

    SELECT table_name,
           ROUND((data_length + index_length) / 1024 / 1024) AS mib
      FROM information_schema.TABLES
     WHERE table_schema = 'opus'
     ORDER BY mib DESC;

with the database's name in place of ``opus``; ``ANALYZE TABLE`` on a table first brings
its figures up to date. The figures to read from it are these:

* **The total** is the most a pool ever needs. A pool that size holds the whole
  database, and nothing a request reads ever comes from disk once it has been read once.
* **The total less** ``obs_files`` **and** ``obs_preview`` is the least a pool should
  hold. ``obs_files`` lists every file of every observation and is usually the largest
  table by far, and ``obs_preview`` holds the preview image descriptions, but both are
  read one observation, or one page of results, at a time, by primary key, so a request
  reads a few of their pages however large they are. The other observation tables are
  the ones a search scans.

Leave room beside the pool for the operating system, for MySQL's per-connection memory,
and, where they share the machine, for the web workers and memcached. On a server that
imports, the pool also bounds the import's index builds: finalization gives its
concurrent index sorts a quarter of the pool between them
(:ref:`dev_guide_import_steps_create_indexes`), so a larger pool builds indexes with
fewer merge passes. The database grows with every bundle the holdings gain, so run the
query again after a full import, not only when the server is first set up.

.. _user_guide_database_server_settings:

The settings, and what each does for OPUS
-----------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 25 15 60

   * - Setting
     - For
     - What it does for OPUS
   * - ``innodb_buffer_pool_size``
     - both
     - The memory InnoDB caches table and index pages in. Sized from the database, as
       above.
   * - ``innodb_redo_log_capacity`` (MySQL 8.0.30 and later)
     - import
     - The size of the redo log. The default, 100 MiB, is small beside the gigabytes an
       import writes, and when the log fills, the server holds writes back while it
       flushes pages to make room; a larger log lets it absorb more of an import before
       it must. A few gigabytes suit an import server. Before 8.0.30 the same is
       ``innodb_log_file_size`` times ``innodb_log_files_in_group``, startup only.
   * - ``innodb_flush_method``
     - both
     - **Startup only.** ``O_DIRECT`` reads and writes data files without passing them
       through the operating system's page cache, so the buffer pool is the one copy of
       each page in memory rather than one of two. Use it on a server whose pool is sized
       as above.
   * - ``innodb_flush_log_at_trx_commit``
     - import
     - ``2`` writes the redo log at each commit but flushes it to disk once a second,
       rather than at every commit. A crash of the machine can then lose the last second
       of commits, which costs an import server nothing that running the import again
       does not restore. A server that also holds the sessions and carts of a live site
       keeps the default, ``1``.
   * - ``local_infile``
     - import
     - ``ON`` lets the import write its observation rows with ``LOAD DATA LOCAL INFILE``
       from a scratch file, much faster than ``INSERT`` statements. An import whose
       account may change it turns it on itself; otherwise it writes ``INSERT``
       statements, and its log says so and names the statement an administrator can run.
       The files are read from the computer running the import, not from the server's
       disk. The setting is the server's, for every client: any client that also enables
       local loading on its own connection, as the import does, may then load files from
       its own computer. To keep it off on a server shared with clients you do not trust,
       set ``[import] bulk_load = false`` (:ref:`user_guide_installation_configuring`), or
       give the import's account no privilege to change global settings, since an import
       that may turn it on does so; the import then writes ``INSERT`` statements.
   * - ``log_bin``
     - import
     - **Startup only.** ``skip-log-bin`` in the option file turns the binary log off. An
       import's rows would otherwise be written twice, once to the tables and once to
       the binary log, which a server that is not a replication source has no use for.
       Where the log is kept, an account granted ``SESSION_VARIABLES_ADMIN`` lets the
       import leave its own writes out of it. (``log_bin = OFF`` does not turn it off: it
       names a log file ``OFF``.)
   * - ``innodb_ddl_threads`` (MySQL 8.0.27 and later)
     - import
     - The threads the server sorts one index build with. Finalization builds the
       indexes after the rows are loaded, several tables at once when ``[import]
       index_workers`` asks for more than one (:ref:`user_guide_installation_configuring`),
       and the threads of every build running at once compete for the server's cores, so
       the default, 4, suits a server that builds on several tables at once.
   * - ``innodb_ddl_buffer_size`` (MySQL 8.0.27 and later)
     - import
     - The sort memory of one index build. The import sets it for each of its own builds
       from the build's estimated size and the buffer pool (above), so the server's value
       matters only as the least each build gets.
   * - ``innodb_io_capacity``, ``innodb_io_capacity_max``
     - import
     - How many pages a second InnoDB's background flushing writes, normally and at
       most. The defaults, 200 and 2000, suit a spinning disk; an import writes faster
       than a server flushing at 200 pages a second keeps up with, and then waits for
       free pages. Set them from what the data directory's device sustains, measured
       with a disk benchmark, not from the device's rating.
   * - ``innodb_parallel_read_threads``
     - import
     - The threads the server reads one clustered index with in parallel. For a query it
       speeds only a ``COUNT(*)`` of a whole table with no ``WHERE`` clause, and ``CHECK
       TABLE``; no search OPUS makes is either. From MySQL 8.0.27 it is also how many
       threads scan a table's rows for an index build, beside ``innodb_ddl_threads``,
       which sort them, so on a server that imports it bounds finalization's index builds
       too: the threads of every build running at once compete for the server's cores, as
       those of ``innodb_ddl_threads`` do.
   * - ``max_connections``
     - serve
     - Each web worker thread keeps its database connection open between requests
       (``[django] conn_max_age``), so a web host holds as many connections as it has
       request slots, workers times threads (:ref:`user_guide_web_server`). Allow for
       every web host's slots, the import's connections (a few for each ``opus_import``
       process, and one more for each of ``[import] index_workers`` during
       finalization), and the administrators'. A server that runs out refuses the
       request that would have opened one more.
   * - ``performance_schema_max_digest_length`` and ``max_digest_length``
     - serve
     - **Startup only.** How much of each statement the server keeps when it counts
       statements by shape (:ref:`user_guide_database_server_statistics`). At the default,
       1024 bytes, OPUS's wide search statements are cut off before the parts that tell
       them apart and are counted as one; 4096 keeps them distinct. The first is capped
       by the second, so raise both.
   * - ``performance_schema_digests_size``
     - serve
     - **Startup only.** How many statement shapes the server counts. Once the table is
       full, every further shape is counted in one overflow row, so the counts describe
       the traffic only while that row holds few statements
       (:ref:`user_guide_database_server_statistics`).
   * - ``innodb_ft_enable_stopword``, ``ngram_token_size``
     - neither
     - These shape full-text indexes, and OPUS creates none: its autocomplete matches
       with ``LIKE``. Leave them at their defaults; ``ngram_token_size`` is startup
       only.

The optimizer's statistics are the ones ``ANALYZE TABLE`` keeps for each index:
``opus_import --analyze-tables``, the last step of every finalization, refreshes them for
every observation and mult table. The import builds no column histograms.

.. _user_guide_database_server_statistics:

Re-collecting the index statistics
----------------------------------

Every index costs disk, buffer pool and import time, and earns its place only if a
search reads it. The way to tell is the server's own counters, read after it has served
the site's traffic for long enough to have seen the searches people make -- a month of
uptime on the database being judged. Two queries give what is needed.

**How often each index was read**, with its size::

    SELECT u.OBJECT_NAME AS table_name,
           u.INDEX_NAME AS index_name,
           u.COUNT_READ AS reads,
           ROUND(s.stat_value * @@innodb_page_size / 1024 / 1024) AS mib
      FROM performance_schema.table_io_waits_summary_by_index_usage u
      LEFT JOIN mysql.innodb_index_stats s
             ON s.database_name = u.OBJECT_SCHEMA
            AND s.table_name = u.OBJECT_NAME
            AND s.index_name = u.INDEX_NAME
            AND s.stat_name = 'size'
     WHERE u.OBJECT_SCHEMA = 'opus'
     ORDER BY u.OBJECT_NAME, u.COUNT_READ;

A row whose ``index_name`` is ``NULL`` counts the rows its table gave up to scans that
used no index at all, so a table with many such reads is searched by a column with no key.

**Which statements took the time**::

    SELECT COUNT_STAR AS executions,
           ROUND(SUM_TIMER_WAIT / 1e12, 1) AS total_s,
           SUM_ROWS_EXAMINED AS rows_examined,
           SUM_NO_INDEX_USED AS without_index,
           DIGEST_TEXT
      FROM performance_schema.events_statements_summary_by_digest
     WHERE SCHEMA_NAME = 'opus'
     ORDER BY SUM_TIMER_WAIT DESC
     LIMIT 50;

**How to read them:**

* **The window is the server's uptime.** Both tables count from the moment the server
  started (``SHOW GLOBAL STATUS LIKE 'Uptime'`` gives it in seconds), and restarting it
  empties them. A database switched in during the window has been counted only since
  then.
* **Keys only an import reads count as zero** in a window with no import in it: the key
  on ``obs_general``'s bundle column, which the per-bundle delete reads, is one. An
  import on the same server during the window counts its own reads beside the site's.
* **The statement counts are complete only when the overflow row is small.** Once the
  server has counted ``performance_schema_digests_size`` shapes, it counts every further
  one in the row whose ``DIGEST`` is ``NULL``::

      SELECT COUNT_STAR FROM performance_schema.events_statements_summary_by_digest
       WHERE DIGEST IS NULL;

  A count there that is large beside the other rows' means the table filled early and
  the list leaves out much of the traffic; raise ``performance_schema_digests_size``
  and collect again.

**What to do with them.** The result is the input for removing plain keys -- a primary or
unique key enforces a rule about the rows, and stays whatever its reads -- by this rule:
a plain key goes when the window shows no read of it, or when it leads a composite key on
the same table (the composite answers every read the shorter key does), **unless** the
import, or a part of the application the traffic in the window did not exercise, reads by
it; a foreign key needs it; its column is one autocomplete searches, whose prefix match
reads it; or the other column of its ``1``/``2`` pair keeps one. A key that leads a
composite goes even then. Keys are declared in the
table schemas that ship with each release (:ref:`dev_guide_table_schemas`), so removing
one is a change to a release, which takes effect at the next full import. A search whose
key was removed still answers, by a scan; the ``NULL`` rows above show it, and ``ALTER
TABLE ... ADD KEY`` on the served database restores the key until a release declares it
again.

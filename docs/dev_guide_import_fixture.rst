.. _dev_guide_import_fixture:

The Mini-Holdings Import Fixture
================================

The import pipeline reads the PDS holdings, which are terabytes on a machine at the
Ring-Moon Systems Node. The mini-holdings fixture is what lets the whole pipeline be
tested without them: a few megabytes of real, subsetted archive metadata checked into
``tests/fixtures/mini_holdings/``, which the ``import_tests`` suite assembles into a
temporary holdings tree and runs the real ``opus_import`` command line against.

The suite is not part of a bare ``pytest`` run. It needs a MySQL server, and it is asked
for by name::

    pytest import_tests

That is the everyday form and the one to use: about two minutes, no coverage. The three
executed-functions tests **skip** in it, saying what to run instead, because the report
they read is not there.

Coverage is the other form, and it costs about two and a half times the runtime. It is two invocations,
because the executed-functions check reads the report the rest of the suite writes and
that report does not exist until the session producing it has ended::

    pytest import_tests --ignore=import_tests/test_obs_execution.py \
        --cov --cov-report=json:coverage.json
    pytest import_tests/test_obs_execution.py

Use it when working on the unexecuted-method whitelist, when you want the
executed-functions report, or to reproduce what CI gates on. Under CI the skip does not
apply: with ``GITHUB_ACTIONS`` set, a missing report is a failure rather than a skip, so
dropping ``--cov`` from the workflow cannot quietly delete the gate.

What the fixture is
-------------------

The import is index-driven. Every value it computes comes from a bundle's primary index
and the summary, inventory and supplemental index files beside it, and it never opens a
data file or asks how big one is: the size, checksum and image dimensions it stores in
``obs_files`` all come from a ``pdsfile`` shelf. So the fixture needs the metadata, the
shelves, and nothing else -- there are no data files in it at all, and no stand-ins for
them either.

Four kinds of thing are checked in:

Subsetted metadata
    ``pds3/metadata/`` and ``pds4/metadata/`` hold the real archive files with rows
    removed. A label ships whole, because ``pdstable`` needs every column definition
    to parse the table it describes; only the ``ROWS`` and ``FILE_RECORDS`` keywords are
    edited. ``pds3/volume_index/`` holds the same for the volume types whose primary
    index lives inside the volume rather than under ``metadata/``, and
    ``pds3/_volinfo/`` holds the volume-set descriptions ``pdsfile``'s preload reads off
    the filesystem with a plain ``os.listdir``.

Shelf manifests
    ``pds3/shelf_manifests/`` and ``pds4/shelf_manifests/`` hold one ``.pydict`` file per
    shelf pickle: a single Python dictionary literal, read with :func:`ast.literal_eval`,
    with one entry per line and its keys sorted. They are text so that the values a test
    depends on -- real checksums, sizes, image dimensions and index row keys -- are
    reviewable in a diff, and so that a regenerated manifest's diff shows exactly the
    entries whose values changed. The extension is deliberately not ``.py``: a manifest
    is data, and this keeps the files outside ruff, mypy and vulture entirely.

Expected products
    ``expected_products/<bundle>.tsv`` lists every file each sampled observation names,
    with its size, as recorded from the real holdings. Which files an observation has is
    not derivable -- per-bundle rules generate candidates and existence filtering decides
    which survive -- so it is recorded once and the suite holds the import to it.

The registry's own coverage
    ``exclusions.tsv`` names each registered bundle type that has no bundle in the
    holdings at all, with the reason beside it. The fixture carries one bundle per entry
    of the bundle registry in :mod:`opus_import.config_bundle_info` that OPUS imports,
    minus those, so a newly registered type fails the suite rather than quietly going
    untested, and an exclusion for a type nobody registers any more fails it too.

Which volume represents each type is a rule rather than a list: the entry's own pattern
is matched against the holdings, the volumes ``scripts/import/import_for_tests.sh``
already imports are dropped -- so the fixture and the self-hosted integration run cover
different volumes between them -- and the middle of what remains is taken. A volume
set's early volumes are its least representative, so a first-volume rule would
systematically pick the worst one.

Which rows are kept is also a rule. The sampler scores rows by *code path*: which
enumerated value a column holds, whether a value is present or absent, whether a
longitude range wraps. It seeds with the row covering the most classes and keeps adding
the row covering the most that nothing chosen so far covers, to a cap. An exposure of
0.1 s and one of 100 s execute exactly the same code, so numeric spread is not scored.

What the suite asserts
----------------------

Expected products, in both directions
    Every recorded product is an ``obs_files`` row and every ``obs_files`` row is a
    recorded product. This is the load-bearing assertion, because a shelf gap fails
    silently rather than loudly: a key missing from a shelf that is present makes
    ``os_path_exists`` return False with no warning at all, so the candidate simply never
    existed and the import is quietly smaller. Nothing else in the run would show it.

The logs
    ``ERRORS.log`` is empty, and every warning is admitted by an entry in
    ``warning_whitelist.txt`` -- one regular expression per line, each with a comment
    above it saying why the warning is benign. An entry that admits nothing fails too: a
    whitelist's whole value is that every line was justified against a warning someone
    actually saw. The log is the gate rather than the exit status because several
    pipeline steps report failure through the log and still exit zero.

The goldens
    ``import_tests/goldens/<table>.tsv`` holds every table the run leaves behind, one
    file per table, rows ordered by primary key. Which tables are covered is a rule:
    everything the schema holds, minus the tables ``manage.py migrate`` creates -- captured
    as the before/after difference around the migration step rather than listed -- minus
    any table excused by name, of which there are none today. A table the import newly
    writes therefore shows up as a golden that does not exist rather than escaping
    comparison.

    No table is excused today, and the list is empty on purpose rather than by omission.
    ``definitions`` was excused while it restated a frozen 1.8 MB data file; with that file
    gone it holds 619 rows computed from the table schemas, the UI reads it for every
    tooltip, and 244 KB is a fair price for covering it. The mechanism stays, because the
    rules it carries are what make an exclusion safe to add: an excused table has to exist
    in the run *and hold rows*, so an entry can neither outlive the table it excuses nor
    cover for one that quietly emptied; it must not also have a golden; and it has to carry
    a written reason. Those checks pass trivially over an empty list and start doing work
    the moment anyone adds to it. Both the generator and the comparison read the list from
    one place, so they cannot disagree about what is covered.

    One column is dropped, though. ``obs_files.url`` is ``holdings/`` or
    ``pds4-holdings/`` followed by the logical path, on all 10,199 rows, and carrying it
    cost about a quarter of the widest table's golden -- 819,984 bytes to store a
    concatenation. It is dropped, and the concatenation is asserted against the database
    instead, where it costs nothing to keep: that assertion is not optional decoration,
    because the column is *this repository's* behavior and not just pdsfile's. pdsfile
    serves a file from an HTML root that begins with a slash; ``do_import_index`` stores
    ``file.url.strip('/')``. The expected-products comparison does not cover it -- it
    never reads ``url``, it re-derives the same path itself and compares that against the
    recorder -- so without the derivation check, dropping the column would have deleted
    the only thing watching that line.

    Nothing else in the table is a mechanical transform of the path. The four columns
    whose names invite the suspicion were measured rather than assumed: between 62 and 83
    logical paths carry two or more different values of ``sort_order``, ``short_name``,
    ``full_name`` and ``product_order``, because one file serves several observations
    under different product classifications. The rest are the values the shelves feed --
    ``checksum``, ``size``, ``width``, ``height`` -- which happen to have one value per
    path here but are not computed from it, and which are what the golden is for in this
    table, together with their linkage to an OPUS id.

    Two further things are normalized. Every column MySQL declares as a
    ``timestamp`` is dropped: the import never writes one and the server fills them from
    the wall clock. And ``obs_general.preview_images`` has its JSON list sorted, because
    it is a ``PdsViewSet`` rendered to a dictionary and ``pdsfile`` documents that its
    members come out in the iteration order of a Python set, which is not stable across
    processes. A third measure sits outside the goldens: the suite pins
    ``PYTHONHASHSEED`` in the pipeline's subprocesses, because several steps iterate sets
    of strings. The one that used to matter most, ``do_param_info``, is now fixed at its
    source -- the backend returns table names sorted -- after CI showed the hash-seed pin
    alone was not enough, since that set is filled from a query with no ``ORDER BY`` and so
    depends on insertion order as well. The view set would be better fixed at its source
    too, and neither is a property of the pipeline this suite should teach anybody to rely
    on.

The re-import path
    One volume is imported a second time into the finished database, and every table is
    compared with the goldens again. This is not a determinism check -- the import is
    deterministic by design. It is the only thing in the suite that runs the *update*
    half of every upsert, which is the documented re-import operational mode.

    A re-import does not leave the database bit-for-bit as it was, and the comparison
    splits in two because of it. The pipeline hands out row ids from the largest already
    present in either namespace and deletes the bundle's old rows only afterwards, so
    re-importing a bundle renumbers it above everything else in the table. Every table
    that holds none of that bundle's rows -- every mult table, and everything the
    dictionary and finalization steps write -- is therefore required to be byte-identical
    to its golden, ids included, which is what says the upsert updated the row it found
    rather than adding another. Every table that does hold them is required to hold the
    same rows with the same values once the two server-numbered columns, ``id`` and
    ``obs_general_id``, are dropped. A third assertion checks that neither half is empty,
    so a bundle id matching nothing cannot make both pass.

Every obs function
    The ``obs`` layer is about twelve thousand lines of field methods, and importing it
    lights up almost all of it without calling anything. The check reads the per-function
    regions of the coverage report and requires each function to have executed at least
    one line, or to be named in ``import_tests/fixtures/unexecuted_methods.txt`` with a
    comment saying why the fixture cannot reach it. An unexecuted method is exactly a
    branch the sampled rows never reached, so its report is also the recorder's guide to
    where the sampling is thin.

The negative cases
    Each is its own run into its own schema with its own log directory, and each is
    exempt from the clean-log rules: a volume imported twice in one invocation under
    ``--import-check-duplicate-id``, and a volume whose index names a target the pipeline
    does not describe under ``--import-ignore-errors``. The volumes that have no metadata
    directory at all cover the missing-summary branches, and the volume set reaches them
    naturally rather than by a special case.

What it cannot test
-------------------

Stated rather than implied. The fixture asserts recorded reality, so it says nothing
about ``pdsfile``'s own correctness. It carries no versioned volume sets and no documents
tree, by decision, and no product whose file ``pdsfile`` cannot address an info shelf for
-- the files inside a PDS4 bundle set's ``_support`` directory, which it does not parse a
bundle name from. A tree with no data files in it can say nothing about a file whose size
and checksum have to come off the filesystem. It cannot reach a class of value that
occurs only in volumes it does not carry, or beyond the row cap in the ones it does. It
says nothing about scale -- thousand-row upsert packets, cache behavior at real volume
counts -- and every bundle in it is one that worked, so real-archive messiness is not
represented. PDS4 runs with shelves-only and a filesystem fallback rather than with
shelves required, because production has no PDS4 shelves yet. The self-hosted integration
run against the real archive remains the only test of the archive itself.

Updating the fixture
--------------------

Two programs regenerate what the suite reads, they own different files, and they run in
this order. Neither runs in CI, and both diffs are reviewed.

**First, the recorder.** It runs on the holdings machine, reads the real holdings, and
never writes into them::

    python -m import_tests.tools.make_mini_holdings \
        --pds3-holdings /path/to/holdings \
        --pds4-holdings /path/to/pds4-holdings \
        --scratch /path/to/a/scratch/directory

It rewrites everything under ``tests/fixtures/mini_holdings/``. PDS3 shelves are read
straight out of the production holdings; PDS4 holdings have none, so it builds them with
``pdsfile``'s own maintenance tools -- ``pds4checksums`` first, because the info shelf
reads its digests from the checksum file rather than computing them -- over plain copies
staged in the scratch directory. It prints one line per recorded volume with the
observation and product counts, and one line per candidate it skipped, with the reason.

**Delete the scratch directory when the holdings have changed.** A PDS4 bundle is
staged by copying it, and a copy that is already there is kept rather than made again --
these are gigabyte-scale bundles that normally do not change between runs. When one has
changed, the shelves get built over the previous copy's bytes, and the recorder's diff
then shows nothing at all: the one failure mode where the fixture silently stops
describing the archive. An empty scratch directory costs a few minutes and removes the
question.

``--compare-schemas`` is the other thing to run by hand, and it is off by default
because it parses every volume of every volume set rather than the two dozen the fixture
keeps. It reports the sibling volumes whose primary index carries a column, or a value
class in a shared column, that the chosen representative's does not -- which is the
evidence for giving a type a second representative.

**Then the goldens.** They need a MySQL server and no holdings::

    python -m import_tests.tools.make_mini_goldens

It builds the tree, runs the whole pipeline, and refuses to write anything unless the run
was clean: an empty ``ERRORS.log``, every warning whitelisted with no stale entries, and
the expected-products assertion satisfied. A broken run can never be blessed. Its
``--seed-whitelist`` option prints every distinct warning the run logged instead, which is
how ``warning_whitelist.txt`` is first written -- each message reviewed, given its
why-benign comment, and admitted one at a time.

Reading the diffs
-----------------

The recorder's diff is the drift report. The fixture encodes ``pdsfile``'s current
answers about which products exist and what they contain, so a ``pdsfile`` upgrade that
changes ``opus_products()`` shows up here as changed lines in
``expected_products/`` and in the shelf manifests. That is not an OPUS bug and should not
be debugged as one: regenerate, read the diff, and decide whether the new answer is
right.

Within a manifest, one changed entry is one changed line, because the layout is pinned to
one sorted key per line with its whole value on that line. A diff that moves many lines
means the shelf's contents changed shape, not that a value moved.

The goldens' diff is the behavior report. Every line of it is a value the import now
computes differently. The tests print a unified diff per table on a mismatch, so a
failure reads as rows rather than as a boolean.

Regenerating the fixture and *not* regenerating the goldens is the useful intermediate
state: the suite then fails with exactly the tables and rows the fixture change moved,
which is the review material for deciding whether the change is wanted.

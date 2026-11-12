.. _user_guide_deployment:

Deployment and Operations
=========================

:ref:`user_guide_installation` brings a server up from nothing with the deploy scripts,
and :ref:`user_guide_web_server` puts a web server in front of it. This chapter is the
running of it afterwards: what a deploy actually does, how a release is deployed onto a
running site, the two things that always have to happen when a database changes, the
runbook for replacing one, and the cron jobs that keep the stored searches bounded and the
log reports current.

The scripts are the same ones the installation chapter wrote out with
``opus_deploy_scripts``, in the deploy directory beside their ``secrets/deploy.env``.
Paths below are relative to that directory, and ``/opt/opus`` stands for whatever
``OPUS_DIR`` names.

.. _deployment_server:

What a deploy does
------------------

**A deployed installation is not a checkout.** It is a directory holding a virtual
environment with the released ``rms-opus`` distribution installed **from PyPI**, the
``opus.toml`` that installation reads, and the ``wsgi.py`` symlink the web server points
at. Nothing on the server builds from source, and nothing on the server needs a checkout.

**Every deploy builds a new installation and switches to it.** Nothing is ever upgraded
in place, and two symbolic links say which installation is which:

::

    /opt/opus/staged/<database>_<timestamp>/
        opus_venv/                # the virtual environment; rms-opus is installed here
        opus.toml                 # this installation's configuration, mode 0600
        wsgi.py                   # symlink into opus_venv/.../site-packages/opus_app/
    /opt/opus/deployed  -> staged/<database>_<timestamp>   # what the web server serves
    /opt/opus/import    -> staged/<database>_<timestamp>   # what an import is using

That shape is what makes a deploy safe to run against a live site, and it follows from
one fact about OPUS: **a release that changes the table schemas cannot read a database
an earlier release imported.** Every OPUS table is created by the import pipeline from
the JSON schemas that ship with a release, so the code and the database it was built by
have to move together, and a deploy that changed either one under a running site would
serve one release's code against another release's database for as long as it took to
finish.

So the import that builds a new database runs under an installation of the new release,
built alongside the running one and touching nothing it uses; the deploy that switches to
it moves the ``deployed`` symlink with a single rename, empties the shared cache, and
restarts the workers. A failure before that moment leaves the site serving exactly what it
was serving, and the previous installation is still on disk afterwards, so going back is
another switch rather than a rebuild. Sessions and carts are rows of the database, so a
deploy that switches to a new database carries them over while the workers are stopped
(:ref:`user_guide_deployment_carry_over`), and every deploy ends by answering the landing
page's requests once, so the first visitor finds them cached
(:ref:`user_guide_deployment_warm_search`).

Underneath the installation root the deploy chain also expects, or creates, these
directories: ``staged/`` for the installations above, ``opus_logs/`` for the web
application's log, ``import_logs/`` for one directory per import run, ``downloads/`` and
``manifests/`` for the cart archives, and ``static_media/`` for the collected static
files.

.. _user_guide_deployment_order:

Deploying a release onto a running site
---------------------------------------

Bringing a server up from nothing is :ref:`user_guide_installation`, in six steps ending
with the first deploy. This is every deploy after that one.

.. _user_guide_deployment_refresh:

**It starts with the scripts themselves.** They ship inside the distribution, so a copy on
a server is one release's chain, and it changes between releases like anything else. One
script brings it up to the release being deployed::

    cd /opt/opus/deploy
    ./import_and_deploy/update_deploy_scripts.sh ==<release>

That upgrades ``rms-opus`` in the environment ``OPUS_DEPLOY_VENV`` names -- the one
these commands come from, not any installation that serves anything -- and rewrites this
directory from it, including ``CHAIN_VERSION``, the file recording which release the
scripts came from. It never touches ``secrets/``, which is not part of what ships and so
is not part of what is written. Every other script prints that version as it starts and
says so when it is deploying a different one, which is the check that this step was not
forgotten.

Then the deploy itself is one command, or two, depending on the release. When it
changes nothing about the table schemas -- a bug-fix release -- the database already
being served is still the right one::

    cd /opt/opus/deploy
    ./import_and_deploy/deploy_new_code_only.sh ==<release>

When the release changes neither the import nor the table schemas -- only the web
application, its templates and static files, or the documentation -- ``--no-database``
deploys it without writing to the database at all::

    ./import_and_deploy/deploy_new_code_only.sh --no-database ==<release>

When it does change them, the database has to be rebuilt under the new release first, and
the two commands are the same pair as steps 4 and 5 of the installation chapter::

    cd /opt/opus/deploy
    ./import_and_deploy/run_full_opus_import.sh ==<release>
    #    ... read the log, check ERRORS.log, compare row counts against the served
    #    database, exercise the staged installation ...
    ./import_and_deploy/deploy_new_code_and_database.sh <database> ==<release>

**Give those two the same version specifier.** They install ``rms-opus`` separately --
the import runs under its own installation and the site is served by another -- so
leaving it off both means "the newest release" twice, which is two different releases if
one is published in between.

Either way the installation being replaced stays under ``staged/``, so going back is
moving the ``deployed`` symlink onto it and restarting -- there is nothing to rebuild.
Going back by hand skips the carry-over, so the sessions and carts made since the deploy
stay behind in the newer database; redeploying the previous database with
``deploy_new_code_and_database.sh <previous database> ==<previous release>`` carries them
back when that release can carry sessions over (:ref:`user_guide_deployment_carry_over`).
The version specifier names the release that imported the previous database: left off,
the newest release is installed, and the schema version check
(:ref:`user_guide_deployment_schema_version`) refuses the database when that release
carries another schema version. Old installations are removed by hand, when the one
after them has been trusted for a while.

The scripts
-----------

``deploy_new_code_and_database.sh <database name> [<version spec>]``
    **The deploy to use whenever the database has been rebuilt**, which is every release
    that changes the table schemas. It builds a new installation under ``staged/``
    naming that database -- virtual environment, ``pip install``, generated
    ``opus.toml``, ``wsgi.py`` symlink -- creates the application's own tables
    (``opus_manage migrate``), gathers the static files, reloads the dictionary and empties
    the search tables of any searches made while the staged installation was being tried
    out, flushing the shared cache with them
    (``opus_import --import-dictionary --reset-search-tables``), and only then switches.
    The import already finalized the database, so nothing else is rebuilt: the workers
    are stopped, the sessions and carts are carried over from the database being served
    (:ref:`user_guide_deployment_carry_over`), the ``deployed`` symlink is moved onto the
    new installation, the cache service is restarted, the workers are started again, and
    the landing page is warmed (:ref:`user_guide_deployment_warm_search`). The workers
    are stopped only for the carry-over and the switch, not while the new installation is
    being prepared.
    Which units those are comes from ``OPUS_WEB_SERVICE`` and ``OPUS_CACHE_SERVICE``.

``deploy_new_code_only.sh [--no-database] [<version spec>]``
    **Only for a release that does not change the database schema** -- a bug-fix release
    against the database already being served. It reads the database name out of the
    installation currently deployed, builds a new installation at the new release naming
    that same database, runs the same migration, static-file and description-table steps,
    and switches to it the same way, warming the landing page afterwards. The database
    does not change, so there is nothing to carry over. It does not upgrade anything in
    place. It leaves the
    search tables alone, so the searches users have made are still stored after the
    release; a release that changes either search table's columns changes the schema
    version, and is deployed with ``deploy_new_code_and_database.sh``.

    The description-table step rebuilds ``param_info``, ``partables``, ``table_names`` and
    the dictionary from the new release, so a release that changed a label, a tooltip or
    a category describes itself. Each table is built beside the live one and swapped in
    with one atomic rename, so the workers still serving the old release never find one
    missing or partly filled. The same step runs ``opus_import --update-mult-info``,
    which writes the release's ``mult_options`` and ``mult_overrides`` over the ``mult``
    rows in place, so a release that renamed a checkbox value shows the label it gives once
    the switch has restarted the workers (:ref:`user_guide_deployment_rename_mult_value`).
    It changes no id, so no observation row is touched.

    ``--no-database`` writes nothing to the database: it skips Django's migrations and
    the description-table step, ``--update-mult-info`` with it, and the warm-up after the
    switch, which stores a search and a session as a visitor's first requests do; it
    still installs the release, collects its static files and switches to it. It is for a release that
    changes neither the import nor the table schemas -- the web application, its
    templates and static files, the documentation. Whether a release is one of those is
    your call, from its release notes, as whether it changed the schema is. It still
    makes the schema version check, which only reads, and it refuses a release for which
    Django has a migration to apply (``opus_manage migrate --plan --check``), naming the
    plain code-only deploy as the one to run, so a release that crosses a Django version
    with a new contrib migration cannot skip it unnoticed. A Django that cannot start is
    refused too, with its own output.

    The database records its schema version, and the script refuses, before writing
    anything, a release whose version differs (:ref:`user_guide_deployment_schema_version`).
    When the schemas did change, the deploy is an import under the new release followed
    by ``deploy_new_code_and_database.sh``.

``update_deploy_scripts.sh [<version spec>]``
    Brings this copy of the chain up to a release: it upgrades ``rms-opus`` in
    ``OPUS_DEPLOY_VENV`` and rewrites the scripts from it. **The first command of every
    upgrade**, before either deploy script.

    It rewrites the file it is running from, which is safe because
    ``opus_deploy_scripts`` replaces each file by renaming a new one over it rather than
    truncating and refilling it: the running script's own file is unlinked from the
    directory and read to its end by the process still holding it open. Truncating in
    place is what would break it -- bash reads a script as it executes it, and would
    resume at the offset it had reached inside the new text, which with a longer
    replacement is a fragment of a line.

``run_full_opus_import.sh [<version spec>]``
    Runs a complete import into a brand-new database, which is the first half of
    deploying a release that changed the schemas. It builds an installation of that
    release under ``staged/`` and points ``import`` at it, so the import runs under the
    release being deployed rather than under whatever is serving, and the result is an
    installation a deploy can switch to. The import itself is ``opus_import_all``, the
    installed command, so the order the bundle sets are imported in comes from the
    release rather than from these scripts. It registers every bundle, imports them
    with the importers ``[import] importers`` and ``workers`` ask for (one, by default,
    since ``workers`` defaults to 1),
    and finishes the database; the database is new, so it erases nothing.

    What happens to the database afterwards is what ``deploy.env`` asked for: with
    ``OPUS_DB_DUMP_DIR`` empty the import ends when the database is built, which is
    what a single server wants; with a directory it dumps into it; and with
    ``OPUS_PEER_DB_HOST`` as well it loads that dump onto the second server. It runs
    detached, and mails the log to ``OPUS_IMPORT_MAIL_TO`` if that names anyone.

    When it is done, the second half is ``deploy_new_code_and_database.sh <that
    database>`` **with the same version specifier this was given**: the two install
    ``rms-opus`` separately, so leaving it off the second is how a release ends up
    serving a database another release built.

The optional argument of all three is a **PEP 440 version specifier** appended to the
distribution name -- ``==<release>`` for a particular release, omitted for the newest.

``database/`` holds ``dump_db.sh`` and ``load_db.sh``, which copy a finished database to
a second server: the first writes ``<database>.sql`` into ``OPUS_DB_DUMP_DIR`` from
``OPUS_DB_HOST``, the second loads it into ``OPUS_PEER_DB_HOST``. Neither knows the name
of any machine. ``run_full_opus_import.sh`` runs the first at the end of an import when
``OPUS_DB_DUMP_DIR`` names a directory and the second as well when there is a peer, and
``scripts/import/clone_database.sh`` in the repository copies one database to another on
the same server.

.. _user_guide_deployment_schema_version:

The schema version check
~~~~~~~~~~~~~~~~~~~~~~~~

A finished database records which generation of the table schemas imported it, in a
one-row ``schema_version`` table holding a version and a state. The import's last step,
``opus_import --write-schema-version``, writes it: ``opus_import_all`` runs it after
validation, and only when validation logged no error, so a database
``run_full_opus_import.sh`` built cleanly has it. Each release carries
its own version, and the web application serves a database only when the row holds that
version in the ``ready`` state. For any other database it answers every request with a
503 whose text names the remedy.

Both deploy scripts make the same check right after building the new installation,
before ``opus_manage`` or ``opus_import`` touches the database, and stop there when it
fails. Nothing has been written to the database at that point, and the installation
being served is untouched:

* **No row**: no release finished the database. Re-import it under the release. If this
  release imported it and only the finishing steps are missing, run them against it:
  ``opus_import --finalize``, ``--import-dictionary`` and ``--validate``, then
  ``--write-schema-version``. ``--finalize`` adds the indexes and keeps one copy of
  each observation two bundles share, which a database stamped without it would lack.
* **Another version**: a different release imported it. Re-import it under this release
  and deploy it with ``deploy_new_code_and_database.sh``.
* **A state other than** ``ready``: an append is still writing to it, or stopped part
  way. Finish it, ending with ``opus_import --write-schema-version``
  (:ref:`user_guide_deployment_adding_bundles`).

``--write-schema-version`` never changes a version a database already records, so a
release cannot claim a database another release imported.

.. _user_guide_deployment_carry_over:

Sessions and carts across a deploy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A user's session and cart are rows of the database being served, in ``django_session``
and ``cart``. A new database starts with both empty, so ``deploy_new_code_and_database.sh``
copies them across. It reads the database being served from the deployed installation's
``opus.toml``, prints it as ``Sessions and carts carried over from:``, and, once the
workers have stopped and before the switch, runs this against the new database::

    opus_import --carry-over-sessions-from <database being served>

In one transaction, it empties the new database's two tables, copies every session that
has not expired and owns a cart row, and copies each cart row of those sessions whose
observation the new database holds, matched by OPUS ID. A failure rolls all of it back.
The log says how many sessions and cart rows it copied, and how many cart rows it dropped
because their session had expired or their observation is not in the new database.

A session without a cart is not copied. OPUS keeps nothing else in a session that a
visitor would miss: a marker that the session exists, and the running total that caps
one session's downloads, which starts again. A staff member signed in to Django's admin
signs in again. The served database holds such a session for every caller of the public
API that sends no cookie, so copying them would lengthen the time the site is down.

* **A first deploy**, with no deployed installation, carries nothing; nor does a redeploy
  of the database already being served. ``deploy_new_code_only.sh`` keeps the database, so
  it has nothing to carry.
* **If the carry-over fails**, the workers are started again on the installation that was
  serving, nothing has switched, and the deploy exits with failure. The deploy first reads
  the release's ``opus_import --help`` to learn whether it has the option; if that fails,
  the deploy stops the same way.
* **A release without the option**, such as an older one being deployed again, cannot
  carry sessions over: its ``opus_import --help`` succeeds and lists no
  ``--carry-over-sessions-from``. The deploy warns, leaves the sessions and carts where
  they are, and switches.
* **Going back by moving the** ``deployed`` **symlink by hand** skips the carry-over, so
  the sessions and carts made since the deploy stay in the newer database. Redeploying
  the previous database with ``deploy_new_code_and_database.sh <previous database>
  ==<previous release>``, naming the release that imported it, carries them back, since
  the step empties its target first and so runs in either direction, but only when that
  release has ``--carry-over-sessions-from``.

``--carry-over-sessions-from`` refuses to run with any other step, and refuses a database
that is the one it would write into, before it changes anything.

.. _user_guide_deployment_warm_search:

Warming the landing page
~~~~~~~~~~~~~~~~~~~~~~~~

Every visitor's first search is the empty one, and the answers the landing page asks for
-- its result count, its first page, and the counts each mult widget shows -- are cached in
memcached until the next import. A deploy restarts memcached, so both deploy scripts run
this once the workers are started again::

    opus_manage warm_search

It issues the landing page's requests through the application itself: the empty search's
result count and first page, the default widgets and the menu, and the empty search's
counts for every searchable mult field, so that opening any mult widget is a cache hit. It
prints each request's status and time, and the total. The site is already serving while
it runs.

* **It needs memcached.** On Django's per-process cache it would fill only its own
  process, so it refuses.
* **A failure is a warning**, not a failed deploy: the site serves, and the first visitors'
  requests fill the cache instead.
* **Each worker still loads its own caches** on its first request; the warm-up fills the
  shared cache and the database's buffers, not the workers.
* ``deploy_new_code_only.sh --no-database`` skips it, since its requests store a search
  and a session as a visitor's do.

Run it by hand after anything else that empties the cache, such as the steps in
:ref:`user_guide_deployment_after_import`.

.. _user_guide_deployment_config:

Deploy configuration
--------------------

The deploy chain has its own configuration, separate from the application's, and the
separation is deliberate.

``secrets/deploy.env``
    **Shell syntax**, read by the scripts before any OPUS code exists on the machine. It
    holds everything about *this* server: where to install, which account to run as,
    which environment the chain's own commands come from, which database to connect to
    and as whom, where the PDS holdings are, what the site calls itself, and what to do
    with a finished database. Nothing in the scripts assumes a value for any of it -- no
    host name, no URL, no path, not even the name of the unit running the web server --
    so the same chain runs on any server that fills this file in.
    :ref:`user_guide_installation_deploy_env` is every variable in it.

``opus.toml``
    Read by the installed application and the import pipeline at run time.
    ``_write_opus_toml.sh`` **generates it** per installation from the values above, and
    the deploy exports ``OPUS_CONFIG`` pointing at it. **Do not hand-write this file on a
    server these scripts deploy**: the next deploy overwrites it. Change ``deploy.env``
    instead. :ref:`user_guide_installation_configuring` says what each generated key
    means.

What is validated, and when
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Two validations run before a deploy touches anything:

* ``_read_deploy_env.sh`` refuses to continue when the account running the deploy is not
  ``OPUS_USER``, naming both and the ``sudo -u`` that fixes it, and when ``OPUS_DEBUG``
  is neither ``true`` nor ``false``. It also refuses if any required variable is missing,
  **empty**, or still the placeholder the template ships. Emptiness is refused as well as
  absence because nothing downstream objects to an empty value -- an empty secret key is
  a well-formed TOML string, and Django starts with no secret key.
* ``_write_opus_toml.sh`` refuses a value containing a control character, because TOML
  cannot represent one inside a quoted string, and it writes the generated file under a
  restrictive umask into a temporary name before renaming it into place, so the file is
  never briefly readable while it already holds the password.

Both failures name the variable at fault, but they happen at different moments. The
missing-value check runs at the very start of a deploy, before anything is built; the
generator runs from ``_opus_setup_environment.sh``, part way through the build, so a
value TOML cannot represent costs a build rather than an outage -- the switch has not
happened, and the site is still serving what it was. That script's own comments record
the same reasoning for its other failure point, the :func:`importlib.util.find_spec`
lookup that locates the WSGI target the web server is pointed at.

``_write_opus_toml.sh`` is a separate program rather than a block inside the setup script
so that it can be run on its own against a controlled environment and its output loaded
through :func:`opus_config.config.load_config` -- which is what its unit test does. A
generator whose only exercise is a production deploy is a generator nobody has checked.

.. _user_guide_deployment_after_import:

Two things that always have to happen
-------------------------------------

After **anything** that changes the database, and both are easy to forget:

**1. The shared Django cache has to be emptied**, because it holds each search's number
and answers computed from the old data: mult counts, range endpoints and product-type
lists::

    OPUS_CONFIG=/opt/opus/deployed/opus.toml \
        /opt/opus/deployed/opus_venv/bin/python -m opus_app.clear_django_cache

That module configures the cache backend and calls ``clear()``, and does nothing else.
Restarting the cache service has the same effect, and is what a deploy does -- the unit
``OPUS_CACHE_SERVICE`` names. Without memcached there is no shared cache: the command
succeeds but empties nothing the workers use, because each worker keeps its cache in its
own memory. Step 2 empties those.

**2. Every worker process has to be restarted**, because each one keeps its own copy of
the tables only an import changes -- ``param_info``, ``table_names``, ``partables``,
``definitions``, ``mult_field`` and ``mult`` -- and, without memcached, its own cache.
**Nothing running outside a worker can reach those**, ``clear_django_cache`` included, so
restarting the application is the only thing that clears them. See
:ref:`dev_guide_webapp_caching`.

.. _user_guide_deployment_runbook:

The import runbook
------------------

A production import is long -- hours to days for the full holdings -- and it replaces
what users see, so it is done deliberately.

1. **Import into a new database, under an installation of the release being deployed.**
   ``run_full_opus_import.sh`` does both: a new installation under ``staged/``, a
   database named for the moment it started, and ``import`` pointed at the installation
   doing the work. Neither the database being served nor the installation serving it is
   touched, which is what makes every step after this one reversible.
2. **Read the error log.** The import's own exit status is not the whole story: several
   steps report a failure through the log rather than through the status, so an
   automated run gates on ``ERRORS.log`` being empty. A failed ``param_info`` build,
   dictionary import or validation does stop the run, before the schema is marked ready.
   :ref:`dev_guide_import_verifying` is the full check.
3. **Compare the new database against the one being served.** The new one is named by
   the installation ``import`` points at (``basename "$(readlink /opt/opus/import)"``),
   and the one being served is the ``schema`` line of ``deployed/opus.toml``. Neither prints row
   counts; comparing those is a separate query you run yourself.
4. **Exercise the new database before switching the public site to it.** The staged
   installation is a complete OPUS pointed at it, and naming its own ``opus.toml`` is
   what makes it read the new database rather than the served one::

       # Query it, do not browse it: this serves no static files, so the
       # interface will not work.
       OPUS_CONFIG=/opt/opus/staged/<that installation>/opus.toml \
           /opt/opus/staged/<that installation>/opus_venv/bin/gunicorn \
           --bind 127.0.0.1:8001 opus_app.wsgi:application

   The public site goes on serving what it was serving throughout.
5. **Switch over** with ``deploy_new_code_and_database.sh <that database>``. It builds
   the installation the public site will use, moves the ``deployed`` symlink onto it,
   empties the cache and starts the workers again -- and stops them only for that switch.
6. **Check the site, and keep the previous installation** until you are sure. It is still
   under ``staged/``, and going back to it is moving the same symlink.

**An import can be resumed rather than restarted.** The per-step options let a run redo
only the part that failed: every import deletes each bundle before it writes it, so a
failed bundle is imported again by naming it, and an interrupted
``opus_import --finalize`` is completed by running it again -- see
:ref:`dev_guide_import_write_paths`.

.. _user_guide_deployment_adding_bundles:

Adding bundles to a database that is not being served
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A finished database the public site is not serving -- the one a full import has just
built, before the switch -- can take more bundles, or fresh copies of ones it holds,
without being imported again from the start. Run ``opus_import`` from the installation
that built it, with that installation's own configuration, which names the database::

    # Each command runs only if the one before it succeeded.
    OPUS_CONFIG=/opt/opus/import/opus.toml \
        /opt/opus/import/opus_venv/bin/opus_import --import COISS_2115 &&
    OPUS_CONFIG=/opt/opus/import/opus.toml \
        /opt/opus/import/opus_venv/bin/opus_import --finalize &&
    OPUS_CONFIG=/opt/opus/import/opus.toml \
        /opt/opus/import/opus_venv/bin/opus_import --validate &&
    OPUS_CONFIG=/opt/opus/import/opus.toml \
        /opt/opus/import/opus_venv/bin/opus_import --write-schema-version

Because the database already holds this release's schema version, the import is an
**append**: each named bundle is deleted from the database and loaded again, or added if
the database did not hold it. The first command marks the database ``appending``, and
from then until ``--write-schema-version`` marks it ``ready`` again, both deploy scripts
refuse it and a web application that starts on it answers every request with a 503
(:ref:`user_guide_deployment_schema_version`). A web server already serving the database
checks only once, as it starts, so it would go on serving the half-changed tables --
which is why this is done only to a database nothing is being served from.
``opus_import --delete-bundles`` marks a finished database ``appending`` in the same
way. ``--finalize`` drops and re-creates the ``cart`` table empty, so every cart the
database holds is lost, not only entries for the appended bundles; a database that has
never been served holds none. Read ``ERRORS.log`` afterwards, as for any
import. A database another release imported is refused rather than appended to, and is
re-imported under this one instead.

**A bundle that fails has to be dealt with before the database can be finished.** The
import records every bundle it takes on, and one whose import fails or logs an error is
recorded as failed: ``--finalize`` and ``--write-schema-version`` both refuse, naming
it, and the database stays ``appending``. Either import it again -- the next
``opus_import --import`` takes up every failed or pending bundle before the ones it
names -- or remove it with ``opus_import --delete-bundles <bundle>``, which deletes its
rows and its record. Then run the three closing commands again. A bundle left
``importing`` by an import that was killed is taken up only after
``opus_import --requeue <bundle>`` returns it.

**A bundle imported again keeps its observations' ids.** Two bundles can hold the same
observation -- a calibrated bundle and its raw counterpart -- and the finished database
keeps the copy from the bundle that was registered later, which on a full import is the
later one in import order. Importing a bundle again does not change which copy that is,
so bundles that share observations are deleted and imported again together.

.. _user_guide_deployment_several_importers:

Sharing a full import between processes or computers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``opus_import_all`` divides the import among **importers**, processes that each take
the largest bundle no other has taken, import it, and take the next, until none is left.
``--workers`` is the total of worker processes on the computer and ``--importers`` how
many importers share them; ``[import] workers`` and ``[import] importers`` give the
defaults, 1 and 4. The importers are capped at the total of workers, so the defaults
start one importer of one worker. The total may not pass the ceiling of ``[import] cpu_fraction`` of the
computer's cores. Six importers of four workers each, for one, need a ceiling of at
least 24, which 30 cores give at a ``cpu_fraction`` of 0.8::

    OPUS_CONFIG=<config> opus_import_all --override-db-schema <database> --importers 6 --workers 24

Adding ``--dry-run`` prints the division and each importer's command without running
anything. The first line of the run states the cores, the fraction, the ceiling and the
workers per importer. On a terminal it shows a table of the running importers and the
totals; under ``nohup`` it writes a line per finished bundle and the totals every
``[import] status_interval_minutes``. ``OPUS_CONFIG=<config> opus_import_all --status
--override-db-schema <database>`` prints the same table from any computer.

An importer that dies (killed, or out of memory) on the computer it runs on is noticed
within seconds: its bundle's rows are deleted, the bundle goes back to the queue, and
another importer is started in its place. One whose computer loses power or its network
is noticed only when the database server gives up on its connection, about two hours
later with Linux's default keepalive settings; running ``KILL <id>`` on the server,
with the ``<id>`` that ``SELECT IS_USED_LOCK('<lock>')`` returns for the lock the
importer's log names, frees it at once. A bundle whose importer dies twice is marked
failed instead. A failed bundle stops the run before the database is finished, naming
the bundle and its importer's log; after the fix, ``opus_import_all --requeue <bundle>`` and running
``opus_import_all`` again import only what is left. Ctrl-C once (or ``kill -INT`` under
``nohup``) lets every importer finish its bundle and stops; twice returns their bundles
to the queue at once, and pressing it again does not interrupt that. Either way the
database is left unfinished, and running the same command again resumes. The reason a
run stops, with each failed bundle's importer log, is printed as it exits and written
to ``opus_import_all_<time>.log`` in ``[paths] import_log_dir``. A bundle an importer
of ``opus_import_all`` held is returned to the queue by the coordinator, or by
``opus_import_all --status --recover``, once its importer is gone; ``--requeue``
refuses it.

Another computer can join a running import: with a configuration naming the same
database server, database and holdings, ``opus_import_all --join --override-db-schema
<database> --importers <M> --workers <N>`` starts importers there under that computer's
own ceiling, adding ``--sets COISS,COVIMS`` on a computer that holds only those bundle
sets. It never registers or finishes anything, starts importers only while there are
bundles they may claim, and can stop at any time; the first computer waits for its
importers before finishing. The database is the same whatever
the number of importers, apart from how a checkbox value new to the import is numbered
and, where bundles disagree about a value's spelling or label, which one is kept.

.. _user_guide_deployment_rename_mult_value:

Renaming a checkbox value
~~~~~~~~~~~~~~~~~~~~~~~~~

A checkbox value's label, whether it is offered, its group and its place in the list
are stored in its ``mult`` row, beside the id the observations hold
(:ref:`dev_guide_database_schema_mult`). None of them is part of an observation, so they
change without an import:

1. **Edit the column's table schema.** For a column whose values the import discovers,
   add an entry to its ``mult_overrides`` naming the stored ``value`` and the
   ``label`` to show -- or ``display``, ``grouping`` or ``pin`` -- or change the entry
   already there. For a column whose schema lists its values in ``mult_options``, change that
   list's entry instead, keeping its id and its value: only the label, the pin, the
   display flag and the group of an entry change in place. :ref:`dev_guide_table_schemas`
   gives both formats.
2. **Release** the change (:ref:`user_guide_deployment_releasing`).
3. **Deploy it** with ``deploy_new_code_only.sh ==<release>``. Its database step runs
   ``opus_import --update-mult-info``, which writes the schemas' ``mult_options`` and
   ``mult_overrides`` over the stored ``mult`` rows and ranks the changed fields again.
   Ids and values never change, so no observation row is touched. If a ``mult_options``
   entry gives a stored id another value, or a stored value another id, the step writes
   nothing, logs each such entry in ``ERRORS.log``, and exits with failure, which stops
   the deploy. The switch at the end restarts the cache service and the web service, and
   the restarted workers read the label.

``deploy_new_code_only.sh --no-database`` skips the database step, so it renames
nothing. A database a full import built already carries the overrides, because
finalization applies them, so a release deployed with ``deploy_new_code_and_database.sh``
needs no extra step.

.. _user_guide_deployment_prune:

Pruning stored searches
-----------------------

The web application stores every search a user makes: one row in ``user_searches``, and
the search's results, one row per matching observation, in ``search_results``. The first
request for a search stores its results and every later request reads them, so
``search_results`` grows with every new search and no request removes anything from it.
``opus_manage prune`` is what bounds it::

    opus_manage prune [--max-rows ROWS] [--unused-days DAYS] [--dry-run]

It needs ``OPUS_CONFIG``, like every other OPUS program. It first reports the state of the
table (below), and then removes, in this order and only as much as it must:

1. **The results of the searches the previous prune removed.** A request that read a
   search just before the prune removed it may still be reading its results, so they
   stay until the next run.
2. **Searches, least recently used first**, until the searches left hold no more than
   ``--max-rows`` rows of ``search_results``, and in any case every search nobody has
   used for ``--unused-days`` days. A search whose results a request is storing at that
   moment, or one used since the prune read when it was last used, is left alone, and
   counted as skipped.
3. **Expired sessions**, through Django's own ``clearsessions``.
4. **Cart rows whose session no longer exists.**

Removing a search costs nothing but speed: the next request for it runs the search and
stores its results again. A search's last use is recorded at most once a day, so a search
in daily use always has a recent stamp: it is never removed for going unused, and it is
among the last removed to bring the table down to ``--max-rows``.

**What every run reports**, before it changes anything: the rows ``search_results``
holds, how many of them belong to searches an earlier prune removed, the number of
searches, the table's data and index bytes and the bytes per row they come to, and how
many searches and rows this run removes and keeps. Then it reports what it removed, one
line per kind.

``--max-rows ROWS``
    The rows the searches left may hold. The table also holds, until the next run, the
    results of the searches this run removed. Default: the configuration's
    ``[django] search_results_max_rows``, which is ``50000000`` when the file does not
    set it (:ref:`user_guide_installation_configuring`). It must be at least 0.

``--unused-days DAYS``
    Remove every search unused for this many days, however few rows the table holds.
    Default ``30``. It must be at least 1.

``--dry-run``
    Print the report and change nothing.

**Sizing** ``--max-rows``. Decide how much disk ``search_results`` may take, and divide it
by the bytes per row ``opus_manage prune --dry-run`` reports on the server itself; that is
the figure to give ``search_results_max_rows`` or ``--max-rows``. Deleting rows does not
shrink the table's file on disk, but InnoDB reuses the pages the deleted rows freed, so a
prune run regularly keeps the table near the size its row limit implies rather than
letting it grow.

**Schedule it hourly**, from the crontab of the account ``OPUS_USER`` names, through the
``deployed`` symlink so that it follows each deploy, under ``flock`` so that a run still
going an hour later is not joined by the next::

    0 * * * *  flock -n /opt/opus/opus_logs/prune.lock env OPUS_CONFIG=/opt/opus/deployed/opus.toml /opt/opus/deployed/opus_venv/bin/opus_manage prune >> /opt/opus/opus_logs/prune.log 2>&1

**Nothing in the deploy scripts runs it or installs that line**: each installation adds it
to its own crontab, as it does the log analyzer's jobs below. A database replaced by
``deploy_new_code_and_database.sh`` starts with empty search tables, and a code-only
deploy keeps them as they are, so neither needs a prune of its own.

.. _user_guide_deployment_log_analyzer:

The log analyzer cron jobs
--------------------------

``log_analyzer/`` holds the cron templates: a nightly update, an
end-of-month report, and a full refresh over a range of months. They are **templates**:
each installation fills in the placeholders -- the virtual environment, the Apache log
directory and its file prefix, and the web directory the reports are published to -- and
installs the result in its own crontab. Nothing substitutes or runs them automatically.

They invoke the analyzer as ``opus_log_analyzer``, the console script the distribution
installs; ``python -m opus_log_analyzer`` runs the same entry point and takes the same
arguments. The nightly update is::

    #!/bin/bash
    source <VENV>/bin/activate
    rm -rf /tmp/log_analyzer_results_temp
    mkdir /tmp/log_analyzer_results_temp
    opus_log_analyzer --cronjob --html --dns \
        -o "/tmp/log_analyzer_results_temp/%Y/OPUS-log-analysis-%Y-%m.html" \
        "<APACHELOGDIR>/<PREFIX>_access_log-%Y-%m-%d"
    cp -r /tmp/log_analyzer_results_temp/* <WWW>/log_analyzer_results
    rm -rf /tmp/log_analyzer_results_temp

The end-of-month job is the same command with ``--cronjob-date -1``, and the refresh job
loops the same command over each month of a year range. The reports they write are
internal operator pages, not part of the public site. :ref:`dev_guide_log_analyzer`
describes the program.

.. _user_guide_deployment_releasing:

Releasing
---------

The version comes from the git tag, through setuptools-scm, and is written into the
distribution at build time; nothing carries a hard-coded version string. Tags continue
the zero-padded ``v3.x`` scheme -- ``scripts/releases/add_release_tag.sh`` creates one,
and ``scripts/releases/show_version_tags.sh`` lists them.

Publishing a tagged release on GitHub triggers the PyPI publish workflow, which builds
the distributions, validates them, and uploads them. A second workflow does the same
against Test PyPI and runs only on demand. :ref:`dev_guide_environment` describes both,
and the ``Package`` job that exercises the whole release path except the upload itself on
every push.

A deploy then installs that release by version specifier, which is why the deploy scripts
take a PEP 440 specifier rather than a branch name.

Operating checklist
-------------------

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Task
     - What to do
   * - Deploy a new release, same database
     - ``deploy_new_code_only.sh ==<version>``
   * - Deploy a release that touches neither the import nor the schemas
     - ``deploy_new_code_only.sh --no-database ==<version>``
   * - Deploy a new database
     - ``run_full_opus_import.sh``, verify, then
       ``deploy_new_code_and_database.sh <name>``
   * - Change a credential or a path
     - Edit ``deploy.env``, then run a deploy. Never edit ``opus.toml`` on a Ring-Moon
       Systems Node server.
   * - Change a field label, a tooltip or a checkbox value's label
     - Edit the table schema, release, then ``deploy_new_code_only.sh ==<version>``,
       which rebuilds the description tables and runs ``--update-mult-info``
       (:ref:`user_guide_deployment_rename_mult_value`).
   * - ``search_results`` is growing
     - The hourly ``opus_manage prune`` cron job
       (:ref:`user_guide_deployment_prune`). It is per-installation and is not deployed.
   * - Reports look stale
     - The log-analyzer cron jobs. They are per-installation and are not deployed.
   * - Results look stale
     - :ref:`user_guide_deployment_after_import`.

API reference
-------------

:doc:`api_opus_config`, :doc:`api_opus_log_analyzer`

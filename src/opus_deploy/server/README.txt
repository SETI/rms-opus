================================================================================
  THE OPUS SERVER DEPLOY CHAIN
================================================================================

These scripts install, import and deploy OPUS on a server.

They were written into this directory by the opus_deploy_scripts command, out
of an installed rms-opus. The file CHAIN_VERSION beside this one says which
release they came from.

This is the short version: what to run, in what order. The full account is the
User Guide -- bringing a server up, then running it:

    https://rms-opus.readthedocs.io/en/latest/user_guide_installation.html
    https://rms-opus.readthedocs.io/en/latest/user_guide_deployment.html

The MySQL server's settings -- its memory, the import's settings, and how to
read which indexes the site's traffic uses -- are in their own chapter:

    https://rms-opus.readthedocs.io/en/latest/user_guide_database_server.html


--------------------------------------------------------------------------------
  THE ONE RULE
--------------------------------------------------------------------------------

A RELEASE THAT CHANGES THE DATABASE SCHEMA CANNOT READ A DATABASE AN EARLIER
RELEASE IMPORTED.

Every OPUS table is created by the import pipeline from the JSON table schemas
that ship with a release, so the code and the database it built have to move
together. That is why nothing here upgrades an installation in place: each
deploy builds a complete installation next to the running one and switches to
it with a single rename.

    /opt/opus/staged/<database>_<timestamp>/    an installation of its own:
                                                opus_venv, opus.toml, wsgi.py
    /opt/opus/deployed -> staged/...            what the web server serves
    /opt/opus/import   -> staged/...            what an import is using

/opt/opus there is only what the User Guide uses. The root is whatever OPUS_DIR
in secrets/deploy.env says -- any directory the OPUS account owns -- and
everything else the chain needs underneath it, it creates.


--------------------------------------------------------------------------------
  FIRST, ONCE
--------------------------------------------------------------------------------

1. The account, the installation root, and the environment these commands come
   from.

   The account is the one OPUS runs as and the one every script here has to be
   run as. The useradd line below is an example of making one. It needs a shell,
   because the deploys are run as it, and a home directory, because pip writes a
   cache into one. OPUS_USER in deploy.env is what names it.

   The root has to exist and belong to that account; everything underneath it,
   the chain creates.

   The environment is not an installation that serves anything -- the chain
   builds those itself. Its path goes into deploy.env below as
   OPUS_DEPLOY_VENV, and every script activates it for itself afterwards; this
   is the one time it is done by hand.

    sudo useradd --system --create-home --shell /bin/bash opus
    sudo install -d -o opus -g opus -m 755 /opt/opus
    sudo -u opus -i
    python3.12 -m venv /opt/opus/deploy_venv
    source /opt/opus/deploy_venv/bin/activate
    python -m pip install "rms-opus==<release>"

   A revision with no release -- a branch, a tag or a commit -- is installed
   from the repository instead, and every step below then takes "@<branch>"
   where it shows "==<release>". pip builds it from a clone, so the server needs
   git and access to GitHub:

    python -m pip install \
        "rms-opus @ git+https://github.com/SETI/rms-opus.git@<branch>"

2. This directory, and its configuration.

    opus_deploy_scripts --directory /opt/opus/deploy
    cd /opt/opus/deploy
    install -d -m 700 secrets
    install -m 600 deploy.env.template secrets/deploy.env

   Then fill in every <PLACEHOLDER> in secrets/deploy.env.

   That file is shell, it holds a database password and a secret key, and the
   scripts RUN it. Mode 0600 in a 0700 directory, set as each is created.

   It holds everything about this server -- where to install, which account to
   run as, which database, what the site calls itself, what to do with a
   finished database. Nothing in these scripts assumes any of it, so the same
   chain runs anywhere the file is filled in.

   OPUS_USER is the account OPUS runs as, and every script below has to be run
   as it: everything a deploy creates belongs to whoever ran it, including an
   opus.toml at mode 0600, so a deploy run as anyone else builds an
   installation the web server cannot read. The scripts refuse rather than
   letting that reach the switch.


--------------------------------------------------------------------------------
  BRINGING UP A SERVER
--------------------------------------------------------------------------------

3. Import the holdings, under an installation of the release being deployed.
   Set OPUS_IMPORT_IMPORTERS and OPUS_IMPORT_WORKERS first: left empty, those
   two run one importer of one worker, and the import is far slower. It runs
   detached and mails the log when it finishes.

    ./import_and_deploy/run_full_opus_import.sh ==<release>

4. Read that log, and ERRORS.log in the run's log directory,
   /opt/opus/import_logs/<run>/. The import exits with failure, leaving the
   database unfinished, when a bundle fails or a finishing step logs an error,
   and ERRORS.log says why; it is the check either way. The database it built
   is named by the installation that the import symlink now points at:

    basename "$(readlink /opt/opus/import)"

   Bundles can be added to that database, or imported again into it, before it
   is served. Each command runs only if the one before it succeeded, and from
   the first until the last the database is "appending", which the web
   application and both deploy scripts refuse:

    export OPUS_CONFIG=/opt/opus/import/opus.toml
    /opt/opus/import/opus_venv/bin/opus_import --import COISS_2115 &&
    /opt/opus/import/opus_venv/bin/opus_import --finalize &&
    /opt/opus/import/opus_venv/bin/opus_import --validate &&
    /opt/opus/import/opus_venv/bin/opus_import --write-schema-version

   A bundle that fails stops --finalize and --write-schema-version until it is
   imported again or removed with `opus_import --delete-bundles <bundle>`.

5. Build the installation that will serve, and switch to it.

    ./import_and_deploy/deploy_new_code_and_database.sh \
        opus3_20260902T031500_1 ==<release>

6. Point the web server at /opt/opus/deployed/wsgi.py. Once, and never again:
   every later deploy moves that symlink rather than the web server's
   configuration.

GIVE STEPS 3 AND 5 THE SAME VERSION SPECIFIER. They install rms-opus
separately, so leaving it off both means "the newest release" twice -- which is
two different releases if one is published in between.


--------------------------------------------------------------------------------
  UPDATING A RUNNING SERVER
--------------------------------------------------------------------------------

Always start by updating these scripts. They ship inside the distribution and
change with it, so deploying a new release with an old chain runs one release's
deploy against another release's application.

    cd /opt/opus/deploy
    ./import_and_deploy/update_deploy_scripts.sh ==<release>

Wherever a release is named, "@" and a git branch, tag or commit names a
revision with no release instead, which pip builds from a clone of the
repository (the server needs git): update_deploy_scripts.sh @main, then
deploy_new_code_only.sh @main, and so on.

Then the deploy itself, and which one it is depends on the release. One deploy
runs at a time: each takes a lock on deploy.lock in OPUS_DIR right after
reading deploy.env, and a second deploy started meanwhile stops at once,
changing nothing.

  * The release does NOT change the database schema -- a bug-fix release. The
    database already being served is still the right one:

    ./import_and_deploy/deploy_new_code_only.sh ==<release>

    It rebuilds param_info, partables, table_names and the dictionary from the
    release, and writes the release's mult_options and mult_overrides over the
    mult rows in place (opus_import --update-mult-info), so a release that
    renames a checkbox value shows the renamed label once the workers restart.

  * The release changes neither the import nor the table schemas -- only the
    web application, its templates and static files, or the docs. The database
    is served as it stands:

    ./import_and_deploy/deploy_new_code_only.sh --no-database ==<release>

    It skips Django's migrations, the rebuild of param_info, partables,
    table_names and the dictionary, and --update-mult-info, and refuses if
    Django has a migration to apply.

  * The release DOES change it. The database has to be rebuilt under the new
    release first, which is steps 3 to 5 again:

    ./import_and_deploy/run_full_opus_import.sh ==<release>
    (read the log; compare row counts against the served database)
    ./import_and_deploy/deploy_new_code_and_database.sh \
        <that database> ==<release>

The database records its schema version and a state, and both deploy scripts
refuse, before writing anything, a database that does not hold the release's
version in the "ready" state. The refusal names what is wrong and the
remedy: an import under the release, deployed with
deploy_new_code_and_database.sh, or, for a database this release imported
and did not finish, its finishing steps -- `opus_import --finalize`,
`--import-dictionary` and `--validate` -- then
`opus_import --write-schema-version`. A database stamped without --finalize
lacks its indexes and keeps both copies of an observation two bundles share.

Bundles of the served database can be imported again, added or dropped
without a full import. The update goes into the served database as a new
generation, which the site does not show until it is switched in:

    ./import_and_deploy/run_incremental_opus_update.sh ==<release> \
        COISS_2115 --drop COISS_2001
    (read the log, and ERRORS.log, once the mail says it has finished)
    ./import_and_deploy/promote_generation.sh
    (check the site)
    export OPUS_CONFIG=/opt/opus/deployed/opus.toml
    /opt/opus/deployed/opus_venv/bin/opus_import --purge-generations

The bundles named are imported, replacing the copies the database holds;
--drop names bundles to remove. A bundle named both ways is imported. The
update runs detached, mails its log, and holds the deploy lock until it
ends. Without a version spec it installs what is being served: its release,
or the git commit it was built from.

--continue writes into the pending generation an earlier update began
instead of beginning one. It breaks an update into several commands on
purpose -- the first begins the generation with some bundles, and each later
one adds bundles or drops to it, which the site does not show until it is
switched in -- and it goes on with an update that stopped part way, once
its cause is fixed, run again with the same bundles. It aborts before
writing the database when it has no pending generation (opus_import
--check continue); the installation it built and its log directory remain. A
bundle an import left importing when it was stopped is refused until it
is returned to the queue, from the installation the update built:

    OPUS_CONFIG=<that installation>/opus.toml \
        <that installation>/opus_venv/bin/opus_import --requeue <bundle>

Every command of an update after the begin is given
--require-pending-generation, so one that finds no pending generation (an
--abandon-generation ran after the begin) writes nothing.

promote_generation.sh takes the deploy lock, asks whether the switch would
run (opus_import --check switch, which stops nothing when it would be
refused), stops the web server,
switches the generation in, restarts the cache service and the web server,
and warms the common searches. If the switch fails, the web server stays
stopped: running promote_generation.sh again completes the switch, and
`promote_generation.sh --revert` goes back. A switch refused after the
stop changed nothing, and the web server is started again if it was
serving. The purge deletes the rows the switch replaced, while the site
serves.

Until the purge, the update can be undone:

    ./import_and_deploy/promote_generation.sh --revert
    OPUS_CONFIG=/opt/opus/deployed/opus.toml \
        /opt/opus/deployed/opus_venv/bin/opus_import --abandon-generation

An update that failed, or one not yet switched in, is thrown away with the
second command alone; after a switch that stopped part way it is refused
until promote_generation.sh, or the same with --revert, has finished what
was begun. Deploy no code while a generation is pending: a
code-only deploy's auxiliary tables would wait for the switch. Without a
second server that holds a copy, take a dump of the served database before
the update, with OPUS_DB_DUMP_DIR set:

    ./database/dump_db.sh <the served database>

With OPUS_PEER_DB_HOST set, the update ends by loading the updated database
onto that server under a new name, which the log gives. Nothing serves it
there, so on that server the switch needs no stop, and the purge follows at
once, since the way back there is the database it was serving:

    export OPUS_CONFIG=/opt/opus/deployed/opus.toml
    /opt/opus/deployed/opus_venv/bin/opus_import \
        --override-db-schema <that database> --switch-generation
    /opt/opus/deployed/opus_venv/bin/opus_import \
        --override-db-schema <that database> --purge-generations
    ./import_and_deploy/deploy_new_code_and_database.sh \
        <that database> ==<release>


--------------------------------------------------------------------------------
  AFTER A DEPLOY
--------------------------------------------------------------------------------

deploy_new_code_and_database.sh and promote_generation.sh end with
`opus_manage warm_search`, which asks the site, over its public URL, for the
landing page and for one search per planet, mission, instrument and the
like, so that their results are built and the rows they read are in the
database server's memory when the first visitors come. It takes minutes. A
failure of it is a warning, not a failed deploy. deploy_new_code_only.sh
does not run it: the database it goes on serving keeps both.

deploy_new_code_only.sh refuses, before writing anything, while an
incremental update's generation is pending (opus_import --check rebuild),
unless given --no-database: its rebuild of the description tables would be
left for the generation's switch.

deploy_new_code_and_database.sh also carries the sessions and carts over from
the database being served into the new one, while the web server is stopped.
Only sessions that own a cart row are copied: a session holds nothing else a
visitor would miss. A cart row whose session has expired, or whose observation
the new database lacks, is dropped, and the log counts them. The copy is one
transaction. If it fails, or if the release's `opus_import --help` fails, so
that whether it has the option is unknown, the web server is started again on
the installation that was serving, and nothing has switched. A release whose
help lists no such option, such as an older one, warns and switches without
carrying anything.

The installation that was replaced is still under staged/. Going back to it is
moving the deployed symlink onto it and restarting the web server -- there is
nothing to rebuild. Going back that way skips the carry-over, so the sessions
and carts made since the deploy stay behind in the newer database. To carry
them back, redeploy the previous database instead, which carries them only
when the release you deploy has --carry-over-sessions-from:

    ./import_and_deploy/deploy_new_code_and_database.sh \
        <previous database> <its version specifier>

Old installations are deleted by hand, once the one after them has been trusted
for a while.


--------------------------------------------------------------------------------
  WHAT IS IN HERE
--------------------------------------------------------------------------------

  import_and_deploy/
    update_deploy_scripts.sh          Brings this directory up to a release
                                      or a git revision.
                                      The first command of every upgrade.
    run_full_opus_import.sh           A full import, under a new installation
                                      of the release being deployed.
    deploy_new_code_and_database.sh   Deploys a release together with the
                                      database it imported.
    deploy_new_code_only.sh           Deploys a release against the database
                                      already being served.
    run_incremental_opus_update.sh    Imports, adds or drops bundles of the
                                      served database, as a generation it
                                      does not show yet.
    promote_generation.sh             Switches that generation in, or, with
                                      --revert, back out.
    _*.sh                             Sourced or run by those: the deploy
                                      configuration, the deploy lock, the
                                      virtual environment, the version check,
                                      one installation, the import, the
                                      update's steps, the copy to a second
                                      server, the switch, and the switch's
                                      steps that can fail on their own.

  database/                           dump_db.sh and load_db.sh: copy a finished
                                      database to the server OPUS_PEER_DB_HOST
                                      names, through OPUS_DB_DUMP_DIR. Both run
                                      scripts end with them when deploy.env
                                      sets those; load_db.sh can give the copy
                                      a name of its own.
  log_analyzer/                       Cron templates for the log-analyzer
                                      reports. Fill in the placeholders.
  deploy.env.template                 The contract for secrets/deploy.env.
                                      Everything about this server is in it.
                                      Every <PLACEHOLDER> has to be filled in;
                                      the rest ship with usable defaults.
  CHAIN_VERSION                       The release these scripts came from.

secrets/ is yours. Nothing that ships is written there, and updating these
scripts never touches it.

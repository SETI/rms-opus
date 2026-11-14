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
    python -m pip install "rms-opus==3.24.0"

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
   Hours to days. It runs detached and mails the log when it finishes.

    ./import_and_deploy/run_full_opus_import.sh ==3.24.0

4. Read that log, and ERRORS.log. An import can exit 0 having logged errors, so
   the log is the gate rather than the status. The database it built is named by
   the installation that the import symlink now points at:

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
        opus3_20260902T031500_1 ==3.24.0

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
    ./import_and_deploy/update_deploy_scripts.sh ==3.24.1

Then the deploy itself, and which one it is depends on the release. One deploy
runs at a time: each takes a lock on deploy.lock in OPUS_DIR before it reads
anything, and a second deploy started meanwhile stops at once, changing nothing.

  * The release does NOT change the database schema -- a bug-fix release. The
    database already being served is still the right one:

    ./import_and_deploy/deploy_new_code_only.sh ==3.24.1

    It rebuilds param_info, partables, table_names and the dictionary from the
    release, and writes the release's mult_options and mult_overrides over the
    mult rows in place (opus_import --update-mult-info), so a release that
    renames a checkbox value shows the renamed label once the workers restart.

  * The release changes neither the import nor the table schemas -- only the
    web application, its templates and static files, or the docs. Nothing need
    be written to the database:

    ./import_and_deploy/deploy_new_code_only.sh --no-database ==3.24.1

    It skips Django's migrations, the rebuild of param_info, partables,
    table_names and the dictionary, and --update-mult-info, and refuses if
    Django has a migration to apply.

  * The release DOES change it. The database has to be rebuilt under the new
    release first, which is steps 3 to 5 again:

    ./import_and_deploy/run_full_opus_import.sh ==3.25.0
    (read the log; compare row counts against the served database)
    ./import_and_deploy/deploy_new_code_and_database.sh \
        <that database> ==3.25.0

The database records its schema version, and both deploy scripts refuse,
before writing anything, a release whose version differs from it. A refusal
names the remedy: an import under the new release, or, for a database this
release imported but did not finish, its finishing steps -- `opus_import
--finalize`, `--import-dictionary` and `--validate` -- then
`opus_import --write-schema-version`.


--------------------------------------------------------------------------------
  AFTER A DEPLOY
--------------------------------------------------------------------------------

Every deploy ends with `opus_manage warm_search`, which asks the site, over
its public URL, for the landing page and for one search per planet, mission,
instrument and the like, so that the first visitors find them ready. A failure
of it is a warning, not a failed deploy. --no-database skips it, since it
writes searches and a session as visitors' requests do.

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
    update_deploy_scripts.sh          Brings this directory up to a release.
                                      The first command of every upgrade.
    run_full_opus_import.sh           A full import, under a new installation
                                      of the release being deployed.
    deploy_new_code_and_database.sh   Deploys a release together with the
                                      database it imported.
    deploy_new_code_only.sh           Deploys a release against the database
                                      already being served.
    _*.sh                             Sourced by those: the deploy
                                      configuration, the deploy lock, the
                                      virtual environment, the version check,
                                      one installation, the import, the switch,
                                      and the switch's steps that can fail on
                                      their own.

  database/                           dump_db.sh and load_db.sh: copy a finished
                                      database to the server OPUS_PEER_DB_HOST
                                      names, through OPUS_DB_DUMP_DIR.
  log_analyzer/                       Cron templates for the log-analyzer
                                      reports. Fill in the placeholders.
  deploy.env.template                 The contract for secrets/deploy.env.
                                      Everything about this server is in it.
                                      Every <PLACEHOLDER> has to be filled in;
                                      the rest ship with usable defaults.
  CHAIN_VERSION                       The release these scripts came from.

secrets/ is yours. Nothing that ships is written there, and updating these
scripts never touches it.

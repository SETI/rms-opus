================================================================================
  THE OPUS SERVER DEPLOY CHAIN
================================================================================

These scripts install, import and deploy OPUS on a server.

They were written into this directory by the opus_deploy_scripts command, out
of an installed rms-opus. The file CHAIN_VERSION beside this one says which
release they came from.

This is the short version: what to run, in what order. The full account is the
User Guide:

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

/opt/opus there is the installation root, named by OPUS_DIR in
secrets/deploy.env. Everything else the chain needs underneath it, it creates.


--------------------------------------------------------------------------------
  FIRST, ONCE
--------------------------------------------------------------------------------

1. The environment these commands come from. It is not an installation that
   serves anything -- the chain builds those itself. Its path goes into
   deploy.env below as OPUS_DEPLOY_VENV, and every script activates it for
   itself afterwards; this is the one time it is done by hand.

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

Then the deploy itself, and which one it is depends on the release.

  * The release does NOT change the database schema -- a bug-fix release. The
    database already being served is still the right one:

    ./import_and_deploy/deploy_new_code_only.sh ==3.24.1

  * The release DOES change it. The database has to be rebuilt under the new
    release first, which is steps 3 to 5 again:

    ./import_and_deploy/run_full_opus_import.sh ==3.25.0
    (read the log; compare row counts against the served database)
    ./import_and_deploy/deploy_new_code_and_database.sh \
        <that database> ==3.25.0

Nothing here can tell you which case you are in: a database carries no record
of the release that wrote it. The release notes can.


--------------------------------------------------------------------------------
  AFTER A DEPLOY
--------------------------------------------------------------------------------

The installation that was replaced is still under staged/. Going back to it is
moving the deployed symlink onto it and restarting the web server -- there is
nothing to rebuild. Old installations are deleted by hand, once the one after
them has been trusted for a while.


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
                                      configuration, the virtual environment,
                                      the version check, one installation, the
                                      import, and the switch.

  database/                           Dump a database from one server and load
                                      it onto the other.
  log_analyzer/                       Cron templates for the log-analyzer
                                      reports. Fill in the placeholders.
  deploy.env.template                 The contract for secrets/deploy.env.
                                      Every variable in it is required.
  CHAIN_VERSION                       The release these scripts came from.

secrets/ is yours. Nothing that ships is written there, and updating these
scripts never touches it.

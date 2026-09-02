# The OPUS server deploy chain

These scripts install, import and deploy OPUS on a server. They were written here by
`opus_deploy_scripts`, out of an installed `rms-opus`; `CHAIN_VERSION` beside this file
says which release they came from.

The full account is the **User Guide** at
<https://rms-opus.readthedocs.io/en/latest/user_guide_deployment.html>. This is the short
version: what to run, in what order.

## The one rule

**A release that changes the database schema cannot read a database an earlier release
imported.** Every OPUS table is created by the import pipeline from the JSON table
schemas that ship with a release, so the code and the database it built have to move
together. That is why nothing here upgrades an installation in place: each deploy builds
a complete installation next to the running one and switches to it with a single rename.

```text
/opt/opus/staged/<database>_<timestamp>/   an installation: venv, opus.toml, wsgi.py
/opt/opus/deployed -> staged/...           what the web server serves
/opt/opus/import   -> staged/...           what an import is using
```

`/opt/opus` there is the installation root named by `OPUS_DIR` in `secrets/deploy.env`.
Everything else the chain needs underneath it, it creates.

## First, once

```bash
# 1. The environment these commands come from. Not an installation that serves
#    anything: the chain builds those itself. Its path goes in deploy.env below,
#    as OPUS_DEPLOY_VENV, and every script activates it for itself afterwards.
python3.12 -m venv /opt/opus/deploy_venv
source /opt/opus/deploy_venv/bin/activate
python -m pip install "rms-opus==3.24.0"

# 2. This directory, and its configuration.
opus_deploy_scripts --directory /opt/opus/deploy
cd /opt/opus/deploy
install -d -m 700 secrets
install -m 600 deploy.env.template secrets/deploy.env
#    ... then fill in every <PLACEHOLDER> in secrets/deploy.env
```

`secrets/deploy.env` is shell, it holds a password and a secret key, and the scripts
*run* it. Mode 0600 in a 0700 directory, set as each is created.

## Bringing up a server

```bash
# 3. Import the holdings, under an installation of the release being deployed.
#    Hours to days. Runs detached; mails the log when it finishes.
./import_and_deploy/run_full_opus_import.sh ==3.24.0

# 4. Read that log, and ERRORS.log. An import that exits 0 can still have logged
#    errors, so the log is the gate. The database it built:
basename "$(readlink /opt/opus/import)"

# 5. Build the installation that will serve, and switch to it.
./import_and_deploy/deploy_new_code_and_database.sh opus3_20260902T031500_12345 ==3.24.0

# 6. Point the web server at $OPUS_DIR/deployed/wsgi.py. Once: every later deploy
#    moves that symlink rather than the web server's configuration.
```

**Give steps 3 and 5 the same version specifier.** They install `rms-opus` separately, so
leaving it off both means "the newest release" twice — two different releases if one is
published in between.

## Updating a running server

Always start by updating these scripts. They ship inside the distribution and change with
it, so deploying a new release with an old chain runs one release's deploy against
another release's application:

```bash
cd /opt/opus/deploy
./import_and_deploy/update_deploy_scripts.sh ==3.24.1
```

Then, if the release **does not** change the database schema — a bug-fix release — the
database already being served is still the right one:

```bash
./import_and_deploy/deploy_new_code_only.sh ==3.24.1
```

If it **does** change the schema, the database has to be rebuilt under the new release
first, which is steps 3 to 5 again:

```bash
./import_and_deploy/run_full_opus_import.sh ==3.25.0
# ... read the log, compare row counts against the served database ...
./import_and_deploy/deploy_new_code_and_database.sh opus3_20260915T020000_31337 ==3.25.0
```

Nothing here can tell you which case you are in: a database carries no record of the
release that wrote it. The release notes can.

## After a deploy

The installation that was replaced is still under `staged/`. Going back to it is moving
the `deployed` symlink onto it and restarting the web server — there is nothing to
rebuild. Old installations are deleted by hand, once the one after them has been trusted
for a while.

## What is in here

| Path | What it is |
| --- | --- |
| `import_and_deploy/update_deploy_scripts.sh` | Brings this directory up to a release. First command of every upgrade. |
| `import_and_deploy/run_full_opus_import.sh` | A full import, under a new installation of the release being deployed. |
| `import_and_deploy/deploy_new_code_and_database.sh` | Deploys a release together with the database it imported. |
| `import_and_deploy/deploy_new_code_only.sh` | Deploys a release against the database already being served. |
| `import_and_deploy/_*.sh` | Sourced by those: the deploy configuration, the virtual environment, the version check, one installation, the import, the switch. |
| `database/` | Dump a database from one server and load it onto the other. |
| `log_analyzer/` | Cron templates for the log-analyzer reports. Fill in the placeholders. |
| `deploy.env.template` | The contract for `secrets/deploy.env`. Every variable is required. |
| `CHAIN_VERSION` | The release these scripts came from. Written by `opus_deploy_scripts`. |

`secrets/` is yours: nothing that ships is written there, and a refresh never touches it.

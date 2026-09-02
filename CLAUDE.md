# Working in rms-opus

Orientation for an AI coding assistant working in this repository. The developer
documentation is the authority on everything below; this file exists so a fresh
context knows where to look.

## What this is

rms-opus is OPUS, the search tool for the PDS Ring-Moon Systems Node. It is one
pip-installable distribution containing an import pipeline that populates a MySQL
database from PDS3/PDS4 holdings, and a Django web application serving the public
OPUS API and UI.

## Layout and entry points

Everything importable lives under `src/`: `opus_config` (the TOML configuration
loader), `opus_support` (unit, time, clock, angle and orbit conversions),
`opus_import` (the import pipeline), `opus_log_analyzer` (the server log analyzer)
and `opus_app` (the Django project). The installed commands are `opus_import`,
`opus_log_analyzer` and `opus_error_analyzer`; the first two also run as
`python -m opus_import` and `python -m opus_log_analyzer`. Two more exist for an
installation that has no checkout: `opus_manage` is Django's own management command
line with the settings module already named, so only `OPUS_CONFIG` is needed in the
environment, and `opus_config_template` writes `opus.toml.template` (which ships
inside `opus_config`) into the working directory.

`docs/dev_guide_layout.rst` annotates the whole tree. Build the documentation with
`scripts/read-docs.sh`, or read it at <https://rms-opus.readthedocs.io>.

## Configuration

Every process reads one TOML file, located by the `OPUS_CONFIG` environment
variable. The loader has no default path: an unset or empty variable is an error
naming the variable. The `opus_config_template` command writes out
`opus.toml.template`, the file to copy and fill in;
`tests/fixtures/opus_ci.toml` is the dummy configuration the holdings-free jobs
run against, and the one `docs/conf.py` falls back to so a documentation build
works without the variable set.

## Tests

Three suites, selected by path:

- `pytest` — the holdings-free unit suite (`tests/`), the default run.
- `pytest import_tests` — the import pipeline end to end against the checked-in
  mini-holdings fixture. Needs a reachable MySQL server; no PDS holdings.
- `pytest integration_tests` — the golden-response API suite against a populated
  database. Needs the terabyte holdings and a full import behind it, so it runs on
  the Node's own hardware rather than anywhere else.

`docs/dev_guide_testing.rst` says what each suite needs and how to run it.

`scripts/run-all-checks.sh` runs the gates rather than a suite — ruff, mypy,
pytest, pyroma, bandit, vulture, Sphinx and PyMarkdown. Run it before proposing a
change; `--import-tests` adds the import suite, which it otherwise leaves out
because that one needs a database.

## Standards

The coding and documentation standards are the `.cursor/rules/*.mdc` files. Follow
them. One repository-specific waiver: the public web API's behavior is preserved
even where those rules forbid backwards compatibility, because external callers
depend on it — see `docs/dev_guide_conventions.rst`. That waiver covers the public
API only; internal code carries no compatibility shims.

Two rules worth stating here because they are easy to violate while being helpful:
a comment or docstring describes the code as it is now, never how it came to be;
and a claim about the code that can be counted is either measured or not made —
state the command that regenerates a set rather than writing the set out.

## History

`plans/archive/` and `critiques/archive/` hold the design documents behind the
current tree and the reviews of them. They are a record of decisions already
taken, not a specification of work to do, and nothing in them describes the
software more accurately than the software and its documentation do.

# rms-opus Modernization Plan

**Target executor:** an opus-class AI — **one fresh sub-agent per PR, no shared context** (execution protocol in §4a).
**Strategy:** all PRs target a long-lived `rewrite` branch off `main`; `rewrite` merges to `main` once at the end.
**Date:** 2026-07-18 (rev 6 — rev 4 fixed all findings from two independent adversarial reviews; rev 5 added the API-guide migration to ReadTheDocs; rev 6 adds the per-PR sub-agent execution protocol)

---

## 1. Context

rms-opus contains the OPUS search tool for the PDS Ring-Moon Systems Node: a ~16.7K-line,
79-file import pipeline (`opus/import`) that populates a MySQL database from PDS3/PDS4
holdings, and a ~26K-line, 9-app Django web application (`opus/application`) serving the
public OPUS API and UI. The repo predates the RMS Node's modern repo conventions
(`/seti/all_repos/rms-devenv/repo_template`): nothing is pip-installable, the three code
bodies (import, Django app, `lib/opus_support.py`) are glued together by `sys.path.insert`
calls and a `from opus_secrets import *` wildcard, there are zero type annotations, near-zero
docstrings, no unit tests for import, flake8 with a huge ignore list instead of ruff, and CI
requires a self-hosted runner with access to real PDS holdings.

Issues folded into this plan: **#1434** (import code analysis), **#1435** (application code
analysis), **#383** (the exception-handling-architecture portion of its body; the "stress
testing" in its title remains open work after this rewrite), **#1082** (return 400 not 404),
**#512** (use `logging.exception`/`exc_info=True`).

**End state:** a single pip-installable distribution `rms-opus` (src-layout, setuptools-scm,
published to PyPI) where the import pipeline runs as `python -m opus_import`, the backend
runs via wsgi, and the log analyzer runs as `python -m opus_log_analyzer`; code is
ruff-clean, mypy-strict, fully docstringed; a pytest suite with parallel execution runs on
GitHub-hosted CI **without holdings access**; the existing end-to-end holdings-based
integration + golden-response API suite is retained essentially as-is on the self-hosted
runner; full Sphinx developer documentation (no user docs needed).

### Decisions made (with rfrench)

| Topic | Decision |
|---|---|
| Packaging | One distribution; `opus_support` folded in as an **internal** (non-user-visible) package |
| Distribution | **Publish to PyPI** per template flow (GitHub Release on version tag → publish workflow); servers `pip install rms-opus` |
| Config | Single **TOML** file located via **`OPUS_CONFIG` env var only** — the loader never falls back to a default path (multi-install servers each set their own) |
| Versions | **Django 5.2 LTS**, **Python ≥3.12** (CI matrix 3.12/3.13); Django 4.2 is EOL |
| obs typing | **Schema-validated annotations**: shared aliases + a CI test that cross-checks every `field_obs_*` annotation against `table_schemas/*.json` (decision table in PR-16) |
| ruff | Adopt template rule set; **do not enforce `ruff format`** (the only template check disabled — the `ruff format --check` step is *deleted* when copying the template workflow; pymarkdown and pyroma ARE adopted per template) |
| Back-compat | Public web API behavior preserved (incl. `ringobsid`, `metadata_v2`, and the `/static_media/` URL namespace); the template's "no backwards compatibility" rule is waived *for the public API only* — internal code carries no compat shims. Two sanctioned, documented API changes only: #1082's 404→400 (PR-13) and `apiguide.pdf` becoming a redirect to the ReadTheDocs API guide (PR-21) |
| API guide | The public API guide **moves into the Sphinx dev docs on ReadTheDocs** (full content parity with today's `api_guide.md`); the GUI's "API Guide" menu item opens the RTD page in a new tab instead of the in-app rendering; the in-app guide machinery (mistune rendering, `%` placeholders, `__help/apiguide.*`) is removed — see PR-21 |
| Error PR scope | **Status codes + logging only** per the decision table in PR-13; error *bodies* stay as-is (body normalization is possible later work, not this rewrite) |
| Fault injection | `OPUS_FAKE_*` delays/errors and `throw_random_*` behavior **kept but folded into the `@api_view` decorator** (fires pre-handler; see PR-13); `__fake/*` endpoints stay |
| Dictionary | Django dictionary *app* removed; `definitions`/`contexts` tables, `do_dictionary.py` import step, and a tooltip lookup helper are kept. `DICTIONARY_TERM_URL` is **dropped** from config (defined in the secrets template but consumed nowhere in the code — verified by repo-wide grep) |
| Dictionary data | `pdsdd.full` (1.8 MB) + `contexts.csv` **ship as package data** (importlib.resources) — installs are self-contained |
| log_analyzer | **Becomes a formal package in `src/`** runnable via `python -m opus_log_analyzer`; fully inside the ruff/mypy/test/docs gates |
| perf_test | Stays a top-level directory outside `src/` and **explicitly excluded from ruff/mypy/pytest scopes in pyproject (PR-01)**; the checked-in `stream_c.exe` binary is deleted |
| Coverage | GitHub-hosted unit CI: **≥90% measured over `opus_support`+`opus_config`+`opus_import`+`opus_log_analyzer` only** (`src/opus` — the Django app — is explicitly excluded from the unit gate; its coverage is owned by the integration workflow's retained **100%** gate). Two coverage configs, not one — see §5a |
| Version file | setuptools-scm `write_to = "src/opus_config/_version.py"`; every other package surfaces version at runtime via `importlib.metadata.version("rms-opus")` — no per-package `_version.py` |
| Version scheme | Release tags **continue the existing zero-padded v3.x scheme** (next release after the merge: `v3.23.00`) — a declared deviation from the template's plain-SemVer tagging rule; setuptools-scm parses these tags fine (PEP 440 normalizes `3.23.00` → `3.23.0`) |
| Django pkg name | The Django project package is importable as `opus` — accepted deliberately despite being a generic name (server venvs are dedicated to OPUS) |
| Git history | **Strict move/modify separation**: a move commit contains ONLY renames; even mechanical import rewrites land in the immediately following commit, so `git log --follow` detection is perfect. No history rewriting |
| Migrations | Django's own contrib tables (`django_session`, auth/contenttypes/admin) continue to be created by a migrate step — on pip-deployed servers this is **`django-admin migrate` with `DJANGO_SETTINGS_MODULE=opus.settings` and `OPUS_CONFIG` set** (repo-root `manage.py` is a dev convenience, not part of the wheel). OPUS tables are always created from scratch by import; OPUS-side Django migrations remain irrelevant |

### Remaining standing assumptions

- The JS/CSS frontend is untouched except for being packaged as static assets (no bundler introduced).
- `djangorestframework` moves to dev-extras. Note: `rest_framework` also sits in INSTALLED_APPS (`settings.py:142`) with a `REST_FRAMEWORK` block (146-149) until PR-09 removes both; between PR-01 and PR-09 the wheel's runtime deps alone cannot start the app — this is fine because `requirements.txt` remains the deploy mechanism until Phase F. Do **not** "fix" this by re-adding DRF to runtime deps.
- `hurry.filesize` (one call site, `cart/views.py:34`) replaced by a small local helper; `pdfkit`/`qrcode`/`pyyaml` stay; `mistune` is **dropped in PR-21** (its only consumer is the in-app API-guide renderer, which PR-21 removes).
- `manage.py` lives at repo root pointing at `opus.settings` (dev convenience); deployment remains Apache/mod_wsgi + memcached.

---

## 2. Target repository layout

```
rms-opus/
├── pyproject.toml               # single config source for project, deps, ruff, mypy, pytest, setuptools-scm, and the UNIT coverage config (integration coverage config is separate — §5a)
├── README.md, CONTRIBUTING.md, LICENSE, codecov.yml, .readthedocs.yaml
├── .cursor/{rules,skills}/      # copied from repo_template (17 rules, 4 skills)
├── .github/workflows/
│   ├── run-tests.yml            # GitHub-hosted: ruff + mypy + pymarkdown + pytest (holdings-free, MySQL service container), matrix 3.12/3.13; docs-build job added in PR-21
│   ├── run-integration.yml      # self-hosted: current end-to-end import + golden API suite (successor of run-app-tests.yml); 100% coverage gate kept
│   └── publish_to_pypi.yml, publish_to_test_pypi.yml   # template release flow
├── scripts/
│   ├── run-all-checks.sh        # from template; ENABLE_RUFF_FORMAT=false stays false
│   ├── automated_tests/…        # kept, paths updated
│   ├── import/                  # shell wrappers moved from opus/import: import_for_tests.sh, import_all.sh, _import_all_internal.sh, clone_database.sh, find_unknown_warnings.sh
│   ├── releases/                # kept (v3.x tag flow)
│   └── server/…                 # kept, updated to pip-install deploy flow (Phase F); log_analyzer cron templates land here; deploy-infrastructure env file (see PR-22)
├── src/
│   ├── opus_support/            # internal shared package (split from lib/opus_support.py: sclk.py, orbits.py, time_parsing.py, angles.py, units.py)
│   ├── opus_config/             # TOML config loader (frozen dataclasses, validation, OPUS_CONFIG env var, no default path); hosts _version.py; temporarily hosts the secrets shim (PR-03→PR-08)
│   ├── opus_import/             # from opus/import; python -m opus_import
│   │   ├── __main__.py, cli.py  # argparse surface unchanged
│   │   ├── importdb/            # MySQL only (postgresql stub + brand concept removed)
│   │   ├── obs/                 # obs_* hierarchy as a subpackage (incl. field_types.py — NOT typing.py, which would trip ruff A005 stdlib-shadow)
│   │   ├── steps/               # do_* modules; do_import.py split into ≤1000-line submodules
│   │   ├── table_schemas/*.json # package data
│   │   ├── dictionary_data/     # pdsdd.full, contexts.csv (moved from top-level dictionary/; package data)
│   │   └── util/                # schema-authoring tools incl. dump_pds_definitions.py (kept; its assert False fixed); OPUS2-era get_opus2_mults.py deleted
│   ├── opus_log_analyzer/       # from log_analyzer/; python -m opus_log_analyzer; cli.py (renamed from log_analyzer.py); Jinja templates as package data
│   └── opus/                    # Django project package
│       ├── settings.py, urls.py, wsgi.py
│       ├── apps/{search,results,metadata,ui,cart,help,paraminfo,tools}/   # dictionary app removed
│       ├── templates/, static/  # package data (directory static_media/ renamed static/; the public URL stays /static_media/ — see PR-05)
│       └── (search/models → generated models/ package, split by group)
├── tests/                       # holdings-free pytest suite (runs on GitHub CI); pytest testpaths=["tests"] — the default run is directory-scoped, not marker-filtered
│   ├── fixtures/opus_ci.toml    # checked-in dummy OPUS_CONFIG for CI lint/mypy/docs/unit jobs (PR-08)
│   ├── opus_support/            # extracted from the inline unittest classes
│   ├── opus_config/             # loader tests (written in PR-08)
│   ├── opus_import/
│   │   └── fixtures/mini_holdings/   # subsetted real PDS3 + PDS4 bundle indexes + 1-byte data stand-ins (see PR-19)
│   ├── opus_log_analyzer/       # fixture log files → report snapshots
│   └── opus/                    # Django tests that don't need a populated DB (written in PR-18)
├── integration/                 # holdings-dependent suites, kept essentially as-is; run explicitly (pytest integration), never by the default run
│   ├── .coveragerc              # the 100%-gate coverage config (see §5a)
│   ├── test_api/                # golden-response suite (411 fixtures) + api_test_helper
│   ├── apps_db_tests/           # the old per-app DB-dependent unittest files, pytest-collected
│   ├── test_db_data/, test_perf/   # moved here by PR-05
├── docs/                        # Sphinx dev guide (created in PR-21); code_of_conduct lives here per template
└── perf_test/                   # out of scope, excluded from all gates in pyproject (stream_c.exe deleted)
```

Root-file dispositions (explicit, so nothing is left to judgment): `CODING_STYLE.md` and
`CODE_REVIEW_TEMPLATE.txt` deleted, `LICENSE.md` renamed `LICENSE`, and the obsolete
`scripts/create_all_venv.sh` + `scripts/test_all_venv.sh` deleted (superseded by the CI
matrix) — all in PR-01; `CODE_OF_CONDUCT.md` moves under `docs/` per template in PR-21;
`install.md` deleted in PR-21 (content subsumed by the deployment guide);
`browserstack-logo-600x315.png` kept (README acknowledgment); `NEW_INSTRUMENT_TEMPLATE.txt`
moves to `docs/` source material in PR-04 and is deleted when PR-21 ports it; the untracked
`u28_…xml` in the working tree is local litter, not a repo change (nothing to commit).

Notes:
- `opus_support` keeps its import name (minimizes churn across its 22 importer files on both sides) but is documented as internal with no API guarantees. The 100KB single file is split by domain; its header's "100% test coverage" demand is preserved for this package.
- The import pipeline's flat modules become real subpackages with absolute imports (`from opus_import.obs.obs_base import ObsBase`); the `field_obs_<table>_<column>` getattr dispatch is unaffected by packaging.
- `opus_config` is deliberately its own tiny package because *both* `opus_import` and `opus` (Django) depend on it and neither should import the other.
- `log_analyzer` is renamed `opus_log_analyzer` on the move (avoids squatting a generic top-level import name); its existing generic-engine/OPUS-subconfig split is preserved as subpackages.
- After PR-04 and PR-05, the old top-level `opus/` directory is empty and is deleted in PR-05 (this also removes any chance of the repo-root `opus/` namespace dir shadowing the installed `opus` package when running from the repo root).

---

## 3. Configuration design (replaces `opus_secrets.py`)

One `opus.toml` (template `opus.toml.template` in repo root), path from `OPUS_CONFIG` env
var — **required; no default-path fallback** (clear startup error if unset/missing/invalid;
multi-install servers set a distinct `OPUS_CONFIG` per install in the vhost/unit/profile).
Loader in `opus_config`: frozen dataclasses per section, explicit validation, no `import *`
anywhere.

```toml
[database]      # host, schema, user, password  (DB_BRAND deleted — MySQL only)
[paths]         # pds3_holdings, pds4_holdings, logfile dirs, tar/manifest paths, notification/blog files, static_root
[django]        # secret_key, debug, allowed_hosts, cache_server_prefix, public_url, product_http_path, viewmaster_url, log levels, fake-delay/error knobs
[import]        # table_temp_prefix, log files
[dictionary]    # pdsdd/contexts paths — default to the packaged data files (term_url dropped; no consumer anywhere). The table_schemas path (DICTIONARY_JSON_SCHEMA_PATH today) gets NO TOML key — schemas are resolved via importlib.resources
```

- `opus/settings.py` reads the loaded config object (SECRET_KEY, DEBUG, ALLOWED_HOSTS,
  DATABASES, cache prefix…); everything Django-modern otherwise (BASE_DIR via
  `Path(__file__)`, lists not tuples, no deprecated settings).
- `RMS_OPUS_PATH`/`RMS_OPUS_LIB_PATH` die — package data found via `importlib.resources`.
  The one non-package-data consumer of `RMS_OPUS_PATH` is
  `apps/tools/app_utils.py:178-212 get_git_version()` (chdir + `git log` for the About
  page): PR-08 replaces its internals with `importlib.metadata.version("rms-opus")` —
  a pip-deployed server has no git checkout at all, so this is forced by the end state.
  (Verified: no golden fixture under `test_api/responses/` embeds the git value.)
- CI/deploy scripts that currently `echo` a Python secrets file generate the TOML instead;
  a checked-in `tests/fixtures/opus_ci.toml` (dummy DB creds, tmp paths) serves every
  GitHub-hosted job that must import Django settings (mypy/django-stubs, Sphinx autodoc,
  pytest-django) — see PR-08.
- The separate `apps/dictionary/secrets_template.py` is deleted.

**Transitional secrets shim (PR-03 → PR-08).** Because the sys.path inserts die before the
TOML system exists, PR-03 creates the `opus_config` package containing (initially) only
`_secrets_compat.py`: it locates `opus_secrets.py` via an `OPUS_SECRETS` env var (absolute
path to the file), falling back to the process CWD, loads it with
`importlib.util.spec_from_file_location`, and exposes its attributes. **All four direct
consumers** are rewritten against the shim: `opus_import/cli.py` (the old wildcard,
PR-04), `opus/import/import_util.py:21` (`import opus_secrets`, used at :392 for
`IMPORT_TABLE_TEMP_PREFIX` — PR-04), `opus/import/do_dictionary.py:15` (uses the three
`DICTIONARY_*` settings — PR-04), and `opus/settings.py` (wildcard, PR-05). PR-04's
definition of done includes `grep -rn "import opus_secrets" src/` returning nothing. CI
and server scripts export `OPUS_SECRETS` (and
`scripts/automated_tests/opus_import_test_database.sh` stops relying on `cd opus/import`
for secrets discovery). PR-08 replaces the shim's internals with the real TOML loader and
deletes `_secrets_compat.py`.

---

## 4. Phased PR sequence

Every PR: targets `rewrite`; keeps **both** CI workflows green — and "green" is real
because PR-01 makes both workflows trigger on `rewrite` (see PR-01). Move PRs must update
**every CI-reachable file** (workflow YAML, `scripts/automated_tests/*`,
`scripts/server/*`, `run_coverage.sh`, coverage config, `manage.py` verbs), enumerated in
each PR below — not just `scripts/automated_tests/`. Renames/moves are **pure-move PRs**
with **strict move/modify commit separation**: the move commit contains only `git mv`
renames; mechanical import rewrites and path fixes follow in the next commit(s) of the same
PR, so rename detection and `--follow` stay perfect.

### §4a — Execution protocol: one fresh sub-agent per PR

Every PR is executed by a **fresh opus-class sub-agent with no inherited conversation
context** — contexts stay clean; nothing learned in PR-N travels to PR-N+1 through
memory. Consequences and rules:

- **Input contract per sub-agent:** the checked-in plan file (this document lives in the
  `rewrite` branch as `plans/opus_modernization_plan.md`, committed at branch creation),
  the single PR number to execute, and repository access — plus, for PR-01 only, read access
  to the template repo at `/seti/all_repos/rms-devenv/repo_template` (the source of the
  copied scaffolding). Nothing else. The sub-agent reads §1–§3, §4's preamble,
  its own PR section, §4a/§5/§5a/§6, and the Execution notes appendix — it does not
  need, and must not rely on, any prior conversation.
- **All inter-PR state lives in artifacts, never in context:** the repository content,
  merged PR descriptions, and this plan file are the only carriers of state. Where a PR
  produces knowledge later PRs need (e.g. PR-19's spike outcome, PR-07's generator
  validation result, any deviation forced by reality), the executing sub-agent records it
  in a **"Execution notes" appendix at the bottom of `plans/opus_modernization_plan.md`, amended in that same PR**
  — dated, one bullet per fact, never rewriting the plan body.
- **Orchestration:** the orchestrator (human, or a supervising agent) launches the
  sub-agent for PR-N only after PR-(N-1) is merged into `rewrite` with both workflows
  green. PRs are strictly sequential; no parallel PR execution (later PRs edit files
  earlier PRs create).
- **Definition of done for a sub-agent:** an open PR against `rewrite` with both
  workflows green, a description covering what/why/testing evidence (plus the extra
  artifacts specific PRs require: PR-07's `_meta` diff, PR-13's rule-annotated fixture
  diff, PR-21's content-parity checklist), and any Execution-notes amendment. The
  sub-agent does not merge; the orchestrator reviews and merges.
- **Stop-and-report rule:** if reality contradicts the plan (a file:line claim is stale,
  a step is impossible as written, a decision table doesn't cover a case), the sub-agent
  **stops and reports the contradiction in the PR/conversation rather than improvising**
  — the plan is then amended (Execution notes or a reviewed plan-body fix) before work
  resumes. Small mechanical drift (line numbers moved, counts changed) that doesn't
  change the instruction's meaning is not a contradiction; note it and proceed.

### Phase A — Tooling bootstrap & dead code (no moves)

**PR-01: Tooling: ruff replaces flake8; pyproject + template scaffolding; CI runs on `rewrite`.**
- (`plans/opus_modernization_plan.md` — this document — the executive overview
  `plans/opus_modernization_overview.md`, and the executor guide in `CLAUDE.md` were
  committed directly to `rewrite` at branch creation, before this PR; verify they are
  present. The `plans/` directory is deleted in PR-23 when `rewrite` merges — its content
  is superseded by the dev docs and the merged PR history.)
- **First:** add `rewrite` to the `pull_request`/`push` branch filters of
  `run-app-tests.yml` (and the new `run-tests.yml`); every subsequent PR is actually
  gated. These filters are narrowed back to `main` in PR-23. **Branch-protection note:**
  `rewrite` carries the same protection as `main` (1 approval + required status checks,
  currently contexts "Run Lint" and "Test OPUS (self-hosted-linux, 3.12)"). Whenever a
  PR renames a workflow or job (this PR replaces Run Lint; PR-19/PR-20 rename the
  workflows), the required-check contexts on the `rewrite` protection must be updated to
  the new names — via `gh api -X PUT
  repos/SETI/rms-opus/branches/rewrite/protection/required_status_checks` if the
  executor's token permits, otherwise reported for the orchestrator to do.
- Add `pyproject.toml`: project metadata (name `rms-opus`, `requires-python >=3.12`,
  dynamic version via setuptools-scm with `write_to = "src/opus_config/_version.py"` —
  directory created then, harmless until PR-03 populates it), runtime deps lifted from
  `requirements.in` (django upgrade deferred to PR-09 — start with `django>=4.2,<5` to
  keep working), dev extras (incl. `pytest-django`, `pytest-xdist`, `pytest-cov`,
  `djangorestframework`) and docs extras; `[tool.ruff]` per template (line 100, py312
  target, select E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF) with `perf_test/` in `exclude`;
  `[tool.pytest.ini_options]` (`testpaths=["tests"]`), `[tool.coverage]` (unit scope only
  — §5a), mypy section present but not yet enforced (also excluding `perf_test/`).
- Copy from the template repo (`/seti/all_repos/rms-devenv/repo_template` on the RMS
  development machines): `.cursor/rules` (17 files) + `.cursor/skills`, `.vscode`/`.cursor` settings,
  `codecov.yml`, `.readthedocs.yaml`, `scripts/run-all-checks.sh` (ENABLE_RUFF_FORMAT
  stays false; ENABLE_MYPY flips true in Phase D; pymarkdown + pyroma enabled per
  template defaults — but until PR-21 creates `docs/`, the pymarkdown scan list and the
  Sphinx step are limited to what exists: `README.md CONTRIBUTING.md .cursor/`),
  `CONTRIBUTING.md`, PR/issue templates, publish workflows from repo_template. **When
  adapting the template `run-tests.yml`, delete its `ruff format --check` step** (the
  declared deviation). Delete `CODING_STYLE.md`, `CODE_REVIEW_TEMPLATE.txt`,
  `scripts/create_all_venv.sh`, `scripts/test_all_venv.sh`; rename `LICENSE.md` → `LICENSE`.
- Replace `.flake8` + `run_flake8.sh` + `run-lint.yml` with ruff in the new `run-tests.yml`
  (lint job only for now). Bring the codebase to `ruff check` clean. **Burn-down
  discipline:** the `[tool.ruff.lint.per-file-ignores]` table in pyproject *is* the
  burn-down list; PR-01 may seed it **only** with codes E722, F403, F405, N8xx, E501
  (today's flake8 ignores that need real refactoring); every other failing code must be
  fixed in PR-01 itself (import sorting, `.find()`→`in`, comprehensions, etc.). PR-17's
  exit criterion is that this table is empty. Ruff scope includes `log_analyzer/`.
- requirements.in/txt stay temporarily as the deploy mechanism until Phase F.

**PR-02: Dead code removal & bug fixes.**
- Delete `importdb/postgresql.py`; remove the brand concept end-to-end: `get_db()` loses
  `db_brand`; `DB_BRAND` removed from `opus_secrets_template.py:12`,
  `scripts/automated_tests/opus_setup_environment.sh:41`,
  `scripts/server/import_and_deploy/_opus_setup_environment.sh:31`, and the call site
  `main_opus_import.py:442`.
- **Shelf-requirement fix (prerequisite for PR-19's holdings-free CI):** move the
  unconditional `Pds3File.require_shelves(True)` (`main_opus_import.py:423`) *inside* the
  `if not impglobals.ARGUMENTS.dont_use_shelves_only:` block at :419. Rationale: with
  `--dont-use-shelves-only` the import is meant to run from the real filesystem, but
  `require_shelves(True)` still makes pdsfile raise on any missing shelf (hit via
  `file.size_bytes` on every product, `do_import.py:1591`); the PDS4 equivalents were
  already commented out in commit 1e11d994. Behavior without the flag is unchanged.
  Integration CI (which uses shelves) gates the change.
- Remove dead code catalogued in #1434/#1435: dictionary app's commented-out
  views/urls/admin (app removal itself is PR-09), `instruments.py` commented hooks,
  `obs_volume_covims_0xxx.py` code after return, `obs_volume_cassini_occ_common.py`
  commented block, OPUS2-era `util/get_opus2_mults.py` (deleted; `util/dump_pds_definitions.py`
  is **kept** as a schema-authoring tool with its `assert False` replaced by a real error),
  stale `install.md` refs to `requirements-python3.txt`, `perf_test/stream_c.exe`.
- Fix known bugs from #1434: `importdb/super.py:113` `showarning` typo;
  `obs_volume_hstjx_xxxx.py` unbound `wr/bw` (else-branch at ~91 before `bw // wr`);
  `obs_volume_hstox_xxxx.py` `wr1 > wr2` None comparison (~63-72). (The
  `obs_profile_pds4.py` missing-return reported in #1434 is already fixed in the current
  tree — verify and do not hunt for it.) Bare `except:` → `except Exception`; pointless
  `except: raise` removed; `assert False` → `NotImplementedError`; mutable default arg in
  `ImportDBSuper.__init__` fixed.
- Replace `from config_data import *` with explicit imports (the opus_secrets wildcard
  fully dies in PR-08).

### Phase B — Restructure (each move its own PR)

**PR-03: Move `lib/opus_support.py` → `src/opus_support/` package; create `opus_config` shim; pytest job goes live.**
- Split by domain (sclk/orbits/time/angles/units), `__init__.py` re-exports the full
  public surface so both sides keep `from opus_support import parse_form_type` working.
- Extract the inline `unittest` classes to `tests/opus_support/` (converted to pytest —
  first beachhead of the new suite). Create `src/opus_config/` with `_secrets_compat.py`
  (§3) ready for PR-04/05. Packaging glue so `pip install -e .` provides both packages;
  delete the `RMS_OPUS_LIB_PATH` sys.path inserts on both sides.
- **Integration workflow kept green — explicit edits (the blanket clause is not enough):**
  (i) `run-app-tests.yml` gains `pip install -e .` after the requirements install;
  (ii) `opus/application/run_coverage.sh` line `coverage run ../../lib/opus_support.py`
  becomes `coverage run -a -m pytest ../../tests/opus_support` (path relative to its CWD);
  (iii) `opus/application/.coveragerc` include pattern `*/opus_support.py` becomes
  `*/src/opus_support/*` (the `src/` prefix matters — a bare `*/opus_support/*` would also
  pull `tests/opus_support/*` into the 100% integration gate).
- **GitHub workflow:** `run-tests.yml` gains its pytest job now (no MySQL needed yet),
  running `pytest` (= `tests/`) with `-n auto` on the 3.12/3.13 matrix — every subsequent
  PR is unit-tested in CI, not only via local run-all-checks.

**PR-04: Move `opus/import/` → `src/opus_import/` package.**
- Pure move: `cli.py` (from `main_opus_import.py`) + `__main__.py`; subpackages `obs/`,
  `steps/`, `importdb/`; `table_schemas/` and the top-level `dictionary/` data files become
  package data (`opus_import/dictionary_data/`) resolved via `importlib.resources`;
  absolute imports throughout; the three sys.path inserts deleted — secrets now via the
  `opus_config._secrets_compat` shim + `OPUS_SECRETS` env var, rewritten in **all three**
  import-side consumers (`cli.py`, `import_util.py:21`, `do_dictionary.py:15`; done-check:
  `grep -rn "import opus_secrets" src/` empty — see §3).
- Shell wrappers (`import_for_tests.sh`, `import_all.sh`, `_import_all_internal.sh`,
  `clone_database.sh`, `find_unknown_warnings.sh`) move to `scripts/import/` (never into
  the installed package); `NEW_INSTRUMENT_TEMPLATE.txt` moves to `docs/` source material.
- CI-reachable updates: `scripts/import/import_for_tests.sh`,
  `scripts/automated_tests/opus_import_test_database.sh` (export `OPUS_SECRETS`; stop
  depending on `cd opus/import` for discovery), server import scripts — all invoke
  `python -m opus_import`.

**PR-05: Move `opus/application/` → `src/opus/` Django package.**
- `settings.py`/`urls.py` into the package; real `wsgi.py` committed (`opus.wsgi_template`
  deleted — note the memcache probe already lives in `settings.py:4-21` and simply moves
  with it); repo-root `manage.py` with `DJANGO_SETTINGS_MODULE=opus.settings`; apps become
  `opus.apps.*` (INSTALLED_APPS, ROOT_URLCONF, all cross-app imports rewritten from bare
  names; `import settings` → `from django.conf import settings` everywhere); templates
  DIRS from BASE_DIR (stale `quide` path dropped). Secrets via the shim. The emptied
  top-level `opus/` directory is deleted. **This PR is executed as a single PR** — the
  strict move/modify commit separation is what makes it reviewable (review the rename
  commit and the rewrite commit independently); there is no per-app fallback (a partial
  split would require both import roots resolvable simultaneously, i.e. new sys.path
  shims, which this plan bans).
- **Static files:** directory `static_media/` → `src/opus/static/`, but
  `STATIC_URL = '/static_media/'` and the `OPUS_STATIC_ROOT`/Apache alias semantics are
  **unchanged, permanently** — the URL namespace is public surface (hardcoded in
  `opus.js:1120`, embedded in golden HTML fixtures, aliased in production Apache). Zero
  golden-fixture diffs expected from this PR.
- test_api + per-app DB tests **+ `test_db_data/` + `test_perf/`** move to `integration/`
  (with `__init__.py` files so unittest discovery keeps working). URL patterns byte-identical.
- **Integration invocation between this PR and PR-18 — explicit spec:**
  `run_coverage.sh` moves to repo root (invoked from root); the integration coverage
  config becomes `integration/.coveragerc` (see §5a) with includes updated to
  `src/opus/apps/*`, `integration/test_api/*`, `src/opus_support/*`; `manage.py` custom
  verbs (`api-all` etc.) keep working with their label mappings updated to
  `integration.test_api`; Django test discovery runs from repo root (`manage.py test
  integration`); `opus_run_unittests_coverage.sh` and `opus_check_coverage.sh` drop their
  `cd opus/application` and use repo root; `run-app-tests.yml` codecov upload path becomes
  `./coverage.xml`.

**PR-06: Move `log_analyzer/` → `src/opus_log_analyzer/` package.**
- Rename on move; **`log_analyzer.py` is renamed `cli.py` in the move commit** (its
  existing `main()` becomes the entry point); `__main__.py` calls `cli.main()`; generic
  engine and OPUS-specific `opus/` config become subpackages; Jinja `templates/` as
  package data; `server/` cron templates relocate to `scripts/server/` **and are rewritten
  to invoke `python -m opus_log_analyzer`**; its private `mypy.ini` deleted (config
  consolidates into pyproject in Phase D).
- **Config-module default fix:** `cli.py`'s `--configuration` default is the string
  `'opus.configuration'` resolved via `importlib.import_module` (`log_analyzer.py:80,109`)
  — after PR-05 that resolves to the installed *Django* package and breaks. The default
  becomes `'opus_log_analyzer.opus.configuration'`, and a unit test asserts the default
  module imports and exposes `Configuration`.

**PR-07: Split the checked-in `search/models.py` into a package; update the generator.**
- The checked-in 700KB `models.py` is **restructured by hand/script** (no live DB needed)
  into `opus/apps/search/models/` split by table group (obs tables, mult tables,
  partables/param_info/etc.); duplicate `ZZDefinitions`/`ZZContexts` mappings dropped.
- **Verification (two-process, because Django's app registry loads once):** a small
  script dumps every model's `_meta` (db_table, column names, field class names,
  null/key attributes) to JSON; run it once on the pre-split commit and once on the
  post-split tree; diff the two JSON files — must be identical except the deleted ZZ
  duplicates. No database connection involved.
- `create_opus_models.sh` (a `manage.py inspectdb` + sed pipeline requiring a live
  imported DB) is updated to emit the new package layout; since regeneration needs the
  self-hosted environment, the generator change is validated by running it during the
  next integration-CI import run and diffing against the checked-in package. PR-09
  re-runs the `_meta` JSON diff after the Django 5.2 upgrade (inspectdb output is
  version-dependent).

**PR-08: Configuration: TOML + `opus_config` (design in §3).**
- Implement the real loader in `opus_config` **with its unit tests in
  `tests/opus_config/`** (they gate the riskiest cutover in the plan); rewrite
  consumption in `opus_import.cli`, `opus/settings.py`, `do_dictionary`; delete
  `_secrets_compat.py`, `opus_secrets_template.py`, `apps/dictionary/secrets_template.py`,
  and every remaining `opus_secrets`/`OPUS_SECRETS` reference;
  `scripts/automated_tests/opus_setup_environment.sh` and the server
  `_opus_setup_environment.sh` emit `opus.toml` and export `OPUS_CONFIG`.
- **Check in `tests/fixtures/opus_ci.toml`** (dummy DB creds, tmp-dir paths): the standing
  config for every GitHub-hosted job that must import `opus.settings` — mypy/django-stubs
  (PR-14 on), pytest-django collection of `tests/opus` (PR-18 on), Sphinx autodoc (PR-21).
  `run-all-checks.sh` and the workflow jobs export `OPUS_CONFIG=tests/fixtures/opus_ci.toml`
  from this PR forward.
- Replace `get_git_version()` internals (`apps/tools/app_utils.py:178-212`) with
  `importlib.metadata.version("rms-opus")` — see §3.
- (Note: `scripts/server/import_and_deploy/_read_opus_secrets.sh` sources a *shell-format*
  env file distinct from the Python secrets — the shell deploy chain keeps its own env
  file for script-level variables (dirs, hosts); only app config moves to TOML. The
  deploy-chain rewrite is PR-22; this PR just keeps it working.) Wildcard F403/F405
  per-file-ignores from PR-01 are now removable. After this PR,
  `grep -rn "sys.path" --include="*.py" src/` must return nothing (the actual inserts
  already died in PR-04/PR-05; this is the standing invariant, not new work).

### Phase C — Framework & code modernization

**PR-09: Django 5.2 upgrade + settings/app cleanup.**
- `django>=5.2,<6`; fix deprecations; remove `ADMIN_MEDIA_PREFIX`, `USE_L10N`, `REUSE_DB`
  env hack, `SITE_ID`/`contrib.sites`, `contrib.admindocs`, DRF from INSTALLED_APPS
  (`settings.py:142`) and the `REST_FRAMEWORK` block (dep already in dev extras),
  debug-toolbar remnants; MIDDLEWARE/INSTALLED_APPS as lists; the
  `multilines_template_tags` tag_re monkeypatch is **kept, with a comment pinning the
  Django version it was verified against** (verify against 5.2 as part of this PR).
  The migrate step (contrib tables) remains documented and unchanged.
- **Remove the dictionary app**: `Definitions`/`Contexts` models + `get_def_for_tooltip()`
  move to `opus/apps/tools/dictionary.py` (imports updated in paraminfo/ui/cart);
  dictionary urls/templates/statics deleted; `do_dictionary.py` import step untouched.
- `hurry.filesize` call replaced by a local helper. Re-run the PR-07 `_meta` JSON diff under 5.2.

**PR-10: Import pipeline internal cleanup.**
- Split `do_import.py` (1,782 lines) into `steps/` submodules (table prep, mult handling,
  one-index import, observation-table import, main loop) and `config_targets.py` (1,003
  lines — over the limit, split mandatory) by section — all ≤1000 lines.
- Consolidate the ~18 duplicated SCLK try/except blocks into one helper on the mission
  common classes; named constants for magic numbers (wavenumber conversion, angles,
  detector sizes); typo fixes; `NoDupLogger` lists → sets; batch `upsert_rows`.

**PR-11: Replace `impglobals` with an `ImportContext`.**
- Dataclass carrying `db`, `logger`, `args`, and current-state fields; constructed in
  `cli.py`, threaded through `steps/*` and the obs hierarchy (obs classes already receive
  constructor args — context becomes one of them). Executed as **one PR** (no conditional
  split); mechanical but wide; no behavior change (verified by integration CI).
- **Threading pattern (fixed, not executor-designed):** (i) obs classes store the context
  (`self._ctx`) and their `_log_nonrepeating_*` wrappers route through it; (ii) free
  functions in `import_util` (the `log_*`/`log_nonrepeating_*` family and anything reading
  `impglobals.DATABASE/LOGGER/ARGUMENTS`) gain an explicit `ctx` first parameter;
  (iii) `do_import`'s three module-level caches (`_MULT_TABLE_CACHE`,
  `_CREATED_IMP_MULT_TABLES`, `_MODIFIED_MULT_TABLES`) become context fields.
  Worked example (the shape every site follows) — before, `obs_cassini_common.py`:
  `import_util.log_nonrepeating_error(msg)` → after:
  `self._ctx.log.nonrepeating_error(msg)` (obs methods) or
  `import_util.log_nonrepeating_error(ctx, msg)` (step functions).

**PR-12: SQL consistency.**
- One documented convention + small helper module per side:
  `opus/apps/tools/sql_builder.py` (identifier quoting via `connection.ops.quote_name`,
  composable SELECT/JOIN/WHERE assembly, `%s` params for all values). Scope is
  **grep-defined**: every call site under `src/opus/apps/**` that *assembles* SQL from
  strings is refactored through the builder. The five worst files by volume are
  `search/views.py`, `results/views.py`, `cart/views.py` (which alone has ~15 additional
  sites beyond its big `_get_download_info` region), `metadata/views.py`,
  `tools/file_utils.py` — but the grep, not this list, defines the work.
- **Acceptance (mechanical):** cursor acquisition and `cursor.execute(...)` may remain at
  call sites; constant literal statements with only `%s` placeholders (e.g.
  `search/views.py:1519`) are exempt. The criterion is that no site outside
  `sql_builder.py` builds SQL by string concatenation or interpolation:
  `grep -nE "sql \+=|sql = .* \+ |f['\"].*(SELECT|INSERT|UPDATE|DELETE|CREATE)" -r src/opus/apps --include='*.py'`
  (excluding `sql_builder.py`) returns nothing.
- `importdb/mysql.py` aligned to the same style (backtick-quoted identifiers validated
  against `^[A-Za-z0-9_]+$`, values always parameterized). Golden-response outputs must be
  byte-identical (SQL result ordering preserved).

**PR-13: API error handling & logging (#383, #1082, #512).**
- An `@api_view` decorator replaces the manual `enter_api_call`/`exit_api_call` pairs;
  the fault-injection machinery (`OPUS_FAKE_API_DELAYS`, random 404/500 probabilities)
  moves out of every handler body into the same decorator, driven by the same config
  knobs (`__fake/*` endpoints stay). **Injection now fires pre-handler** (today it fires
  at ~103 interior points); endpoint-visible behavior is equivalent, and any test that
  asserted injection interacting with handler-interior state is updated under this PR's
  sanctioned fixture regeneration.
- **400-vs-404 decision table (the rule set; no per-endpoint judgment):**
  1. Identifier in the URL *path* naming a resource (e.g. `api/metadata/<opus_id>`) that
     doesn't exist → **404** (unchanged).
  2. Anything arriving via query string or POST body that is malformed, unknown, or
     invalid — bad/unknown slugs (incl. in `?cols=`/`?order=`/widgets), non-numeric
     `limit`/`startobs`/`page`, invalid units/qtypes, missing required params, **and
     unknown opus_ids passed as parameters** (e.g. cart add/remove) → **400** (changed
     from 404).
  3. `ringobsid` conversion failure (`app_utils.py:310`) → **404** (unchanged — it stands
     in for a path identifier in compat URLs).
  4. Fault-injected errors keep today's codes (404/500 per the config knobs).
  5. Unexpected exceptions → **500** + `logger.exception`/`exc_info=True` (repo-wide
     logging audit; #512).
- **Scope limit:** status codes and logging only — error response *bodies* stay as they
  are today. **Verification procedure:** regenerate the affected golden fixtures and
  produce a per-endpoint diff report in the PR description listing every status-code
  change annotated with the table rule (1–5) that mandates it; any change not traceable
  to a rule is a bug. Update the API guide (`api_guide.md` — still in-app at this point;
  it migrates to RTD in PR-21). This is the first of the two sanctioned public-API
  changes (the other is PR-21's `apiguide.pdf` redirect).

### Phase D — Types & docstrings (mypy strict at the end)

**PR-14: mypy infra; annotate `opus_support` + `opus_config`.** django-stubs added
(requires `OPUS_CONFIG=tests/fixtures/opus_ci.toml` in the lint job and run-all-checks —
wired in PR-08); `[tool.mypy] strict=true` with temporary per-module `ignore_errors`
overrides for not-yet-annotated packages (burn-down list; no global exclusions per the
rules). Google-style docstrings (`Parameters:`) for everything annotated. ENABLE_MYPY
flips true in run-all-checks + CI. `opus_log_analyzer`'s existing partial typing (it had
its own mypy.ini) is folded into the same strict config.

**PR-15: Annotate `opus_import` core** (importdb, import_util, steps/, cli) + docstrings.

**PR-16: obs hierarchy: schema-validated annotations.**
- Aliases live in `opus_import/obs/field_types.py` (not `typing.py` — ruff A005
  stdlib-shadow). `MultField` is a `TypedDict` matching `ObsBase._create_mult()`
  (`obs_base.py:349-367`) with value types: `col_val: str | None`, `disp: str`,
  `disp_name: str | None`, `disp_order: int | str | None`, `grouping: str | None`,
  `group_disp_order: int | None`, `tooltip: str | None`, `aliases: str | None` (note:
  the *post-`json.dumps`* string, `obs_base.py:359`).
- **field_type → alias decision table (exhaustive; no executor judgment):**
  | schema `field_type` | annotation |
  |---|---|
  | `char*` / `varchar*` / `text` | `StrField = str | None` |
  | `real4` / `real8` | `FloatField = float | None` |
  | `int*` / `uint*` | `IntField = int | None` |
  | `flag_yesno` / `flag_onoff` | `FlagField = str | int | None` (normalized at `do_import.py:1294-1310`) |
  | `mult_idx` (GROUP/MULTIGROUP form types) | `MultFieldRet = MultField | list[MultField]` |
  | `mult_list` | `list[MultField]` |
  Mult-column functions currently may also return *bare values* (permitted by
  `do_import.py:1236-1253`): as part of this PR those (and only those) are **normalized to
  return `_create_mult(...)` dicts**, in a separate commit, gated by the integration
  suite — so the table above holds without unions-with-bare-values.
- **CI test (two layers):** (1) walk every obs class, resolve each
  `field_obs_<table>_<column>` against the JSON schema (replicating the pipeline's
  surface-geometry table-name normalization, `do_import.py:1454-1456`), and assert the
  annotation equals the table's alias; (2) **behavioral smoke:** call the field functions
  of at least one instrument class per mission against fixture metadata dicts and assert
  each returned value's runtime type matches its annotation (this pulls a small slice of
  PR-19's fixture-driven layer forward, so annotations are checked against behavior, not
  only schema). Docstrings across the hierarchy; MRO documented (feeds the dev-guide
  Mermaid diagram).

**PR-17: Annotate the Django side + `opus_log_analyzer`** (tools, then app views/models
with django-stubs; `HttpRequest`→`HttpResponse` signatures; log-analyzer engine and OPUS
config classes). Remove every temporary mypy override — repo is mypy-strict clean. The
`[tool.ruff.lint.per-file-ignores]` table is emptied (PR-01's exit criterion).

### Phase E — Test suite

**PR-18: pytest everywhere.**
- **Selection model:** the default run is directory-scoped (`testpaths=["tests"]`), so
  `pytest` alone never touches `integration/`; markers `integration`, `holdings`,
  `livetest` are registered (strict-markers) and used to select *within* an explicit
  `pytest integration` invocation. No `-m` filter in addopts.
- **Django under pytest:** `pytest-django` with `DJANGO_SETTINGS_MODULE=opus.settings`
  and `OPUS_CONFIG` (CI fixture TOML for `tests/`, real TOML for `integration/`).
  **DB-lifecycle rule (fixed, not executor-chosen):** integration tests **remain
  `unittest.TestCase` subclasses** (pytest collects them natively and pytest-django does
  not manage the DB for them), preserving today's deliberate no-create/no-teardown
  behavior against the live imported schema; an autouse session fixture in
  `integration/conftest.py` uses `django_db_blocker.unblock()` for the session.
  **`@pytest.mark.django_db` is forbidden in `integration/`** (it would wrap tests in
  transactions or, with `transaction=True`, flush the freshly imported schema) — a
  conftest collection hook asserts no integration test carries it.
- `tests/opus/` (holdings-free Django unit tests — request parsing, pure helpers,
  decorator behavior with mocked handlers) is written in this PR.
- `manage.py` custom test verbs replaced by pytest invocations + a small conftest that
  reads `TEST_GO_LIVE`-style env config; `run_coverage.sh` deleted in favor of pytest-cov
  invocations (§5a). xdist: unit suite `-n auto --dist loadscope`; integration suite runs
  serially (DB/cache-table mutation — e.g. `results/test_results.py:37` drops cache
  tables — is not parallel-safe; revisit later).
- **Integration coverage scope preserved:** the integration coverage invocation runs
  `pytest tests/opus_support integration` as a single combined coverage run (today
  `run_coverage.sh` runs the opus_support tests inside the integration coverage; dropping
  them would silently deflate the 100% gate).

**PR-19: Holdings-free import test suite (the new CI centerpiece).**
- **Fixture strategy — subset, don't synthesize** (this is the load-bearing decision that
  keeps the task opus-class):
  1. PDS3: copy the real `holdings/metadata/COISS_2xxx/COISS_2002/` index, supplemental
     index, ring/moon summary, and inventory `.tab`/`.lbl` files (COISS_2002 is already in
     the `import_for_tests.sh` bundle list); truncate each `.tab` to its first N rows
     (one coherent observation set); edit **only** the `ROWS` and `FILE_RECORDS` keywords
     in each `.lbl` to match. PDS4: same subsetting for `uranus_occ_u0_kao_91cm`
     (`.csv` index + `.xml` label; fix the `<records>` counts).
  2. Every data file named by the surviving index rows exists as a **1-byte stand-in**
     (never 0 bytes — `do_import.py:1624-1626` errors on zero size) at its exact path
     under `holdings/volumes/COISS_2xxx/COISS_2002/…` (and the PDS4 equivalent). Data
     files are only stat'd, never parsed.
  3. Shelves are not needed: PR-02 moved `require_shelves(True)` under the
     `--dont-use-shelves-only` guard, so with the flag pdsfile falls back to `os.stat`.
  4. **Spike success criterion (mechanical):** `OPUS_CONFIG=<fixture toml> python -m
     opus_import --dont-use-shelves-only --do-all-import COISS_2002` against the CI MySQL
     container exits 0 with an empty ERRORS.log and `obs_general` row count == N.
     Warnings (missing previews/calibrated products) are acceptable. The asserted table
     contents come from the first successful run, reviewed once, then frozen as expected
     fixtures.
  5. **Bounded fallback:** only if step 4 fails *inside pdsfile's directory-acceptance
     logic* after a time-boxed spike (≤2 days of effort) does the suite switch to the
     pre-specified `FakePds3File` at the pdsfile boundary — methods: `from_path`,
     `from_filespec`, `from_opus_id`, `associated_abspaths`, `opus_products`, `abspath`,
     `exists`, `childnames`, **`size_bytes`, `is_local`** — with real-file parsing tested
     at the `pdstable` seam.
- CI runs a **MySQL 8 service container**; the end-to-end fixture import (incl. mult
  tables, aux tables, and the dictionary step with a trimmed pdsdd fixture) asserts on
  resulting table contents.
- Plus fast pure-unit layers: `import_util` helpers, `config_targets` lookups,
  `importdb.mysql` SQL generation (against the service DB), the full obs-field-method
  fixture layer (extending PR-16's per-mission smoke to all instrument classes).
- `opus_log_analyzer` tests: checked-in fixture Apache logs → expected report snapshots.
- `run-tests.yml` final form for this phase: ruff + mypy + pymarkdown
  (README/CONTRIBUTING/.cursor — `docs/` joins in PR-21) + pytest matrix (3.12/3.13) with
  codecov upload, all on `ubuntu-latest`. **Coverage gate: ≥90% via
  `--cov=opus_support --cov=opus_config --cov=opus_import --cov=opus_log_analyzer`**
  (`src/opus` excluded — owned by the integration 100% gate).

**PR-20: Integration workflow consolidation.**
- `run-integration.yml` (successor of `run-app-tests.yml`): unchanged philosophy —
  self-hosted runner, real holdings, fresh `opus_test_db_<id>`,
  `scripts/import/import_for_tests.sh` bundle list, golden-response API suite,
  DB-integrity checks, **100% coverage gate kept with its current scope** (via
  `integration/.coveragerc`, §5a, including the `tests/opus_support` contribution per
  PR-18) — invoked through pytest and the TOML config. Nightly cron + on-demand; PRs run
  it too (as today; still triggering on `rewrite` until PR-23).

### Phase F — Documentation & packaging finalization

**PR-21: Developer documentation (Sphinx, per doc_dev_guide.mdc).**
- Create `docs/`: intro; annotated repository layout; environment setup (editable
  install, TOML config, running import + backend + log analyzer + tests + checks);
  architecture chapters with Mermaid diagrams (obs class hierarchy/MRO, import pipeline
  dataflow: holdings → pdsfile → index rows → field functions → import tables → perm
  tables → aux tables; Django request flow; table_schemas JSON reference — port
  `table_schemas/README.md`, `docs/database_schema.md`, `opus_id_format.md`,
  `adding_an_instrument_or_mission.md`, `NEW_INSTRUMENT_TEMPLATE.txt`; **ported sources
  are deleted at their old locations in this PR**); extending recipes; deployment guide
  (wsgi/Apache, memcached, `django-admin migrate` for Django contrib tables, import
  runbook, log-analyzer cron — replaces `install.md`, deleted here); autodoc API
  reference (needs `OPUS_CONFIG=tests/fixtures/opus_ci.toml` + `django.setup()` in
  `conf.py` for the `opus.*` modules). `CODE_OF_CONDUCT.md` moves under `docs/`. Builds
  clean under `-W` and `-n`. **ReadTheDocs timing:** the RTD project is created by the
  orchestrator (rfrench) *after* this PR's docs build clean — the sub-agent commits
  `.readthedocs.yaml` and the RTD URLs (GUI link, `apiguide.pdf` redirect target) but
  must not stall on the RTD site being live; it becomes live before PR-22's acceptance
  run exercises the redirect.
- **API guide migration (full content parity, second sanctioned API change):**
  - Port `apps/help/api_guide.md` into the dev guide as a "Public Web API" chapter set.
    **Content-parity acceptance:** every section of the source markdown appears in the
    ported guide (checklist of its headings in the PR description); every documented
    endpoint, parameter, example, and return-format description is preserved — the port
    reformats (proper Sphinx sections, cross-references, code blocks), it does not trim.
    Placeholder handling: `%HOST%` → the literal production URL
    (`https://opus.pds-rings.seti.org`); `%VERSION%`/`%DATE%` → Sphinx version/date;
    `%EXTLINK%`/`%CODE%`/`%ADDCLASS%` Bootstrap-injection markup → native Sphinx/MyST
    formatting.
  - The guide's dynamic **field tables** (today built at render time from
    `get_fields_info()`/the param_info DB) are produced by a build-time generator script
    that reads `table_schemas/*.json` directly (the same `pi_*` metadata `do_param_info`
    uses) — no database needed, so the RTD build stays holdings-free. The generator runs
    from `conf.py` at build time; a unit test asserts it runs clean against the packaged
    schemas.
  - **GUI change:** the "API Guide" dropdown item (`ui/templates/ui/base.html:68`,
    `data-action="apiguide"`) becomes a plain external link opening the RTD API guide in
    a new tab; the `apiguide` case in `opus.js:1038-1040` is removed. The RTD base URL is
    a Django settings constant.
  - **Endpoints:** `__help/apiguide.(html|pdf)` (internal) removed; the public
    `apiguide.pdf` route returns an HTTP 302 to the RTD guide (documented as the second
    sanctioned public-API change). The `api_api_guide` view, its templates
    (`apiguide.html`, `apiguide_print.html`), `api_guide.css`, and the `%`-placeholder
    machinery are deleted; the `mistune` dependency is dropped (sole consumer). `pdfkit`
    stays (other help PDFs).
  - **Fixtures/tests:** delete the `api_help_apiguide.html` golden fixture and its tests
    in `integration/test_api/test_help_api.py`; add a test asserting the 302 and its
    Location target.
- **CI:** `run-tests.yml` gains the docs-build job NOW (not earlier — `docs/` did not
  exist before this PR); pymarkdown scope and `run-all-checks.sh` extend to `docs/`.
- README rewritten per the structure mandated by `.cursor/rules/doc_readme.mdc` (in the
  repo since PR-01): Title, grouped badges, Introduction, Features, Installation, Quick
  Start, Documentation, Contributing, License, with the `<!-- start-after-point -->`
  marker for Sphinx inclusion; BrowserStack acknowledgment kept. (No template-repo access
  needed — the copied rule file is the specification.)

**PR-22: Packaging finalization & deploy flow.**
- Console scripts `opus-import = opus_import.cli:main` and
  `opus-log-analyzer = opus_log_analyzer.cli:main` (module created by PR-06) alongside the
  `python -m` forms; package data audit (table_schemas, templates, static, help md/yaml,
  pdsdd.full, contexts.csv, Jinja templates, `py.typed` markers); `requirements.in/txt`
  deleted (deps live in pyproject; deploy pins via a `constraints.txt` generated at
  release if ops wants one).
- `scripts/server/import_and_deploy/*` rewritten for the pip flow: venv + `pip install
  rms-opus` (PyPI), `opus.toml` in place with `OPUS_CONFIG` set per install,
  **`django-admin migrate`** (Django contrib tables; `DJANGO_SETTINGS_MODULE=opus.settings`),
  `collectstatic`, Apache mod_wsgi pointing at installed `opus.wsgi`. The
  shell-script-level variables currently sourced from `_read_opus_secrets.sh` move to an
  explicit `deploy.env` consumed only by the shell chain (documented as deploy
  infrastructure, distinct from app config).
- PyPI publishing live: version tag on `main` → GitHub Release → `publish_to_pypi.yml`
  (first release cut after the merge PR); Test PyPI dry-run from the rewrite branch first.
  (PyPI ownership of the `rms-opus` name and the `PYPI_API_TOKEN`/`TEST_PYPI_API_TOKEN`
  repo secrets are confirmed in place — no verification step needed.)
- **Final acceptance test** (see §6) on a clean machine/venv.

**PR-23: Merge `rewrite` → `main`** after a full integration run, a production-style
deploy rehearsal, and a final `run-all-checks.sh` pass. Workflow branch filters narrowed
back to `main`. First release tag (`v3.23.00`, continuing the existing scheme) and PyPI
publish follow.

---

## 5. CI evolution timeline

| Stage | GitHub-hosted | Self-hosted |
|---|---|---|
| Today | flake8 only (main-only triggers) | full import + Django tests (holdings, 100% gate; main-only triggers) |
| After PR-01 | ruff; **both workflows trigger on `rewrite`** | unchanged behavior, now gating rewrite PRs |
| After PR-03 | ruff + pytest (`tests/`, no DB) | green via explicit run_coverage.sh/.coveragerc/pip-install-e fixes |
| After PR-08 | + `OPUS_CONFIG=tests/fixtures/opus_ci.toml` available to all jobs | secrets → TOML |
| After PR-19 | ruff + mypy + pymarkdown + holdings-free pytest w/ MySQL container; 90% gate over the four non-Django packages | unchanged |
| After PR-20 | same | pytest-driven integration, 100% gate kept |
| After PR-21 | + Sphinx docs-build job; pymarkdown covers `docs/` | same |

The self-hosted workflow must stay green on **every** rewrite PR — it is the safety net
proving behavior preservation while structure churns underneath.

### §5a — The two coverage configurations (they must not share one config)

coverage.py ignores `include` when `source`/`--cov` is set, so a single merged config
would silently corrupt one gate or the other. Therefore:
- **Unit config** lives in `[tool.coverage.*]` in pyproject: shared `report`/
  `exclude_lines` options + the unit run's settings; invoked as
  `pytest --cov=opus_support --cov=opus_config --cov=opus_import --cov=opus_log_analyzer`;
  gate ≥90% (codecov + `fail_under`).
- **Integration config** lives in `integration/.coveragerc` (activated via
  `COVERAGE_RCFILE=integration/.coveragerc` in the self-hosted workflow): the include
  list `src/opus/apps/*`, `integration/test_api/*`, `src/opus_support/*` (migrated from
  today's `opus/application/.coveragerc` in PR-05); gate 100% via `opus_check_coverage.sh`.

---

## 6. Verification

Per-PR: `scripts/run-all-checks.sh` locally; both workflows green; move-PRs verified by
integration suite passing with zero golden-fixture diffs (except the sanctioned ones:
PR-13's status-code changes, each traceable to its decision table, and PR-21's API-guide
fixture removal + redirect).

End-to-end acceptance (PR-22/23, on a clean venv, no repo checkout on path):
1. `pip install <built wheel>`; `OPUS_CONFIG=/path/to/opus.toml python -m opus_import --do-it-all <test bundles>` against a fresh MySQL schema → zero ERRORS.log entries; `--validate-perm` clean.
2. `python -m opus_import --help` surface identical to the old CLI (documented diff otherwise).
3. `django-admin migrate` (`DJANGO_SETTINGS_MODULE=opus.settings`) + serve `opus.wsgi` (mod_wsgi or gunicorn smoke run) against that schema; golden API suite passes against the live server, including `api/metadata_v2/...` and ringobsid conversions; `apiguide.pdf` returns 302 to the RTD guide; the GUI "API Guide" menu item opens the RTD page.
4. `python -m opus_log_analyzer` produces a report from a sample log using packaged templates and the packaged default configuration module.
5. `pytest` (default, no holdings, no DB beyond the container) green with `-n auto`; coverage ≥90% over the four non-Django packages.
6. `sphinx-build -W -n` clean; `mypy` strict clean; `ruff check` clean with an empty per-file-ignores table.

---

## 7. Risks & mitigations

- **Breaking the public API silently during refactors** → golden-response suite runs on every PR (workflows trigger on `rewrite` from PR-01); fixtures only change in PR-13 (rule-annotated diff report) and PR-21 (API-guide fixture removal + redirect test).
- **Move-PRs breaking CI via files outside `scripts/automated_tests/`** → each move PR enumerates its CI-reachable edits explicitly (PR-03: run_coverage.sh/.coveragerc/pip-install-e; PR-05: coverage config, manage.py verbs, check/upload paths; PR-06: cron templates + config-module default); the generalized rule in §4 covers the rest.
- **Django 5.2 surprises** (tag_re monkeypatch, PyMemcacheCache, mysqlclient, `extra()` usage in `metadata/views.py:534-545`) → PR-09 includes a targeted deprecation sweep (`python -W error::DeprecationWarning manage.py check`) and the integration suite; `extra()` rewritten then.
- **Models restructure drift** → PR-07's two-process `_meta` JSON diff (no DB needed for the checked-in split); generator changes validated on the self-hosted runner; diff re-run in PR-09 under 5.2.
- **`ImportContext` refactor regressions** → the threading pattern is fixed in PR-11 (no design latitude), the pytest beachhead (PR-03) and PR-02 seams exist, and the integration import run gates it.
- **xdist + shared MySQL state** → unit suite touches only per-test scratch schemas; integration suite stays serial; pytest-django never manages the integration DB (unittest.TestCase collection + `django_db_blocker.unblock()`; `django_db` marker forbidden there).
- **Coverage gate integrity** → two separate configs (§5a); the 90% gate is introduced with PR-19 when the suite exists; the integration 100% gate keeps its scope explicitly, including the `tests/opus_support` contribution.
- **Deployed servers during the rewrite** → `main` remains deployable throughout; `rewrite` merges once, with the deploy-flow rewrite (PR-22, incl. `django-admin migrate` and the `deploy.env` split) landing before the merge.
- **log_analyzer scope addition** → 2,955 lines, the least-explored codebase now in scope; PR-06 is a pure move with two pre-identified landmines fixed (config-module default collision with the Django `opus` package; cron templates), and its lint/type/test debts are absorbed by the existing phase structure.

## 8. Self-critique (known weak points of this plan)

- **PR-05 is the riskiest PR** (every import line in the Django app changes) and is deliberately executed as a single PR — a partial per-app split would require both import roots resolvable simultaneously (new sys.path shims), which this plan bans. Mitigation is the strict move/modify commit separation: the rename commit and the rewrite commit are reviewed independently, and the rewrite commit is almost entirely mechanical (`import settings` → `from django.conf import settings`; bare app names → `opus.apps.*`).
- **The mini-holdings fixture spike (PR-19)** was the plan's largest unknown; it is now specified as subset-don't-synthesize with a mechanical success criterion, the PR-02 `require_shelves` prerequisite, and a time-boxed, pre-specified fallback — the residual risk is pdsfile's directory-acceptance logic, which the fallback covers.
- **Phase ordering trade-off:** types (Phase D) land before the full test suite (Phase E). Mitigated by PR-16's two-layer test (schema check + behavioral smoke per mission), opus_support tests landing early (PR-03), and the GitHub pytest job running from PR-03 on.
- **`ImportContext` (PR-11) is a wide mechanical diff** across every do_* module and many obs methods; the fixed threading pattern removes design latitude but not volume. The alternative (keep impglobals, wrap in accessors) was rejected as not actually fixing testability.
- **Estimate honesty:** PR-12 (SQL consistency, grep-scoped) and PR-17 (Django annotations) are each large; if they stall, they can be subdivided by app without breaking the sequence. PR-16's mult-return normalization commit touches many obs modules and leans on integration CI as its oracle.

---

## Execution notes (append-only; see §4a)

*Each executing sub-agent adds dated bullets here — in its own PR — for any fact later
PRs need (spike outcomes, validation results, forced deviations). Never rewrite the plan
body; never rewrite or delete earlier notes.*

- (none yet)

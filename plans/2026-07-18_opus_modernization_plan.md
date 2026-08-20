# rms-opus Modernization Plan

**Target executor:** an opus-class AI — **one fresh sub-agent per PR, no shared context** (execution protocol in §4a).
**Strategy:** all PRs target a long-lived `rewrite` branch off `main`; `rewrite` merges to `main` once at the end.
**Date:** 2026-07-18 (rev 7, amended 2026-07-21 — rev 4 fixed all findings from two independent adversarial reviews; rev 5 added the API-guide migration to ReadTheDocs; rev 6 adds the per-PR sub-agent execution protocol; rev 7: console scripts with underscore names for `opus_import`/`opus_log_analyzer`/`opus_error_analyzer`; `ruff format` enforced but only in a final format-only PR (PR-23); Django package renamed `opus`→`opus_app`; `DB_BRAND`/DB-backend abstraction kept for the future; more OPUS2-porting `util/` tools deleted; settings.py made maximally Django-modern; a required adversarial pre-PR review governed by the named cursor rules (`python.mdc`, `python_testing.mdc`, `doc_python.mdc`, `doc_dev_guide.mdc`, `pull_request.mdc`); `filecache.mdc`/`logging.mdc` rules NOT copied; bandit + vulture enabled in CI and run-scripts (bandit in PR-01, vulture in PR-02 after the dead-code removal); pyproject copied from the template first; RTD acceptance made a manual post-merge check; the adversarial pre-PR review iterates up to four churn-focused passes then stops-and-reports if unconverged; a post-PR CodeRabbit loop (respond to/fix all comments, wait for settle, `@coderabbitai review` in 10-min increments if out of reviews) with a ready-to-merge gate on CI **and** CodeRabbit both green; PR titles carry the plan's phase/PR tag; fixed a stale §2 layout comment that said the postgresql stub was removed; **rev 7.1 (2026-08-16): PR-01 ruff burn-down amended after a stop-and-report — the seed set predated ruff's `PT`/`B` rules, which fire on tests the plan keeps/defers; `PT009`+`PT027` go in a documented global `ignore` (the integration suite stays `unittest` per PR-18), `PT015`/`B011`/`B006` are grandfathered per-file and removed in PR-02, `PT018` and the rest are fixed in PR-01; PR-17's empty-table criterion is preserved; **rev 7.2 (2026-08-16): documented wide-PR exception to the CodeRabbit merge gate — CodeRabbit hard-skips PRs over its 100-file cap (PR-01 ≈139 files; the move PRs), so for such PRs the skip is accepted and the §4a adversarial review substitutes; **rev 7.3 (2026-08-16): after a PR-01 integration failure (ruff SIM118 stripped `.keys()` off a `pdsparser.PdsLabel`, which has no `__iter__` → `KeyError` at import), added a mandatory §4a review lens for semantics-changing lint/refactor autofixes on duck-typed objects; **rev 7.4 (2026-08-17): ratified that `ImportDBException`'s `BaseException` base is an old mistake — PR-10 narrows it to `Exception` with a mandatory audit of intervening `except Exception:` handlers (esp. `do_import.py:1462`); PR-09 told explicitly to delete (not relocate) the dictionary app's lone surviving `favicon` route, verified dead and a `STORAGES` import-time hazard; **rev 7.5 (2026-08-17): added PR-03a (fix the four pre-existing `opus_support` defects CodeRabbit found during PR-03, incl. the user-visible `wavenumber_resolution` alias bug), inserted after PR-03 without renumbering; **rev 7.6 (2026-08-18): PR-13 given a named bug to fix — `math.isfinite()` raises `OverflowError`, not `ValueError`, on a huge int, so a crafted numeric query param escapes `parse_unit_value` as an HTTP 500 where rule 2 requires 400; corrected the PR-03a claim that the fused suffix could never match; **rev 7.7 (2026-08-19): `create_opus_models.sh` homed in its own `scripts/models/` (it is a Django-side generator, not import tooling); PR-10 given two more named bugs from PR-04 — the un-prefixed f-string in `do_dictionary.py` (whose placeholder name is also wrong) and making `util/` import-safe, since `retrieve_ra_dec.py` fires ~160 SIMBAD requests from its module body and PR-21's autodoc imports every module**)

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
| DB backend | **MySQL is the only implemented brand**, but the backend abstraction is *kept for the future*: `DB_BRAND` stays in the config and everywhere it is threaded today, `importdb.get_db()` keeps its `db_brand` dispatch, and `importdb/postgresql.py` remains as the stub for a future backend (**not** deleted) |
| Versions | **Django 5.2 LTS**, **Python ≥3.12** (CI matrix 3.12/3.13); Django 4.2 is EOL |
| obs typing | **Schema-validated annotations**: shared aliases + a CI test that cross-checks every `field_obs_*` annotation against `table_schemas/*.json` (decision table in PR-16) |
| ruff | Adopt template rule set. **`ruff format` IS enforced, but only in the final format-only PR (PR-23)** — until then the template's `ruff format --check` workflow step is **kept but disabled** and `ENABLE_RUFF_FORMAT` in `run-all-checks.sh` stays `false`, exactly like the `ENABLE_MYPY` burn-down. The check is **never deleted** from the workflow or the script (we want it available for PR-23 and beyond). pymarkdown and pyroma ARE adopted per template |
| Back-compat | Public web API behavior preserved (incl. `ringobsid`, `metadata_v2`, and the `/static_media/` URL namespace); the template's "no backwards compatibility" rule is waived *for the public API only* — internal code carries no compat shims. Two sanctioned, documented API changes only: #1082's 404→400 (PR-13) and `apiguide.pdf` becoming a redirect to the ReadTheDocs API guide (PR-21) |
| API guide | The public API guide **moves into the Sphinx dev docs on ReadTheDocs** (full content parity with today's `api_guide.md`); the GUI's "API Guide" menu item opens the RTD page in a new tab instead of the in-app rendering; the in-app guide machinery (mistune rendering, `%` placeholders, `__help/apiguide.*`) is removed — see PR-21 |
| Error PR scope | **Status codes + logging only** per the decision table in PR-13; error *bodies* stay as-is (body normalization is possible later work, not this rewrite) |
| Fault injection | `OPUS_FAKE_*` delays/errors and `throw_random_*` behavior **kept but folded into the `@api_view` decorator** (fires pre-handler; see PR-13); `__fake/*` endpoints stay |
| Dictionary | Django dictionary *app* removed; `definitions`/`contexts` tables, `do_dictionary.py` import step, and a tooltip lookup helper are kept. `DICTIONARY_TERM_URL` is **dropped** from config (defined in the secrets template but consumed nowhere in the code — verified by repo-wide grep) |
| Dictionary data | `pdsdd.full` (1.8 MB) + `contexts.csv` **ship as package data** (importlib.resources) — installs are self-contained |
| log_analyzer | **Becomes a formal package in `src/`** runnable via `python -m opus_log_analyzer`; fully inside the ruff/mypy/test/docs gates |
| perf_test | Stays a top-level directory outside `src/` and **explicitly excluded from ruff/mypy/pytest scopes in pyproject (PR-01)**; the checked-in `stream_c.exe` binary is deleted |
| Coverage | GitHub-hosted unit CI: **≥90% measured over `opus_support`+`opus_config`+`opus_import`+`opus_log_analyzer` only** (`src/opus_app` — the Django app — is explicitly excluded from the unit gate; its coverage is owned by the integration workflow's retained **100%** gate). Two coverage configs, not one — see §5a |
| Version file | setuptools-scm `write_to = "src/opus_config/_version.py"`; every other package surfaces version at runtime via `importlib.metadata.version("rms-opus")` — no per-package `_version.py` |
| Version scheme | Release tags **continue the existing zero-padded v3.x scheme** (next release after the merge: `v3.23.00`) — a declared deviation from the template's plain-SemVer tagging rule; setuptools-scm parses these tags fine (PEP 440 normalizes `3.23.00` → `3.23.0`) |
| Django pkg name | The Django project package is importable as `opus_app` (renamed from the generic `opus`); this also eliminates any risk of a repo-root `opus/` namespace dir shadowing the installed package |
| Git history | **Strict move/modify separation**: a move commit contains ONLY renames; even mechanical import rewrites land in the immediately following commit, so `git log --follow` detection is perfect. No history rewriting |
| Migrations | Django's own contrib tables (`django_session`, auth/contenttypes/admin) continue to be created by a migrate step — on pip-deployed servers this is **`django-admin migrate` with `DJANGO_SETTINGS_MODULE=opus_app.settings` and `OPUS_CONFIG` set** (repo-root `manage.py` is a dev convenience, not part of the wheel). OPUS tables are always created from scratch by import; OPUS-side Django migrations remain irrelevant |

### Remaining standing assumptions

- The JS/CSS frontend is untouched except for being packaged as static assets (no bundler introduced). A JS build system/bundler is out of scope for this plan and is tracked separately in issue **#1436**, which already recommends introducing `npm` + a bundler (Vite).
- `djangorestframework` moves to dev-extras. Note: `rest_framework` also sits in INSTALLED_APPS (`settings.py:142`) with a `REST_FRAMEWORK` block (146-149) until PR-09 removes both; between PR-01 and PR-09 the wheel's runtime deps alone cannot start the app — this is fine because `requirements.txt` remains the deploy mechanism until Phase F. Do **not** "fix" this by re-adding DRF to runtime deps.
- `hurry.filesize` (one call site, `cart/views.py:34`) replaced by a small local helper; `pdfkit`/`qrcode`/`pyyaml` stay; `mistune` is **dropped in PR-21** (its only consumer is the in-app API-guide renderer, which PR-21 removes).
- `manage.py` lives at repo root pointing at `opus_app.settings` (dev convenience); deployment remains Apache/mod_wsgi + memcached.

---

## 2. Target repository layout

```
rms-opus/
├── pyproject.toml               # single config source for project, deps, ruff, mypy, pytest, setuptools-scm, and the UNIT coverage config (integration coverage config is separate — §5a)
├── README.md, CONTRIBUTING.md, LICENSE, codecov.yml, .readthedocs.yaml
├── .cursor/{rules,skills}/      # copied from repo_template (13 rules — filecache.mdc + logging.mdc deliberately excluded; 4 skills)
├── .github/workflows/
│   ├── run-tests.yml            # GitHub-hosted: ruff + mypy + bandit + vulture + pymarkdown + pytest (holdings-free, MySQL service container), matrix 3.12/3.13; docs-build job added in PR-21
│   ├── run-integration.yml      # self-hosted: current end-to-end import + golden API suite (successor of run-app-tests.yml); 100% coverage gate kept
│   └── publish_to_pypi.yml, publish_to_test_pypi.yml   # template release flow
├── scripts/
│   ├── run-all-checks.sh        # from template; ENABLE_RUFF_FORMAT stays false until PR-23 (the format-only PR flips it true)
│   ├── automated_tests/…        # kept, paths updated
│   ├── import/                  # shell wrappers moved from opus/import: import_for_tests.sh, import_all.sh, _import_all_internal.sh, clone_database.sh, find_unknown_warnings.sh
│   ├── releases/                # kept (v3.x tag flow)
│   └── server/…                 # kept, updated to pip-install deploy flow (Phase F); log_analyzer cron templates land here; deploy-infrastructure env file (see PR-22)
├── src/
│   ├── opus_support/            # internal shared package (split from lib/opus_support.py: sclk.py, orbits.py, time_parsing.py, angles.py, units.py)
│   ├── opus_config/             # TOML config loader (frozen dataclasses, validation, OPUS_CONFIG env var, no default path); hosts _version.py; temporarily hosts the secrets shim (PR-03→PR-08)
│   ├── opus_import/             # from opus/import; python -m opus_import
│   │   ├── __main__.py, cli.py  # argparse surface unchanged
│   │   ├── importdb/            # MySQL only implemented; postgresql.py stub + DB_BRAND brand concept KEPT for the future
│   │   ├── obs/                 # obs_* hierarchy as a subpackage (incl. field_types.py — NOT typing.py, which would trip ruff A005 stdlib-shadow)
│   │   ├── steps/               # do_* modules; do_import.py split into ≤1000-line submodules
│   │   ├── table_schemas/*.json # package data
│   │   ├── dictionary_data/     # pdsdd.full, contexts.csv (moved from top-level dictionary/; package data)
│   │   └── util/                # schema-authoring tools KEPT (dump_pds_definitions.py — assert False fixed; retrieve_ra_dec.py); ALL OPUS2-porting-only tools deleted (get_opus2_mults.py, obs_table_to_schema.py, create_all_obs_table_schemas.sh, master_labels/, dump_param_info.sql) — see PR-02
│   ├── opus_log_analyzer/       # from log_analyzer/; TWO top-level programs kept: log_analyzer.py + error_analyzer.py (NOT renamed to cli.py — there are two entry points); python -m opus_log_analyzer runs the log analyzer; Jinja templates as package data
│   └── opus_app/                # Django project package (renamed from the generic `opus`)
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
│   └── opus_app/                # Django tests that don't need a populated DB (written in PR-18)
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
- `opus_config` is deliberately its own tiny package because *both* `opus_import` and `opus_app` (Django) depend on it and neither should import the other.
- `log_analyzer` is renamed `opus_log_analyzer` on the move (avoids squatting a generic top-level import name); its existing generic-engine/OPUS-subconfig split is preserved as subpackages. Its two top-level programs (`log_analyzer.py`, `error_analyzer.py`) are kept as separate modules — neither is renamed to `cli.py` because there are two entry points (see the console scripts in PR-22).
- After PR-04 and PR-05, the old top-level `opus/` directory is empty and is deleted in PR-05. Because the Django package is renamed `opus_app`, there is no longer any repo-root `opus/` vs. installed-package name collision to worry about at all.

---

## 3. Configuration design (replaces `opus_secrets.py`)

One `opus.toml` (template `opus.toml.template` in repo root), path from `OPUS_CONFIG` env
var — **required; no default-path fallback** (clear startup error if unset/missing/invalid;
multi-install servers set a distinct `OPUS_CONFIG` per install in the vhost/unit/profile).
Loader in `opus_config`: frozen dataclasses per section, explicit validation, no `import *`
anywhere.

```toml
[database]      # brand (DB_BRAND — defaults to MySQL, kept for a future backend), host, schema, user, password
[paths]         # pds3_holdings, pds4_holdings, logfile dirs, tar/manifest paths, notification/blog files, static_root
[django]        # secret_key, debug, allowed_hosts, cache_server_prefix, public_url, product_http_path, viewmaster_url, log levels, fake-delay/error knobs
[import]        # table_temp_prefix, log files
[dictionary]    # pdsdd/contexts paths — default to the packaged data files (term_url dropped; no consumer anywhere). The table_schemas path (DICTIONARY_JSON_SCHEMA_PATH today) gets NO TOML key — schemas are resolved via importlib.resources
```

- `opus_app/settings.py` reads the loaded config object (SECRET_KEY, DEBUG, ALLOWED_HOSTS,
  DATABASES — with `ENGINE` selected from `DB_BRAND` (MySQL today) — cache prefix…); made
  **as Django-modern as possible**: `BASE_DIR` via `Path(__file__)` and `pathlib` paths
  throughout, lists not tuples, the `STORAGES` setting (not the deprecated
  `DEFAULT_FILE_STORAGE`/`STATICFILES_STORAGE`), `DEFAULT_AUTO_FIELD` set,
  `USE_TZ = True`, no deprecated settings (`USE_L10N`, `ADMIN_MEDIA_PREFIX`, …).
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
`DICTIONARY_*` settings — PR-04), and the Django `settings.py` (wildcard, PR-05). PR-04's
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
  `rewrite` branch as `plans/2026-07-18_opus_modernization_plan.md`, committed at branch
  creation), the single PR number to execute, and repository access — plus, for PR-01 only, read access
  to the template repo at `/seti/all_repos/rms-devenv/repo_template` (the source of the
  copied scaffolding). Nothing else. The sub-agent reads §1–§3, §4's preamble,
  its own PR section, §4a/§5/§5a/§6, and the Execution notes appendix — it does not
  need, and must not rely on, any prior conversation.
- **All inter-PR state lives in artifacts, never in context:** the repository content,
  merged PR descriptions, and this plan file are the only carriers of state. Where a PR
  produces knowledge later PRs need (e.g. PR-19's spike outcome, PR-07's generator
  validation result, any deviation forced by reality), the executing sub-agent records it
  in a **"Execution notes" appendix at the bottom of `plans/2026-07-18_opus_modernization_plan.md`, amended in that same PR**
  — dated, one bullet per fact, never rewriting the plan body.
- **Orchestration:** the orchestrator (human, or a supervising agent) launches the
  sub-agent for PR-N only after PR-(N-1) is merged into `rewrite` with both workflows
  green. PRs are strictly sequential; no parallel PR execution (later PRs edit files
  earlier PRs create).
- **Adversarial pre-PR review (required, before opening the PR):** once the work is
  complete and both workflows are green locally, the executing sub-agent launches a
  **fresh, independent opus-class sub-agent** to adversarially review the full diff
  against: the Python coding style in `.cursor/rules/python.mdc`, documentation against
  `doc_python.mdc` (and `doc_dev_guide.mdc` for the dev guide), test coverage **and** the
  test-design/critique guidance in `python_testing.mdc` (are the tests meaningful, not just
  present), adherence to this plan (decision tables, scope boundaries, strict move/modify
  commit separation), and the
  correctness/accuracy of the code changes. The executor resolves every finding — or
  records in the PR why a finding is rejected — **before** opening the PR, and includes the
  review summary in the PR description. The reviewer is advisory; it does not merge or open
  the PR.
  - **Iterate up to four review passes.** After the executor addresses a pass's findings,
    it launches another fresh reviewer, **repeating until a pass comes back clean, up to a
    maximum of four passes.** Each pass after the first focuses on the *churn* — the
    changes the executor made in response to the previous pass — checking both that each
    finding was actually fixed and that the fix introduced no new problem, rather than
    re-reviewing the whole diff from scratch (a full re-read is still allowed when the
    churn is large or structural). Watch for churn that oscillates (a later fix reverting
    an earlier one) or grows instead of converging — that is a signal to stop patching and
    reconsider the approach.
  - **If the fourth pass is still not clean,** do **not** open the PR on a hope: the
    executor analyzes *why* the reviews aren't converging (findings the fix can't satisfy,
    conflicting guidance, a plan contradiction, an underspecified requirement) and
    **stops-and-reports** that analysis rather than shipping. The orchestrator then
    decides how to proceed.
  - **Additional small, focused reviews are allowed** whenever the executor's judgment
    warrants — e.g. a targeted re-check of one risky module or one contentious finding —
    and do not count against the four-pass budget for the full-diff review.
  - **Mandatory lens — semantics-changing lint/refactor autofixes on duck-typed objects.**
    Every review pass on a PR that runs ruff (or any) autofixes or mechanical refactors
    **must** explicitly audit each change that could alter *runtime behavior* on a
    non-builtin / duck-typed object, because the holdings-free GitHub CI cannot catch these
    — only the self-hosted integration suite (or nothing) will. Validate that the target of
    each such change is actually a builtin `dict`/`list`/etc., not a custom class or C
    extension that merely looks like one. Known traps: **SIM118** (`.keys()`/`.values()`/
    `.items()` stripped from iteration/membership — broke `pdsparser.PdsLabel` in PR-01,
    which has no `__iter__`; see Execution notes), **SIM110/111** (`any()`/`all()`
    rewrites), **C4** comprehension rewrites, `.get()`/`in`/truthiness rewrites, and
    generator-vs-list changes. When in doubt, keep the explicit form and suppress the rule
    on that line with a justified `# noqa` rather than trusting the autofix.
- **PR title format:** every PR title carries **the phase letter and PR number from this
  plan** alongside the normal conventional-commit description, e.g.
  `[Phase A · PR-01] feat: ruff replaces flake8; pyproject + template scaffolding`. The
  phase/PR tag makes the PR's place in the sequence unambiguous at a glance.
- **Post-PR CodeRabbit loop (required, after opening the PR):** once the PR is open, the
  executor **lets CodeRabbit review it and responds to every CodeRabbit comment** — fixing
  the ones that are correct (with a commit) and replying with a reasoned rejection to the
  ones that are not. After pushing fixes, **wait for CodeRabbit to re-review and settle
  again**; repeat until CodeRabbit raises nothing new. If CodeRabbit is rate-limited / out
  of reviews, **wait in 10-minute increments and post a `@coderabbitai review` comment** to
  re-trigger it, until it responds.
  - **Wide-PR exception (documented):** CodeRabbit hard-skips any PR whose changed-file
    count exceeds its per-PR cap (100 files) with "Review skipped: N files exceed the
    limit" — this is **not** rate-limiting and the 10-minute retry cannot clear it. A few
    PRs are structurally wide by design (PR-01's repo-wide ruff burn-down ≈139 files; the
    move PRs, esp. PR-05's Django-app rename, touch every import). For a PR that legitimately
    exceeds the cap, **the CodeRabbit skip is accepted** and the §4a adversarial pre-PR
    review (which covers the full diff) stands in its place; the executor records the
    accepted skip (with the file count) in the PR description. This exception applies **only**
    when the cap is genuinely exceeded — a normal-sized PR must still get CodeRabbit green,
    and the executor must not split or reshape a PR merely to dodge review.
- **Ready-to-merge gate:** the executor declares the PR ready to merge **only once both CI
  workflows and CodeRabbit are simultaneously stable and green** — CI passing and
  CodeRabbit having settled with no unresolved correct findings — **or, for a PR that
  exceeds CodeRabbit's file cap, once CI is green and the accepted-skip is recorded per the
  wide-PR exception above.** Until then the PR is still in progress. The sub-agent still
  does **not** merge; it hands the settled PR to the orchestrator.
- **Definition of done for a sub-agent:** the adversarial pre-PR review (above) is
  complete and its findings addressed; then an open PR against `rewrite`, titled with its
  phase/PR tag, with both workflows green, the post-PR CodeRabbit loop settled, a
  description covering what/why/testing evidence **and the adversarial review summary**
  (plus the extra artifacts specific PRs require: PR-07's `_meta` diff, PR-13's
  rule-annotated fixture diff, PR-21's content-parity checklist), and any Execution-notes
  amendment. The PR itself is written and opened following `.cursor/rules/pull_request.mdc`.
  The sub-agent declares ready-to-merge per the gate above but does not merge; the
  orchestrator reviews and merges.
- **Stop-and-report rule:** if reality contradicts the plan (a file:line claim is stale,
  a step is impossible as written, a decision table doesn't cover a case), the sub-agent
  **stops and reports the contradiction in the PR/conversation rather than improvising**
  — the plan is then amended (Execution notes or a reviewed plan-body fix) before work
  resumes. Small mechanical drift (line numbers moved, counts changed) that doesn't
  change the instruction's meaning is not a contradiction; note it and proceed.

### Phase A — Tooling bootstrap & dead code (no moves)

**PR-01: Tooling: ruff replaces flake8; pyproject + template scaffolding; CI runs on `rewrite`.**
- (`plans/2026-07-18_opus_modernization_plan.md` — this document — the executive overview
  `plans/2026-07-19_opus_modernization_overview.md`, and the executor guide in `CLAUDE.md`
  were committed directly to `rewrite` at branch creation, before this PR; verify they are
  present. The `plans/` and `critiques/` directories are deleted in PR-24 when `rewrite`
  merges — their content is superseded by the dev docs and the merged PR history.)
- **First:** add `rewrite` to the `pull_request`/`push` branch filters of
  `run-app-tests.yml` (and the new `run-tests.yml`); every subsequent PR is actually
  gated. These filters are narrowed back to `main` in PR-24. **Branch-protection note:**
  `rewrite` carries the same protection as `main` (1 approval + required status checks,
  currently contexts "Run Lint" and "Test OPUS (self-hosted-linux, 3.12)"). Whenever a
  PR renames a workflow or job (this PR replaces Run Lint; PR-19/PR-20 rename the
  workflows), the required-check contexts on the `rewrite` protection must be updated to
  the new names — via `gh api -X PUT
  repos/SETI/rms-opus/branches/rewrite/protection/required_status_checks` if the
  executor's token permits, otherwise reported for the orchestrator to do.
- **Copy the template's `pyproject.toml`
  (`/seti/all_repos/rms-devenv/repo_template/pyproject.toml`) first, then modify it** for
  OPUS — do not author it from scratch: project metadata (name `rms-opus`,
  `requires-python >=3.12`,
  dynamic version via setuptools-scm with `write_to = "src/opus_config/_version.py"` —
  directory created then, harmless until PR-03 populates it), runtime deps lifted from
  `requirements.in` (django upgrade deferred to PR-09 — start with `django>=4.2,<5` to
  keep working), dev extras (incl. `pytest-django`, `pytest-xdist`, `pytest-cov`,
  `djangorestframework`) and docs extras; `[tool.ruff]` per template (line 100, py312
  target, select E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF; global `ignore = ["PT009", "PT027"]` for
  the permanently-`unittest` integration suite — see the burn-down discipline below) with
  `perf_test/` in `exclude`;
  `[tool.pytest.ini_options]` (`testpaths=["tests"]`), `[tool.coverage]` (unit scope only
  — §5a), mypy section present but not yet enforced (also excluding `perf_test/`);
  `[tool.bandit]` (recurse `src/`, exclude tests + `perf_test/`) and `[tool.vulture]`
  (min-confidence + a `vulture_whitelist.py` for framework/false-positive symbols, scoped
  away from `perf_test/`) — **bandit is enabled in CI this PR; vulture's config lands here
  but vulture is not enabled until PR-02, after the dead-code removal** (see below).
- Copy from the template repo (`/seti/all_repos/rms-devenv/repo_template` on the RMS
  development machines): `.cursor/rules` — **all except `filecache.mdc` and `logging.mdc`,
  which are deliberately NOT copied** (13 of the template's 15 rules) — plus
  `.cursor/skills`, `.vscode`/`.cursor` settings, `codecov.yml`, `.readthedocs.yaml`,
  `scripts/run-all-checks.sh` (ENABLE_RUFF_FORMAT stays false until PR-23; ENABLE_MYPY
  flips true in Phase D; **ENABLE_BANDIT flipped true this PR; ENABLE_VULTURE flipped true
  in PR-02** — both default false in the template; pymarkdown + pyroma enabled per template
  defaults — but until
  PR-21 creates `docs/`, the pymarkdown scan list and the Sphinx step are limited to what
  exists: `README.md CONTRIBUTING.md .cursor/`),
  `CONTRIBUTING.md`, PR/issue templates, publish workflows from repo_template. **When
  adapting the template `run-tests.yml`, keep its `ruff format --check` step but disable
  it** (guarded like `ENABLE_MYPY`, off until PR-23) — do **not** delete it; PR-23 enables
  it. Delete `CODING_STYLE.md`, `CODE_REVIEW_TEMPLATE.txt`,
  `scripts/create_all_venv.sh`, `scripts/test_all_venv.sh`; rename `LICENSE.md` → `LICENSE`.
- **Governing cursor rules** (binding on executors and on the §4a adversarial review):
  `python.mdc` = Python coding style; `python_testing.mdc` = test design and critique;
  `doc_python.mdc` = overall documentation/docstring style; `doc_dev_guide.mdc` = the
  Sphinx dev guide (PR-21); `doc_readme.mdc` = the README (PR-21);
  `pull_request.mdc` = how every PR is written and opened. `filecache.mdc` and
  `logging.mdc` are intentionally absent (not applicable to OPUS).
- Replace `.flake8` + `run_flake8.sh` + `run-lint.yml` with ruff in the new `run-tests.yml`
  (lint job runs `ruff check` + `bandit` now; vulture joins in PR-02, mypy in Phase D,
  `ruff format --check` in PR-23). Bring the codebase to `ruff check` and `bandit`
  clean. **Burn-down
  discipline:** the `[tool.ruff.lint.per-file-ignores]` table in pyproject *is* the
  burn-down list; PR-01 seeds it with two kinds of entry and **nothing else**:
  1. **Legacy-refactor codes** (today's flake8 ignores that need real refactoring):
     `E722, F403, F405, E501`. (`N8xx` is authorized but currently fires zero times — it
     may be listed inertly or omitted.) Removed as the underlying code is cleaned up
     through PR-17.
  2. **Codes whose remediation this plan assigns to the *next* PR** — grandfathered here so
     PR-01 doesn't pre-empt PR-02's scope, each entry annotated with its removal PR:
     `PT015, B011` (`assert False`) and `B006` (mutable default arg) — PR-02 explicitly
     rewrites these (`assert False` → `NotImplementedError`; the `ImportDBSuper.__init__`
     default), and removes these ignores. **Removed in PR-02.**
  Every **other** failing code must be fixed in PR-01 itself (import sorting, `.find()`→`in`,
  comprehensions, `UP*`, `B904`, `B007`, `PT018` (3, composite assertions), etc.). PR-17's
  exit criterion is that this table is empty (which holds: the legacy-refactor codes and the
  two PR-02 grandfathers are each retired by their annotated PR, all ≤ PR-17).
  - **Global `ratchet` exception for the retained `unittest` suite (not a per-file-ignore):**
    `PT009` (1023 — `self.assertEqual` etc.) and `PT027` (215 — `self.assertRaises`) exist
    solely to migrate `unittest`-style assertions to pytest-native ones, but PR-18 *fixes*
    that the live-DB integration tests (today's `apps/*/test_*.py`, all
    `django.test.TestCase` subclasses) **stay `unittest.TestCase` permanently**. Enforcing
    these two codes would contradict that ratified decision, and no conversion PR will ever
    retire them — so they cannot be burn-down entries. Instead, list them **once** in the
    top-level `[tool.ruff.lint] ignore` (a documented global config choice, *not* the
    per-file-ignores burn-down table), with a comment citing the PR-18 unittest decision.
    This keeps `PT018` and all other `PT` rules enforced everywhere, keeps the per-file
    burn-down table emptiable by PR-17, and costs nothing on the new function-style pytest
    suites (plain `assert`/`pytest.raises` never trigger `PT009`/`PT027`). Ruff scope
    includes `log_analyzer/`.
  **Bandit follows the same burn-down discipline:** findings are fixed or annotated
  `# nosec` with a written justification (per `security.mdc`). (Vulture is enabled in PR-02
  with its own whitelist burn-down — see there.) Both the bandit `# nosec`/config skips and
  the vulture whitelist are shrunk to individually-justified entries by PR-17.
- requirements.in/txt stay temporarily as the deploy mechanism until Phase F.

**PR-02: Dead code removal & bug fixes.**
- **Enable vulture in CI + run-all-checks** (flip `ENABLE_VULTURE=true`; add the vulture
  step to `run-tests.yml`) as the **final step of this PR, after all the dead-code deletions
  below** — running it last means most of what vulture would flag is already gone. Genuine
  remaining dead code it surfaces is removed here too; only irreducible false positives
  (framework hooks, dynamically-referenced symbols) go in `vulture_whitelist.py`, which
  PR-17 shrinks to individually-justified entries. Bring the tree vulture-clean before the
  PR is opened.
- **The DB-backend abstraction is KEPT** (decision table): do **not** delete
  `importdb/postgresql.py`, do **not** remove `db_brand` from `get_db()`, and keep
  `DB_BRAND` in every place it appears today (`opus_secrets_template.py:12`,
  `scripts/automated_tests/opus_setup_environment.sh:41`,
  `scripts/server/import_and_deploy/_opus_setup_environment.sh:31`, and the call site
  `main_opus_import.py:442`). MySQL stays the only implemented brand; this preserves the
  option of a future backend at no cost.
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
  commented block, the **OPUS2-porting-only** `util/` tools (deleted: `get_opus2_mults.py`;
  `obs_table_to_schema.py` plus its driver `create_all_obs_table_schemas.sh` and the
  `master_labels/` reference labels it consumes; and `dump_param_info.sql` — all marked
  *"should only be used for initial setup of the new import pipeline … deprecated"* and now
  superseded by the checked-in `table_schemas/*.json`), stale `install.md` refs to
  `requirements-python3.txt`, `perf_test/stream_c.exe`. `util/dump_pds_definitions.py` and
  `util/retrieve_ra_dec.py` are **kept** (not OPUS2-porting; the former is a schema-authoring
  tool with its `assert False` replaced by a real error).
- Fix known bugs from #1434: `importdb/super.py:113` `showarning` typo;
  `obs_volume_hstjx_xxxx.py` unbound `wr/bw` (else-branch at ~91 before `bw // wr`);
  `obs_volume_hstox_xxxx.py` `wr1 > wr2` None comparison (~63-72). (The
  `obs_profile_pds4.py` missing-return reported in #1434 is already fixed in the current
  tree — verify and do not hunt for it.) Bare `except:` → `except Exception`; pointless
  `except: raise` removed; `assert False` → `NotImplementedError`; mutable default arg in
  `ImportDBSuper.__init__` fixed. **Then remove the now-obsolete `PT015, B011, B006`
  entries PR-01 grandfathered into `[tool.ruff.lint.per-file-ignores]`** (they were parked
  there awaiting exactly these fixes); re-run `ruff check` to confirm still clean.
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

**PR-03a: Fix the four latent `opus_support` defects.**
- Assigned 2026-08-17 after PR-03's CodeRabbit review surfaced four **pre-existing** bugs in
  the moved code. PR-03 correctly refused to fix them (a pure move must not change
  behavior), and no other PR owned them. This is a small, behavior-changing fix PR — it
  lands **immediately after PR-03** so the user-visible parsing bug does not survive the
  whole types phase. Full diagnoses are in the PR-03 Execution-notes bullet; do not
  re-derive them.
- Each fix **requires a regression test** in `tests/opus_support/` (the pytest suite and its
  coverage gate went live in PR-03, so they have a home):
  1. **`units.py` — `wavenumber_resolution` loses two aliases to missing commas.** Adjacent
     string literals with no comma make Python concatenate them, so the list holds
     `'cm^-1perpixelcm**-1/p'` and neither original alias; same defect in the `m^-1` entry.
     `1 cm^-1perpixel` and `1 cm**-1/p` are therefore unrecognized, and the fused entry is
     reachable only by typing the fused spelling itself (pre-fix,
     `'1 cm^-1perpixelcm**-1/p'` really did parse, returning `1.0`).
     **User-visible — this is the reason this PR is not deferred.** Test must
     parse one suffix per alias list.
  2. **`angles.py` — unescaped dot in the fallback `"N N N"` regex.** `(\d+(|.\d*))` lets
     `.` match any character, so `'1 30 36 5'` / `'1 30 36a5'` reach `float(second)` and
     raise a `ValueError` carrying CPython's message. **Note the coupling:** every other
     rejection in that function raises a bare `ValueError`, and `tests/opus_support/
     test_angles.py` asserts that empty-message contract — so fixing the regex changes which
     message these inputs produce and **the existing test must be updated in the same
     commit**. Decide explicitly whether the contract is "bare ValueError for all rejects"
     (preferred — then the fix must route these through the same raise) and state it.
  3. **`orbits.py` — unreachable raise + mangled value in `parse_cassini_orbit`.** The
     `raise ValueError(f'Invalid Cassini orbit {orbit}')` sits inside the `try` whose own
     `except ValueError: pass` swallows it, and `orbit` is rebound to the stripped string,
     so `'0002'` reports `Invalid Cassini orbit 2`. Fix both the reachability and the
     reported value (report the original input).
  4. **`sclk.py` — no-op statement in `_parse_multi_field_sclk`.** `parts[-1]` is evaluated
     and discarded where the comment says the empty final field is deleted. Output is
     unchanged (the padding loop pads it anyway), so this is dead code PR-02 missed —
     vulture does not flag bare expression statements. Either make it the intended deletion
     or remove it; **assert the output is unchanged either way**.
- Integration CI gates the behavior change; `parse_unit_value` is used by the import
  pipeline and the web app, so run the full local chain (§ local-testing note) before
  opening.

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

**PR-05: Move `opus/application/` → `src/opus_app/` Django package.**
- `settings.py`/`urls.py` into the package; real `wsgi.py` committed (`opus.wsgi_template`
  deleted — note the memcache probe already lives in `settings.py:4-21` and simply moves
  with it); repo-root `manage.py` with `DJANGO_SETTINGS_MODULE=opus_app.settings`; apps become
  `opus_app.apps.*` (INSTALLED_APPS, ROOT_URLCONF, all cross-app imports rewritten from bare
  names; `import settings` → `from django.conf import settings` everywhere); templates
  DIRS from BASE_DIR (stale `quide` path dropped). Secrets via the shim. The emptied
  top-level `opus/` directory is deleted. **This PR is executed as a single PR** — the
  strict move/modify commit separation is what makes it reviewable (review the rename
  commit and the rewrite commit independently); there is no per-app fallback (a partial
  split would require both import roots resolvable simultaneously, i.e. new sys.path
  shims, which this plan bans).
- **Static files:** directory `static_media/` → `src/opus_app/static/`, but
  `STATIC_URL = '/static_media/'` and the `OPUS_STATIC_ROOT`/Apache alias semantics are
  **unchanged, permanently** — the URL namespace is public surface (hardcoded in
  `opus.js:1120`, embedded in golden HTML fixtures, aliased in production Apache). Zero
  golden-fixture diffs expected from this PR.
- test_api + per-app DB tests **+ `test_db_data/` + `test_perf/`** move to `integration/`
  (with `__init__.py` files so unittest discovery keeps working). URL patterns byte-identical.
- **Integration invocation between this PR and PR-18 — explicit spec:**
  `run_coverage.sh` moves to repo root (invoked from root); the integration coverage
  config becomes `integration/.coveragerc` (see §5a) with includes updated to
  `src/opus_app/apps/*`, `integration/test_api/*`, `src/opus_support/*`; `manage.py` custom
  verbs (`api-all` etc.) keep working with their label mappings updated to
  `integration.test_api`; Django test discovery runs from repo root (`manage.py test
  integration`); `opus_run_unittests_coverage.sh` and `opus_check_coverage.sh` drop their
  `cd opus/application` and use repo root; `run-app-tests.yml` codecov upload path becomes
  `./coverage.xml`.

**PR-06: Move `log_analyzer/` → `src/opus_log_analyzer/` package.**
- Rename on move; **both top-level programs are kept as separate modules —
  `log_analyzer.py` and `error_analyzer.py` (do NOT rename either to `cli.py`; there are
  two entry points, wired as console scripts in PR-22)**; add an `__main__.py` that calls
  `log_analyzer.main()` so `python -m opus_log_analyzer` runs the log analyzer; the generic
  engine and the OPUS-specific `opus/` config become subpackages (this internal
  `opus_log_analyzer.opus` subpackage is unrelated to the Django `opus_app` package); Jinja
  `templates/` as package data; `server/` cron templates relocate to `scripts/server/`
  **and are rewritten to invoke the installed `opus_log_analyzer` / `opus_error_analyzer`
  commands**; its private `mypy.ini` deleted (config consolidates into pyproject in
  Phase D).
- **Config-module default fix:** `log_analyzer.py`'s `--configuration` default is the
  string `'opus.configuration'` resolved via `importlib.import_module`
  (`log_analyzer.py:80,109`) — once installed as a package there is no top-level `opus`
  package for that bare name to resolve against (and it must not be confused with the
  Django `opus_app` package), so it breaks. The default becomes
  `'opus_log_analyzer.opus.configuration'`, and a unit test asserts the default module
  imports and exposes `Configuration`. (`error_analyzer.py` has no such config-module
  default.)

**PR-07: Split the checked-in `search/models.py` into a package; update the generator.**
- The checked-in 700KB `models.py` is **restructured by hand/script** (no live DB needed)
  into `opus_app/apps/search/models/` split by table group (obs tables, mult tables,
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
  consumption in `opus_import.cli`, `opus_app/settings.py`, `do_dictionary`; delete
  `_secrets_compat.py`, `opus_secrets_template.py`, `apps/dictionary/secrets_template.py`,
  and every remaining `opus_secrets`/`OPUS_SECRETS` reference;
  `scripts/automated_tests/opus_setup_environment.sh` and the server
  `_opus_setup_environment.sh` emit `opus.toml` (its `[database]` section keeps the
  `DB_BRAND`/`brand` value) and export `OPUS_CONFIG`. This is the point at which the
  `scripts/server/*` and `scripts/automated_tests/*` chains fully switch to the TOML
  config + `OPUS_CONFIG` model.
- **Check in `tests/fixtures/opus_ci.toml`** (dummy DB creds, tmp-dir paths): the standing
  config for every GitHub-hosted job that must import `opus_app.settings` — mypy/django-stubs
  (PR-14 on), pytest-django collection of `tests/opus_app` (PR-18 on), Sphinx autodoc (PR-21).
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
  Django version it was verified against** (verify against 5.2 as part of this PR). Also
  adopt the modern settings surface here (`STORAGES`, `DEFAULT_AUTO_FIELD`, timezone-aware
  settings, `pathlib` paths) — **make `settings.py` as Django-modern as possible**.
  The migrate step (contrib tables) remains documented and unchanged.
- **Remove the dictionary app**: `Definitions`/`Contexts` models + `get_def_for_tooltip()`
  move to `opus_app/apps/tools/dictionary.py` (imports updated in paraminfo/ui/cart);
  dictionary urls/templates/statics deleted; `do_dictionary.py` import step untouched.
  - **The `favicon` route in `dictionary/urls.py` is deleted with the app — do NOT relocate
    it to the root `urls.py`.** After PR-02 it is the app's only live route, so it can look
    load-bearing; it is not. Verified 2026-08-17: (i) `dictionary.urls` is included only
    under `^dictionary/` and `^__dictionary/` (`application/urls.py`), so it answers
    `/dictionary/favicon.ico`, never the root `/favicon.ico` browsers request; (ii) it
    redirects to `staticfiles_storage.url('favicon.ico')` → `<STATIC_URL>favicon.ico`, which
    **does not exist** (the assets are `static_media/img/favicon.ico` and
    `img/faviconPDS.ico`), so it 302s to a 404; (iii) nothing reverses the `'favicon'` URL
    name and no template references it. The real root favicon is served by the web-server
    config, which is unaffected.
  - **Interaction with `STORAGES` (same PR):** that `staticfiles_storage.url(...)` runs at
    **import time**. If `ManifestStaticFilesStorage` were adopted while this route survived,
    Django would raise at startup because `favicon.ico` is absent from the manifest.
    Deleting the route removes the hazard — another reason not to relocate it.
- `hurry.filesize` call replaced by a local helper. Re-run the PR-07 `_meta` JSON diff under 5.2.

**PR-10: Import pipeline internal cleanup.**
- Split `do_import.py` (1,782 lines) into `steps/` submodules (table prep, mult handling,
  one-index import, observation-table import, main loop) and `config_targets.py` (1,003
  lines — over the limit, split mandatory) by section — all ≤1000 lines.
- Consolidate the ~18 duplicated SCLK try/except blocks into one helper on the mission
  common classes; named constants for magic numbers (wavenumber conversion, angles,
  detector sizes); typo fixes; `NoDupLogger` lists → sets; batch `upsert_rows`.
- **Named bug: the un-prefixed f-string in `steps/do_dictionary.py`** (found during PR-04,
  assigned 2026-08-19). The contexts-file reader logs
  `logger.log('error', 'Bad row in "{ctxfile}": {row}')` — no `f` prefix, so the braces are
  logged literally instead of the offending file and row. **Do not simply add the `f`:**
  `ctxfile` is not a name in scope (the variable is `ctx_file`), so that alone raises
  `NameError` on the error path. Fix both the prefix and the name, and cover the bad-row
  branch with a test.
- **Make `util/` import-safe** (found during PR-04, assigned 2026-08-19). Both surviving
  tools do their work in the **module body**, so merely importing them executes it:
  1. `util/retrieve_ra_dec.py` opens a `requests.Session()` and runs a bare module-level
     `for` loop over ~160 entries in `STARS`, issuing a live HTTP GET per star to
     `http://simbad.u-strasbg.fr/simbad/sim-id`. **Importing this module makes ~160
     external network requests.**
  2. `util/dump_pds_definitions.py` reads `sys.argv[1]` at module level, so importing it
     raises `IndexError`.
  Wrap each in a `main()` plus `if __name__ == '__main__':`, changing no behavior when run
  as a script. **Why it matters beyond tidiness:** these modules now ship inside the
  installed wheel (`src/opus_import/util/`), and **PR-21's Sphinx autodoc imports every
  module** — leaving them as-is would fire the SIMBAD requests during every docs build and
  fail whenever that service is slow or unreachable. Fixing it here removes the hazard
  before PR-21 depends on it. While there, switch the SIMBAD URL to `https://`.
- **Narrow `ImportDBException` from `BaseException` to `Exception`** (`importdb/super.py:4`).
  Ratified 2026-08-17: deriving from `BaseException` is an old mistake, not a deliberate
  design. **This is a control-flow change, not a one-line edit — it must be audited:**
  today `except Exception:` handlers do *not* catch DB failures, so those failures
  propagate to the top-level handler; after narrowing, every intervening `except Exception:`
  will swallow them. Required work:
  1. Audit all `except Exception` sites under `opus/import/` (28 at time of writing) for any
     that sit between a DB operation and the top-level handler. **The critical one is
     `do_import.py:1462`**, which wraps obs field-function calls (`res = func()`): a DB
     failure raised inside a field function would be logged as "field function failed" and
     **the import would continue**, silently producing an incomplete database instead of
     aborting. Any such site must re-raise `ImportDBException` (or catch a narrower type).
  2. Simplify PR-02's defensive `except (Exception, importdb.ImportDBException):` in
     `main_opus_import.py` back to plain `except Exception:` — it exists only because of the
     `BaseException` base and becomes redundant here.
  3. Keep the deliberate `except importdb.ImportDBException: sys.exit(-1)` at
     `main_opus_import.py:449` working (it is unaffected by the base-class change).
  The integration suite gates this; a DB-failure path is not otherwise covered by CI, so
  reason about each audited site statically and record the audit in the PR.

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
  `opus_app/apps/tools/sql_builder.py` (identifier quoting via `connection.ops.quote_name`,
  composable SELECT/JOIN/WHERE assembly, `%s` params for all values). Scope is
  **grep-defined**: every call site under `src/opus_app/apps/**` that *assembles* SQL from
  strings is refactored through the builder. **Preserve the explanatory comments** attached
  to each SQL string — they often document *why* the query is built the way it is and how it
  was designed; carry them onto the refactored builder calls, never drop them. The five
  worst files by volume are
  `search/views.py`, `results/views.py`, `cart/views.py` (which alone has ~15 additional
  sites beyond its big `_get_download_info` region), `metadata/views.py`,
  `tools/file_utils.py` — but the grep, not this list, defines the work.
- **Acceptance (mechanical):** cursor acquisition and `cursor.execute(...)` may remain at
  call sites; constant literal statements with only `%s` placeholders (e.g.
  `search/views.py:1519`) are exempt. The criterion is that no site outside
  `sql_builder.py` builds SQL by string concatenation or interpolation:
  `grep -nE "sql \+=|sql = .* \+ |f['\"].*(SELECT|INSERT|UPDATE|DELETE|CREATE)" -r src/opus_app/apps --include='*.py'`
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
- **Named bug this PR must fix (found during PR-03a, verified 2026-08-18):**
  `src/opus_support/units.py` — `parse_unit_value` guards its result with
  `math.isfinite(ret)`, but `math.isfinite()` raises **`OverflowError`** (not
  `ValueError`) on an int too large to convert to float, e.g. a 400-digit numeric
  string. `OverflowError` is outside the parser's rejection contract and is not caught
  by `views.py`, so a crafted numeric query parameter **escapes as an HTTP 500 where
  rule 2 requires a 400**. PR-03a fixed the sibling instances of this class in
  `angles.py` (its rejections are now uniformly bare `ValueError`) but deliberately left
  this one, since routing it to a 400 is this PR's job. Fix the parser to reject such
  input as a `ValueError` and confirm the endpoint returns 400. Related: the same class
  of "non-`ValueError` escapes a parser" bug is worth grepping for across
  `opus_support`/`app_utils` while doing the rule-5 audit.
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
`[tool.ruff.lint.per-file-ignores]` table is emptied (PR-01's exit criterion), and the
bandit `# nosec`/skip set and the vulture whitelist are reduced to only irreducible,
individually-justified entries.

### Phase E — Test suite

**PR-18: pytest everywhere.**
- **Selection model:** the default run is directory-scoped (`testpaths=["tests"]`), so
  `pytest` alone never touches `integration/`; markers `integration`, `holdings`,
  `livetest` are registered (strict-markers) and used to select *within* an explicit
  `pytest integration` invocation. No `-m` filter in addopts.
- **Django under pytest:** `pytest-django` with `DJANGO_SETTINGS_MODULE=opus_app.settings`
  and `OPUS_CONFIG` (CI fixture TOML for `tests/`, real TOML for `integration/`).
  **DB-lifecycle rule (fixed, not executor-chosen):** integration tests **remain
  `unittest.TestCase` subclasses** (pytest collects them natively and pytest-django does
  not manage the DB for them), preserving today's deliberate no-create/no-teardown
  behavior against the live imported schema; an autouse session fixture in
  `integration/conftest.py` uses `django_db_blocker.unblock()` for the session.
  **`@pytest.mark.django_db` is forbidden in `integration/`** (it would wrap tests in
  transactions or, with `transaction=True`, flush the freshly imported schema) — a
  conftest collection hook asserts no integration test carries it.
- `tests/opus_app/` (holdings-free Django unit tests — request parsing, pure helpers,
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
- `run-tests.yml` final form for this phase: ruff + mypy + bandit + vulture + pymarkdown
  (README/CONTRIBUTING/.cursor — `docs/` joins in PR-21) + pytest matrix (3.12/3.13) with
  codecov upload, all on `ubuntu-latest`. **Coverage gate: ≥90% via
  `--cov=opus_support --cov=opus_config --cov=opus_import --cov=opus_log_analyzer`**
  (`src/opus_app` excluded — owned by the integration 100% gate).

**PR-20: Integration workflow consolidation.**
- `run-integration.yml` (successor of `run-app-tests.yml`): unchanged philosophy —
  self-hosted runner, real holdings, fresh `opus_test_db_<id>`,
  `scripts/import/import_for_tests.sh` bundle list, golden-response API suite,
  DB-integrity checks, **100% coverage gate kept with its current scope** (via
  `integration/.coveragerc`, §5a, including the `tests/opus_support` contribution per
  PR-18) — invoked through pytest and the TOML config. Nightly cron + on-demand; PRs run
  it too (as today; still triggering on `rewrite` until PR-24).

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
  `conf.py` for the `opus_app.*` modules). `CODE_OF_CONDUCT.md` moves under `docs/`. Builds
  clean under `-W` and `-n`. **ReadTheDocs timing:** the RTD site **cannot go live until
  `rewrite` is merged to `main` (PR-24)** — so this PR (and PR-22) must not depend on a
  live RTD site. The sub-agent commits `.readthedocs.yaml` and the RTD URLs (GUI link,
  `apiguide.pdf` redirect target) and verifies the docs build clean locally, but the
  checks that require the live site — the RTD guide actually resolving and the GUI menu
  item opening it — are **manual, post-merge acceptance checks** performed by the
  orchestrator after PR-24 (see §6). The `apiguide.pdf` 302 + `Location` target is asserted
  in CI without the site being live.
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
- Console scripts in `[project.scripts]`, **underscore names**, all shipped in the wheel
  (`include` the packages): `opus_import = opus_import.cli:main`,
  `opus_log_analyzer = opus_log_analyzer.log_analyzer:main`, and
  `opus_error_analyzer = opus_log_analyzer.error_analyzer:main` (both log-analyzer modules
  created by PR-06) alongside the `python -m opus_import` / `python -m opus_log_analyzer`
  forms. **These installed commands are the top-level programs used on the server to
  import and deploy a new database** — the `scripts/server/import_and_deploy/*` and
  `scripts/automated_tests/*` chains invoke them by name (no repo-relative paths, no bare
  `python -m` in the server chain). Package data audit (table_schemas, templates, static, help md/yaml,
  pdsdd.full, contexts.csv, Jinja templates, `py.typed` markers); `requirements.in/txt`
  deleted (deps live in pyproject; deploy pins via a `constraints.txt` generated at
  release if ops wants one).
- `scripts/server/import_and_deploy/*` rewritten for the pip flow: venv + `pip install
  rms-opus` (PyPI), the new `opus.toml` config file created and `OPUS_CONFIG` exported per
  install, **`django-admin migrate`** (Django contrib tables;
  `DJANGO_SETTINGS_MODULE=opus_app.settings`), `collectstatic`, Apache mod_wsgi pointing at
  installed `opus_app.wsgi`; the import step runs the installed `opus_import` command. The
  shell-script-level variables currently sourced from `_read_opus_secrets.sh` move to an
  explicit `deploy.env` consumed only by the shell chain (documented as deploy
  infrastructure, distinct from app config).
- PyPI publishing live: version tag on `main` → GitHub Release → `publish_to_pypi.yml`
  (first release cut after the merge PR); Test PyPI dry-run from the rewrite branch first.
  (PyPI ownership of the `rms-opus` name and the `PYPI_API_TOKEN`/`TEST_PYPI_API_TOKEN`
  repo secrets are confirmed in place — no verification step needed.)
- **Final acceptance test** (see §6) on a clean machine/venv.

**PR-23: Enforce `ruff format` (format-only, final phase).**
- Deliberately the **last content PR** so the large, purely mechanical formatting diff
  never collides with any logic PR's review.
- In one commit: flip `ENABLE_RUFF_FORMAT=true` in `run-all-checks.sh` and enable the
  previously-disabled `ruff format --check` step in `run-tests.yml`.
- In a **separate, format-only commit** (no logic changes): run `ruff format` across the
  whole in-scope tree (`src/`, `tests/`, `integration/`, and `docs/` code; `perf_test/`
  stays excluded per pyproject).
- Both workflows green; **zero golden-fixture diffs** — formatting touches only Python
  source, never `integration/test_api/responses/*`. The adversarial pre-PR review (§4a)
  confirms the second commit is formatting-only.

**PR-24: Merge `rewrite` → `main`** after a full integration run, a production-style
deploy rehearsal, and a final `run-all-checks.sh` pass. Workflow branch filters narrowed
back to `main`. **Post-merge manual acceptance (RTD only goes live after this merge):**
the orchestrator creates/enables the ReadTheDocs project, then manually verifies the live
RTD guide resolves, the GUI "API Guide" menu item opens it, and `apiguide.pdf` redirects
to a reachable page (§6). First release tag (`v3.23.00`, continuing the existing scheme)
and PyPI publish follow.

---

## 5. CI evolution timeline

| Stage | GitHub-hosted | Self-hosted |
|---|---|---|
| Today | flake8 only (main-only triggers) | full import + Django tests (holdings, 100% gate; main-only triggers) |
| After PR-01 | ruff + bandit; **both workflows trigger on `rewrite`** | unchanged behavior, now gating rewrite PRs |
| After PR-02 | + vulture (enabled after the dead-code removal) | unchanged |
| After PR-03 | ruff + pytest (`tests/`, no DB) | green via explicit run_coverage.sh/.coveragerc/pip-install-e fixes |
| After PR-08 | + `OPUS_CONFIG=tests/fixtures/opus_ci.toml` available to all jobs | secrets → TOML |
| After PR-19 | ruff + mypy + bandit + vulture + pymarkdown + holdings-free pytest w/ MySQL container; 90% gate over the four non-Django packages | unchanged |
| After PR-20 | same | pytest-driven integration, 100% gate kept |
| After PR-21 | + Sphinx docs-build job; pymarkdown covers `docs/` | same |
| After PR-23 | + `ruff format --check` enabled (the format-only PR) | same |

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
  list `src/opus_app/apps/*`, `integration/test_api/*`, `src/opus_support/*` (migrated from
  today's `opus/application/.coveragerc` in PR-05); gate 100% via `opus_check_coverage.sh`.

---

## 6. Verification

Per-PR: `scripts/run-all-checks.sh` locally; both workflows green; move-PRs verified by
integration suite passing with zero golden-fixture diffs (except the sanctioned ones:
PR-13's status-code changes, each traceable to its decision table, and PR-21's API-guide
fixture removal + redirect).

End-to-end acceptance (PR-22/PR-24, on a clean venv, no repo checkout on path):
1. `pip install <built wheel>`; `OPUS_CONFIG=/path/to/opus.toml python -m opus_import --do-it-all <test bundles>` against a fresh MySQL schema → zero ERRORS.log entries; `--validate-perm` clean.
2. `python -m opus_import --help` surface identical to the old CLI (documented diff otherwise).
3. `django-admin migrate` (`DJANGO_SETTINGS_MODULE=opus_app.settings`) + serve `opus_app.wsgi` (mod_wsgi or gunicorn smoke run) against that schema; golden API suite passes against the live server, including `api/metadata_v2/...` and ringobsid conversions; `apiguide.pdf` returns HTTP 302 with its `Location` pointing at the RTD guide URL (asserted **without** the RTD site being live). **Manual, post-merge (RTD only goes live after PR-24):** confirm the live RTD guide resolves and the GUI "API Guide" menu item opens it.
4. The installed `opus_log_analyzer` and `opus_error_analyzer` console commands both run; `opus_log_analyzer` produces a report from a sample log using packaged templates and the packaged default configuration module.
5. `pytest` (default, no holdings, no DB beyond the container) green with `-n auto`; coverage ≥90% over the four non-Django packages.
6. `sphinx-build -W -n` clean; `mypy` strict clean; `ruff check` clean with an empty per-file-ignores table; `ruff format --check` clean (enabled in PR-23); `bandit` and `vulture` clean.

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
- **log_analyzer scope addition** → 2,955 lines, the least-explored codebase now in scope; PR-06 is a pure move with pre-identified landmines fixed (config-module default no longer resolves once packaged — fixed to the absolute `opus_log_analyzer.opus.configuration`, with no confusion with the renamed Django `opus_app` package; two top-level programs `log_analyzer.py`/`error_analyzer.py` kept, neither renamed to `cli.py`; cron templates), and its lint/type/test debts are absorbed by the existing phase structure.

## 8. Self-critique (known weak points of this plan)

- **PR-05 is the riskiest PR** (every import line in the Django app changes) and is deliberately executed as a single PR — a partial per-app split would require both import roots resolvable simultaneously (new sys.path shims), which this plan bans. Mitigation is the strict move/modify commit separation: the rename commit and the rewrite commit are reviewed independently, and the rewrite commit is almost entirely mechanical (`import settings` → `from django.conf import settings`; bare app names → `opus_app.apps.*`).
- **The mini-holdings fixture spike (PR-19)** was the plan's largest unknown; it is now specified as subset-don't-synthesize with a mechanical success criterion, the PR-02 `require_shelves` prerequisite, and a time-boxed, pre-specified fallback — the residual risk is pdsfile's directory-acceptance logic, which the fallback covers.
- **Phase ordering trade-off:** types (Phase D) land before the full test suite (Phase E). Mitigated by PR-16's two-layer test (schema check + behavioral smoke per mission), opus_support tests landing early (PR-03), and the GitHub pytest job running from PR-03 on.
- **`ImportContext` (PR-11) is a wide mechanical diff** across every do_* module and many obs methods; the fixed threading pattern removes design latitude but not volume. The alternative (keep impglobals, wrap in accessors) was rejected as not actually fixing testability.
- **Estimate honesty:** PR-12 (SQL consistency, grep-scoped) and PR-17 (Django annotations) are each large; if they stall, they can be subdivided by app without breaking the sequence. PR-16's mult-return normalization commit touches many obs modules and leans on integration CI as its oracle.

---

## Execution notes (append-only; see §4a)

*Each executing sub-agent adds dated bullets here — in its own PR — for any fact later
PRs need (spike outcomes, validation results, forced deviations). Never rewrite the plan
body; never rewrite or delete earlier notes.*

- **2026-08-16 (pre-PR-01, orchestrator plan-body amendment after a stop-and-report):**
  the PR-01 ruff burn-down seed (`E722/F403/F405/N8xx/E501`) predated ruff's `PT`/`B`
  categories. Verified counts (ruff 0.15.7, scope `lib opus/import opus/application/apps
  log_analyzer`, select per plan): `PT009`×1023, `PT027`×215, `PT015`×27, `B011`×27,
  `B006`×3, `PT018`×3, plus `B007`×17/`B904`×24/`B905`×7/`B019`×2/`B023`×2 and the
  legacy-ignore codes `E501`×965/`F405`×19/`E722`×14/`F403`×4 (`N` fires 0×). Resolution
  (now in the PR-01 burn-down text): `PT009`+`PT027` → documented global
  `[tool.ruff.lint] ignore` (the live-DB integration tests stay `unittest.TestCase`
  permanently per PR-18, so these never burn down); `PT015`/`B011`/`B006` → per-file
  grandfather removed in **PR-02** when the `assert False`→`NotImplementedError` and
  `ImportDBSuper.__init__` mutable-default fixes land; `PT018` and everything else fixed in
  PR-01. PR-17's empty per-file-ignores-table exit criterion is unchanged and still holds.
  Bandit (142 findings, incl. 5×`B324` HIGH, 18×`B608`/PR-12, 4×`B610`/PR-09) uses its
  sanctioned `# nosec`/skips valve, unaffected.
- **2026-08-16 (PR-01 executed):** facts later PRs rely on:
  - **`N801`/`N802` actually fire** (`N802`×24 invalid-function-name, `N801`×7
    invalid-class-name; ruff 0.16.3) — the earlier "`N` fires 0×" reading was contaminated
    by a since-removed seed. Both are `N8xx`, authorized for the legacy seed, so they are
    grandfathered in the `lib/**`, `opus/**`, `log_analyzer/**` per-file-ignore globs and
    retired by PR-17 with the rest of that table.
  - **Lint scope (pre-move):** ruff runs on `lib opus/import opus/application/apps
    log_analyzer` (historical flake8 scope + log_analyzer); bandit on `lib opus
    log_analyzer` with `exclude_dirs` for `test_api`/`test_perf`/`test_db_data`/`perf_test`.
    These paths live in `run-tests.yml` (`RUFF_PATHS`/`BANDIT_PATHS` env), `pyproject.toml`
    (`[tool.bandit].targets`, `[tool.ruff.lint.per-file-ignores]` globs), and
    `run-all-checks.sh` (`OPUS_RUFF_PATHS`/`OPUS_BANDIT_PATHS`); **each move PR (PR-03..06)
    must shift them toward `src/`.** `opus/application/{settings,urls,manage,
    clear_django_cache}.py`, `test_api/`, `test_db_data/`, `test_perf/` are NOT yet
    ruff-scoped (as under flake8) and get linted when they move.
  - **Bandit burn-down:** `B324` (5× weak-MD5 cache keys in `search/views.py`) fixed
    in-code with `usedforsecurity=False` (not skipped). A category `skips` list
    (`B101,B105,B110,B113,B301,B311,B403,B404,B506,B603,B607,B608,B610,B704`) is in
    `[tool.bandit]`, each justified; PR-17 shrinks it to per-line `# nosec`, PR-09 removes
    the `B610` `.extra()` sources, PR-12 addresses `B608`. (`B105` was the `'XXX'`
    placeholder in `apps/dictionary/secrets_template.py`, deleted in PR-08 — not a real
    secret.)
  - **PR-02 hand-off — the 3 grandfathered `B006` (mutable-default) sites** are:
    `opus/import/importdb/super.py` (`ImportDBSuper.__init__`),
    `opus/import/import_util.py` (`read_schema_for_table(..., replace=[])`), and
    `opus/application/apps/tools/file_utils.py`. PR-02 must fix all three before
    removing the per-file `B006` ignores, else `ruff check` fails. `PT015`/`B011`
    (`assert False`) are grandfathered in `super.py`, `mysql.py`, `util/
    obs_table_to_schema.py`, `util/dump_pds_definitions.py`,
    `obs_volume_hstix_xxxx.py`, and `log_analyzer/opus/query_handler.py`.
  - **`B019` fixes (behavior-preserving, integration-CI-gated):** `importdb/mysql.py`
    `table_info` `@cache`→instance dict `self._table_info_cache` (cleared where the two
    `.cache_clear()` calls were); `log_analyzer/ip_to_host_converter.py` `convert`
    `@functools.cache`→instance dict `self._convert_cache` (a base `__init__` was added).
  - **Tooling/CI shape:** the package is NOT pip-installable until `src/` exists (PR-03),
    so the `run-tests.yml` lint job installs `ruff`/`bandit`/`pymarkdownlnt` directly, not
    `pip install -e ".[dev]"`. `pyroma` passes 10/10 already and is enabled in
    `run-all-checks.sh`; `pytest`/`sphinx` ENABLE flags are `false` there until PR-03/PR-21
    create `tests/`/`docs/`. `run-tests.yml` keeps a disabled `ruff format` step
    (`ENABLE_RUFF_FORMAT` env `false`) for PR-23.
  - **SIM118 regression on a duck-typed object (found by integration CI, fixed):**
    the burn-down rewrote `for item_name in label.keys():` →
    `for item_name in label:` in `opus/import/do_dictionary.py`, but `label` is a
    `pdsparser.PdsLabel` — dict-*like* (`.keys()`/keyed `__getitem__`) but with no
    `__iter__`, so bare iteration falls back to integer indexing and raises
    `KeyError: 0`, crashing the dictionary import. Restored `.keys()` with a
    targeted `# noqa: SIM118` + explanatory comment (not a per-file-ignore, to keep
    the PR-17 table clean). **Lesson for later PRs:** lint autofixes that remove
    `.keys()/.values()/.items()`, introduce `.get()`, or change membership/`in`
    tests can silently break on custom dict-like objects (pdsparser, DB rows); the
    holdings-free lint job cannot see it — only integration CI can. A full audit of
    every such autofix in this PR confirmed the other five `.keys()` removals
    (`value_to_sessions` defaultdict, `self._session_search_slugs` dict,
    `PREVIEW_SIZE_TO_PDS_TYPE` dict ×2, `rows[0]` csv.DictReader row) and every new
    `.get()` (`extras`, `original_slugs`, `sub_headings`, `UNIT_FORMAT_DB`, `query`)
    are on genuine `dict`s; SIM103/SIM102/C4 changes are type-preserving.
  - **Branch protection:** the new `run-tests.yml` lint job is deliberately named
    **`Run Lint`**, so the existing required-status-check context `Run Lint` is preserved
    (no `rewrite` protection edit needed); `Test OPUS (self-hosted-linux, 3.12)` is
    unchanged.
- **2026-08-16 (PR-02 executed):** facts later PRs rely on:
  - **Vulture is enabled.** Config is `[tool.vulture]` in `pyproject.toml`
    (`min_confidence = 70`, `exclude = ["*/perf_test/*"]`, `paths = ["lib", "opus",
    "log_analyzer", "vulture_whitelist.py"]`). Like `RUFF_PATHS`/`BANDIT_PATHS`, the vulture
    scan paths live in **three** places that each move PR (PR-03..06) must shift toward
    `src/`: `run-tests.yml` (`VULTURE_PATHS` env), `pyproject.toml` (`[tool.vulture].paths`),
    and `run-all-checks.sh` (`OPUS_VULTURE_PATHS`). `vulture_whitelist.py` is always included
    as an input path so whitelisted names count as used. At min-confidence 70 vulture only
    reports unused **imports** (90%) and **unreachable code** (100%) tree-wide — unused
    functions/classes/vars/attrs/args are 60% and below the gate — and a name is only flagged
    when it appears nowhere else in the scanned set, so scanning the whole tree (including the
    integration test suites) suppresses most argument/name false positives.
  - **`vulture_whitelist.py` contents:** a single entry, `lineno` — the unused positional
    parameter required by the `warnings.showwarning` callback signature in
    `opus/import/importdb/super.py` and `opus/import/main_opus_import.py` (handlers use only
    `message`). PR-17 shrinks the whitelist to individually-justified entries; this is already
    minimal.
  - **Per-file-ignores table shrank:** the PR-01 `PT015`/`B011`/`B006` grandfathers were
    removed after the `assert False`→exception and mutable-default fixes landed. The
    `[tool.ruff.lint.per-file-ignores]` table now holds **only** the legacy-refactor codes
    (`E722, E501, F403, F405, N801, N802`) on the `lib/** opus/** log_analyzer/**` globs,
    retired by PR-17. `assert False`→`raise NotImplementedError(...)` everywhere except
    `util/dump_pds_definitions.py`, whose bad-input branch became `raise ValueError(...)` per
    the plan's "replaced by a real error" wording for that file.
  - **Shelf-requirement fix landed (PR-19 prerequisite):** `Pds3File.require_shelves(True)`
    now lives **inside** the `if not ARGUMENTS.dont_use_shelves_only:` block in
    `main_opus_import.py`, so `--dont-use-shelves-only` runs from the real filesystem without
    requiring shelves. Default behavior (shelves used and required) is unchanged.
  - **Files deleted this PR** (so later PRs don't expect them): OPUS2-porting-only
    `opus/import/util/{get_opus2_mults.py, obs_table_to_schema.py,
    create_all_obs_table_schemas.sh, dump_param_info.sql, master_labels/}`, the
    fully-commented `opus/application/apps/dictionary/admin.py`, and `perf_test/stream_c.exe`.
    Kept: `util/dump_pds_definitions.py`, `util/retrieve_ra_dec.py`. The DB-backend
    abstraction (`importdb/postgresql.py`, `db_brand` in `get_db()`, `DB_BRAND`) was left
    intact per the decisions table.
  - **Exception/handler landmines in `opus/import` that Phase C's error-handling and
    logging work (and any future `except:` cleanup) must know about:**
    1. **`ImportDBException` derives from `BaseException`**, not `Exception`
       (`importdb/super.py`), and `importdb/mysql.py` raises it in ~15 places with no
       handler except the narrow one around `get_db()`. A blanket bare-`except:` →
       `except Exception:` conversion therefore **silently stops the top-level "always log"
       handler in `main_opus_import.py` from catching it** (DB failures escape unlogged,
       exit code changes). PR-02 preserved behavior with an explicit
       `except (Exception, importdb.ImportDBException):`; the `BaseException` base class was
       left unchanged (out of scope). Narrowing that base class is a candidate for the
       Phase C error-handling PR — if it is changed to `Exception`, the explicit tuple can
       be simplified.
    2. **The warning-handler install/restore was asymmetric.** `ImportDBSuper._enter()`
       saves+installs `warnings.showwarning` **only `if self.logger:`**, but `_exit()`
       restored it **unconditionally** — so with `logger=None` it assigned
       `warnings.showwarning = None` and the next `warnings.warn()` raised
       `TypeError: warnings.showwarning() must be set to a function or method`. This was
       **latent until PR-02 fixed the `showarning` typo** (the misspelling made the restore
       a no-op on a bogus module attribute), i.e. the typo fix activated the bug. Fixed in
       PR-02 with an explicit `_warning_handler_installed` flag. Integration CI cannot reach
       it (the pipeline always passes a logger). **Lesson:** fixing a typo can activate dead
       code — audit what the misspelled statement was silently *not* doing.
    3. **Pre-existing (NOT introduced by PR-02, left for Phase C):** `ImportDBSuper._exit()`
       is never called from a `finally`. `read_rows()` and `table_exists()` call
       `_enter()` … `_exit()` bare, while `_execute_and_fetchall()` raises
       `ImportDBException` in ~15 places in `mysql.py`. On that path `_enter_stack` stays
       non-empty, the warning handler stays installed process-wide, and
       `_warning_handler_installed` stays stale-`True`. Impact today is nil (the process
       exits shortly after via the top-level handler, and there is a single
       `impglobals.DATABASE` instance), and PR-02's flag does not make it worse. The
       related non-LIFO multi-instance clobber (`a._enter(); b._enter(); a._exit()`) is
       likewise pre-existing and currently unreachable. **Phase C fix:** wrap the
       `_enter`/`_exit` pairs in `try/finally` or turn them into a context manager.
  - **`instruments.py`** `PDSTABLE_PREPROCESS`/`PDSTABLE_REPLACEMENTS` are now empty lists
    (only commented-out hook entries remained); both are still referenced by
    `import_util.py` (`PDSTABLE_REPLACEMENTS` is iterated; `PDSTABLE_PREPROCESS` only in a
    commented loop) and are below vulture's confidence gate.
- **2026-08-17 (PR-03 executed):** facts later PRs rely on:
  - **`opus_support` layout.** `src/opus_support/` holds the five domain modules the plan
    names (`sclk.py`, `orbits.py`, `time_parsing.py`, `angles.py`, `units.py`) **plus a
    sixth, private `_numeric_text.py`** holding `_strip_trailing_zeros` and
    `_clean_numeric_field`. Those two helpers *had* to leave `units.py`: `units` imports
    the angle parse/format functions for `UNIT_FORMAT_DB` while `angles` needs the
    helpers, which sat in the units section — a cycle. Giving them their own module
    rather than parking them in `angles.py` (which would also have been acyclic) keeps
    `angles` about angles. Dependency graph: `units` imports `angles`, `orbits`, `sclk`,
    `time_parsing` and `_numeric_text`; `angles` imports `_numeric_text`; the other four
    are leaves.
  - **The public surface is unchanged and re-exported in full.** `__init__.py` imports all
    49 public names and lists them in `__all__` (`__all__` is also what keeps vulture from
    flagging the re-exports). Verified against the pre-split module: same 49 names, none
    added or missing, every public callable byte-identical, `UNIT_FORMAT_DB` deep-equal
    including key order and every parse/format slot. `from opus_support import X` works
    exactly as before on both sides; **later PRs should keep importing from the package
    root, not from the submodules.** The five underscore helpers
    (`_parse_multi_field_sclk`, `_format_multi_field_sclk`, `_parse_dms_hms`,
    `_strip_trailing_zeros`, `_clean_numeric_field`) are deliberately *not* re-exported.
  - **isort reclassification is a standing landmine for PR-04/05/06.** As soon as a tree
    lands under `src/`, ruff's isort reclassifies it from third-party to first-party, so
    every importing file's import block must be re-sorted **in the same PR** or the lint
    job fails. PR-03 hit this on all 22 `opus_support` importers; the fix is
    `ruff check --select I --fix <paths>` in the rewrite commit. It is a pure reordering,
    but audit it under the §4a semantics lens anyway (PR-03's audit: `opus_support` has no
    import-time side effects beyond `DEG_RAD = np.degrees(1)` and literal dicts, and it
    imports none of the modules it now follows).
  - **`opus_config` shim API (PR-04 and PR-05 consume it; PR-08 deletes it).**
    `from opus_config._secrets_compat import load_secrets` returns the executed
    `opus_secrets.py` as a module object, cached with `functools.cache`; every setting is
    an attribute on it. `secrets_path()` exposes the resolution: `OPUS_SECRETS` (an
    absolute path to the **file**, not its directory) first, then `opus_secrets.py` in the
    process CWD. The module is deliberately **not** registered in `sys.modules`, so a
    leftover `import opus_secrets` still fails loudly. A missing file raises
    `FileNotFoundError`. PR-08 must delete `tests/opus_config/test_secrets_compat.py` and
    `tests/opus_config/conftest.py` along with `_secrets_compat.py`.
  - **`RMS_OPUS_LIB_PATH` is entirely gone** — both `sys.path.insert` calls, the
    definition in `opus_secrets_template.py`, and the two shell generators that echoed it.
    No executable reference remains (a repo-wide grep hits only explanatory comments and
    the planning docs). The **remaining** `sys.path` inserts belong to the moves that own
    them: `main_opus_import.py` (`RMS_OPUS_ROOT` for `opus_secrets`, and `PROJECT_ROOT`)
    is PR-04's, and `settings.py` (`PROJECT_ROOT`, `RMS_OPUS_ROOT`, `apps/`) is PR-05's.
  - **`pip install -e .` is now required to run anything.** It was added to
    `run-app-tests.yml` (after the `requirements.txt` install; nothing is upgraded because
    every pyproject bound is already satisfied), and to the two deploy scripts that build a
    venv, `scripts/server/import_and_deploy/deploy_new_code_only.sh` and
    `_opus_setup_environment.sh`. `scripts/automated_tests/*` does not install anything
    itself and relies on the workflow. Confirmed that a shallow, tag-less checkout still
    builds: setuptools-scm falls back to a `0.1.devN` guess-next-dev version rather than
    failing. Do not rely on the exact fallback string.
  - **Tool scope paths after this PR** (still the same three files each move PR must
    update): ruff `src opus/import opus/application/apps log_analyzer tests`; bandit
    `src opus log_analyzer` (tests are never bandit-scanned); vulture
    `src opus log_analyzer tests vulture_whitelist.py`. The `lib/**/*.py` row is gone from
    `[tool.ruff.lint.per-file-ignores]`, which now holds only `opus/**` and
    `log_analyzer/**`; **no `src/**` row was added and none should be** — code is brought
    up to the full rule set as it moves.
  - **Vulture found one masked dead import** when its scope widened from `lib` to `src`:
    `import unittest` in `opus/application/test_api/test_help_api.py` (the file uses only
    `from unittest import TestCase`). It had been suppressed because the inline test
    classes in `lib/opus_support.py` referenced the name. Expect similar unmaskings as
    each remaining tree moves.
  - **pytest configuration, and the one dependency-skew trap it exposed.**
    `[tool.pytest.ini_options]` sets `filterwarnings = ["error"]`, with exactly one
    narrowly-scoped exception. **The GitHub-hosted and self-hosted jobs do not run the
    same dependency versions**: the unit job installs `.[dev]` (unpinned, so latest),
    while the integration runner installs `requirements.txt` (pinned). Under the pins
    (`rms-julian==3.0.1`, `pyparsing==3.3.1`) merely importing `julian` raises
    `DeprecationWarning: 'setParseAction' deprecated`, because julian builds its date
    grammar with pyparsing's camelCase compatibility synonyms at import time. That turned
    every `tests/opus_support` collection into an error on the self-hosted runner while
    the GitHub job (which gets `rms-julian` 3.0.2, where it is fixed) was green. The
    filter `"ignore:'setParseAction' deprecated - use 'set_parse_action':DeprecationWarning"`
    covers it, naming that one message rather than the whole category (verified by
    capturing every warning `import julian` raises under those pins: five instances of
    that single message, nothing else); **it becomes removable when
    `requirements.txt` moves past `rms-julian` 3.0.1** (a candidate for PR-22's
    dependency work). **Lesson for later PRs: a pytest-config or dependency change that
    is green on the GitHub job can still fail the integration runner purely on pinned
    versions — reproduce with a venv built from `requirements.txt` before trusting it.**
    `ENABLE_PYTEST` in `run-all-checks.sh` is `true`.
    `[tool.ruff] exclude` now lists `src/opus_config/_version.py` (setuptools-scm writes it
    at build time and it is git-ignored, so a local editable install would otherwise fail
    `ruff check src`).
  - **New CI job.** `run-tests.yml` gained `Unit Tests (3.12)` / `Unit Tests (3.13)`. No
    workflow or job was *renamed*, so the `rewrite` branch-protection contexts (`Run Lint`,
    `Test OPUS (self-hosted-linux, 3.12)`) are unchanged; the new job is not a required
    check. PR-19/PR-20 should add it to the required contexts when they rename the
    workflows.
  - **The integration 100% gate now covers `src/opus_support/*`.** `run_coverage.sh` begins
    with `coverage erase` (the old first command implicitly reset the data file; the new one
    appends) and runs `coverage run -a -m pytest ../../tests/opus_support`;
    `opus/application/.coveragerc` includes `*/src/opus_support/*`. Verified by running
    that exact sequence from `opus/application`: all six package modules at 100% statements
    and 100% branches, with no test file measured. **Any change to `opus_support` in a later
    PR must keep it at 100% or the self-hosted gate fails.**
  - **Four latent defects in the moved `opus_support` code, found by CodeRabbit on the
    PR-03 review and deliberately NOT fixed here** (PR-03 is a pure move; changing any of
    them alters behavior, which a move PR must not do, and the integration suite could not
    distinguish a fix from a regression in the same diff). **No PR in the plan owns
    `opus_support` bug fixes, so the orchestrator must assign these** — the natural home is
    a small dedicated PR, or PR-14 (which is already the only PR that opens these files):
    1. **`units.py` `wavenumber_resolution` loses two unit aliases to missing commas.**
       In both conversion entries a suffix list has adjacent string literals with no comma
       (`'cm^-1perpixel'` / `'cm**-1/p'`, and `'m^-1perpixel'` / `'m**-1/p'`), so Python
       concatenates them: the list holds `'cm^-1perpixelcm**-1/p'` and neither original
       alias. `parse_unit_value` matches user-typed suffixes against these lists, so
       `1 cm^-1perpixel` and `1 cm**-1/p` are not recognized and the fused entry can never
       match. **User-visible.** Fixing it needs a test that parses one suffix per alias
       list.
    2. **`angles.py` fallback "N N N" regex has an unescaped dot.** The last group is
       `(\d+(|.\d*))`, so `.` matches any character and inputs like `'1 30 36 5'` or
       `'1 30 36a5'` reach `float(second)`, which raises a `ValueError` carrying CPython's
       conversion message. Every other rejection in that function raises a bare
       `ValueError`, and `tests/opus_support/test_angles.py` asserts that empty-message
       contract, so fixing the regex changes which message those inputs produce.
    3. **`orbits.py` `parse_cassini_orbit` has an unreachable raise and reports a mangled
       value.** The `raise ValueError(f'Invalid Cassini orbit {orbit}')` sits inside the
       `try` whose own `except ValueError: pass` swallows it, and `orbit` is later rebound
       to the stripped string, so `'0002'` reports `Invalid Cassini orbit 2`.
    4. **`sclk.py` `_parse_multi_field_sclk` has a no-op statement.** `parts[-1]` is
       evaluated and discarded where the comment says the empty final field is deleted.
       Output is unchanged (the padding loop pads the empty field anyway), so it is dead
       code that PR-02 missed — vulture does not flag bare expression statements.
  - **No `py.typed` marker yet.** `[tool.setuptools.package-data]` already globs for it, but
    `opus_support`/`opus_config` carry no annotations until PR-14; shipping the marker now
    would tell downstream type-checkers to trust an untyped package. **PR-14 adds
    `src/opus_support/py.typed` and `src/opus_config/py.typed` with the annotations.**
- **2026-08-18 (PR-03a executed):** all four defects from the PR-03 bullet above are fixed;
  facts later PRs (especially PR-14, which reopens these files) rely on:
  - **PLAN PREMISE CORRECTED (stop-and-report, resolved in this PR).** PR-03a item 2 states
    "every other rejection in that function raises a bare `ValueError`". That was **false**:
    `_parse_dms_hms` had *three* non-conforming rejection paths, not zero, and escaping the
    dot alone would have left all three. The plan's decision ("bare ValueError for all
    rejects", preferred — "the fix must route these through the same raise") was adopted
    anyway, which required fixing all three:
    1. the trailing `float(s)` leaked CPython's "could not convert string to float" text;
    2. `float(degrees_hours)` leaked the same text, because the leading-component regex
       admits an exponent and a fraction together (`'1e5.5d'`) which `float()` rejects —
       **reachable from the public search API**, e.g.
       `parse_unit_value('1e5.d', '.3f', 'longitude', 'dms')`;
    3. a degrees/hours or minutes field long enough to overflow to infinity reached
       `int(...)` and raised **`OverflowError`**, which `apps/search/views.py` does not
       catch (it catches `ValueError` only) — an escaping 500. Fixed by ordering the
       finiteness/range check before the integrality check in both fields.
    All three now produce a message-less `ValueError`. The two `float()` sites use
    `raise ... from err`, so their detail survives as `__cause__`; the overflow fix is a
    statement reorder, so those rejections have `__cause__ is None` and the `OverflowError`
    text is simply gone. `str(exc)` is `''` on every path.
    **Verified by probe: 250,656 probes
    (four public parsers × three conversion factors × 20,888 inputs) produced zero
    non-bare and zero non-`ValueError` rejections**; an independent reviewer sweep of
    240,040 probes (12,002 inputs incl. unicode digits, NUL, 100,000-digit fields) found
    223,405 rejections and zero contract violations. The contract covers *rejected values*
    only: a non-`str` argument raises `AttributeError`/`TypeError`, and
    `conversion_factor=0` raises `ZeroDivisionError` on the DMS/HMS paths that divide by it
    (the plain-number fallback never divides, so it returns the value unchanged). Neither
    is production-reachable — `views.py` always passes a `str` and `UNIT_FORMAT_DB` only
    ever supplies `1`, `1.` or `DEG_RAD`. **What the log loses:** `url_to_search_params`
    (`apps/search/views.py:799-807`) logs `str(e)` and returns, so it never renders a
    traceback and the chained `__cause__` reaches no operator; its line still names the
    whole offending input, but no longer the failing sub-field (it was
    `could not convert string to float: '36 5'` for the input `'1 30 36 5'`). Judged an
    acceptable price for one contract. **Later PRs must keep this single contract**; do
    not reintroduce a message, or any other exception type, on a `_parse_dms_hms`
    rejection path.
  - **The dot fix also narrows what `_parse_dms_hms` ACCEPTS, by design.** A `"N N N"`
    triple whose seconds field was `\d+<any char>\d*` and happened to be a valid float in
    `[0, 60)` used to parse: `'1 30 36e0'` → 1.51, `'0 0 0_5'` → 5 seconds, `'0 0 59E0'` →
    59 seconds. Those spellings were only ever reachable *through* the bug (the DMS regex
    proper never allowed an exponent or a digit separator in seconds) and now raise.
    Differential sweep old-vs-new over 128,768 probes: **0 value differences on inputs both
    accept and 0 reject→accept**; the only exception-type change is `OverflowError`→
    `ValueError`. The accept→reject set is **infinite, not enumerable**; every member has
    shape `N N N<non-dot><digits>` with a seconds text that parses as a float in `[0, 60)`,
    minutes below 60 and a finite leading field. (That shape is a *superset* — `'1 90 36e0'`
    matches it but was already rejected for its minutes. Corpus counts varied: 5 distinct
    instances here, 16 and 195 in two independent reviewer corpora; treat the shape, not
    any count, as the characterization.)
    `tests/opus_support/test_angles.py::test_parse_angle_rejects_malformed_triple`
    pins this across all four parsers.
  - **`parse_cassini_orbit` reports the caller's original input**, not the `'0'`-stripped
    name (`'0002'` → `Invalid Cassini orbit 0002`, not `... orbit 2`), and its raise for a
    numeric orbit below 3 is now reachable. Side effect worth knowing: an orbit passed as an
    `int` rather than a `str` now raises that `ValueError` instead of dying on `int.upper`
    with an `AttributeError`. It has **three** reachable consumers, not one:
    `field_obs_mission_cassini_rev_no_int` (`obs_cassini_common.py:510`), the import
    display-order dispatch (`do_import.py:410,449`), and the **web search API**
    (`table_schemas/obs_mission_cassini.json:106` declares
    `"pi_form_type": "RANGE:range_cassini_rev_no"` → `views.py:762` `parse_unit_value` →
    the `UNIT_FORMAT_DB` parse-func dispatch). All three are safe — the web path only ever
    passes a `str`, and the other two catch `Exception` — but the reworded message now
    surfaces in the OPUS search log and the import log as well. **PR-14 hand-off:**
    `test_orbits.py::test_parse_cassini_orbit_rejects_integer` pins that `int` behavior,
    so when PR-14 annotates the parameter as `orbit: str` that test needs a narrow
    `# type: ignore[arg-type]` (keep it — it is the regression test proving the raise is
    reachable) rather than deletion.
  - **STILL OPEN, deliberately out of PR-03a's scope — the same escaping-`OverflowError`
    class survives one function away.** `units.py:637-639` does `ret = parse_func(s)` then
    `math.isfinite(ret)`; with `parse_func = int` (any `%d` numerical format) a long digit
    string becomes a Python bigint and `math.isfinite` raises
    `OverflowError: int too large to convert to float`. Reproduce with
    `parse_unit_value('1'*400, 'd', None, None)`. It is web-reachable from every `RANGE%d`
    slug and escapes `views.py:799`'s `except ValueError` as a 500, exactly like the angles
    case fixed here. PR-03a fixed only the paths inside `_parse_dms_hms`, so **do not read
    the bullet above as "this class is closed"** — **owner: PR-13** (API error handling).
  - **Deviation from `python.mdc` §1 ("prefer explicit membership checks over catching
    exceptions for control flow"), recorded for PR-14.** `orbits.py`'s letter lookup is
    `try: CASSINI_ORBIT_NUMBER[name] / except KeyError`, which is the rule's literal
    counter-example; `format_cassini_orbit` right below it has the same shape. PR-03a
    briefly converted the first to an `in` test and reverted it, because converting one and
    not the other made the module internally inconsistent and converting both is outside
    the four assigned defects. **PR-14 should convert both sites together** — it is the PR
    that reopens `opus_support` (PR-17 is the Django/log_analyzer annotation PR and does
    not touch this tree).
  - **A second stale claim in the PR-03a plan text, for the record.** §PR-03a item 1 says
    the fused suffix "can never match". It could: pre-fix,
    `parse_unit_value('1 cm^-1perpixelcm**-1/p', '.10f', 'wavenumber_resolution',
    '1_cm_pixel')` returned `1.0`, because the fused string was a real entry that matched
    itself. The defect and the fix are exactly as the plan describes; only that clause is
    wrong.
  - **`_parse_multi_field_sclk` output is provably unchanged** by the no-op removal: a
    differential sweep of 4,826,796 inputs (every 1-to-5-field combination of 13
    representative field spellings × 4 partition prefixes × the Galileo/New Horizons/Cassini
    configurations) gave identical values *and* identical error messages before and after.
    Voyager has its own parser and never reaches this code.
  - **`ruff check --isolated --select ISC001,ISC002,ISC004 <paths>` is the detector for the
    missing-comma defect class** (implicit string concatenation, `ISC004` being the
    inside-a-collection case). Swept the whole tree: `src/` had exactly the two known sites
    and nothing else, and **`opus/` and `log_analyzer/` are clean — zero
    `ISC001`/`ISC002`/`ISC004` — so this defect class exists nowhere else in production
    code.** (Both trees do have 151 `ISC003` "explicitly concatenated string" hits, but that
    is a style rule about `'a' + 'b'`, not this bug. `tests/opus_support/test_sclk.py` has 52
    intentional `ISC004` hits: long expected-error-message literals split across lines inside
    `parametrize` tuples.) `ISC` is deliberately **not** added to the project rule set — that
    set is PR-01's decision and `ISC003`/the test hits would have to be triaged first.
  - **The `opus_support` 100% integration gate survived a behavior change.** Statement counts
    moved (`angles.py` 117→123, `sclk.py` 161→159) and every module is still at 100%
    statements and 100% branches. Note the trap: making the orbits raise reachable *removed*
    the only coverage of the letter-lookup failure path,
    which existing tests had been reaching only via the swallowed raise — a new
    unknown-orbit-name test had to be added or the gate would have failed. **Expect this
    whenever a fix makes an unreachable branch reachable: re-check what stopped being
    covered, not just what started.**
- **2026-08-18 (PR-04 executed):** the import pipeline is `src/opus_import`; facts later PRs
  rely on:
  - **Where the files the plan did not name individually landed.** `create_opus_models.sh`
    is a **sixth** shell script that lived in `opus/import/` (the plan lists five); it is
    really a Django-side generator — it runs `manage.py inspectdb` from `opus/application`
    and writes `apps/search/models.py` — but it is a shell script, so it lives under
    `scripts/`, with its **contents untouched**. It is **not** import tooling, so it does
    not belong in `scripts/import/`: it has its own directory,
    `scripts/models/create_opus_models.sh` (orchestrator's call, 2026-08-19).
    **PR-07 owns rewriting it.** The import
    pipeline's **five** Markdown files did **not** go to `docs/`: `README.md` (a
    scratchpad TODO list) is `src/opus_import/README.md`, the three `docs/*.md` are
    `src/opus_import/docs/`, and `table_schemas/README.md` stays with the schemas.
    Reason: `scripts/run-all-checks.sh` pymarkdown-scans `docs/` as soon as it exists, and
    those files have **68 violations** (MD025/MD024 heading structure, MD007, MD022,
    MD041) that only PR-21's port will fix. `NEW_INSTRUMENT_TEMPLATE.txt` **is** in
    `docs/` as the plan directs — it is not Markdown, so it does not trip that scan.
    **PR-21 must collect the ported sources from those three directories plus `docs/`,
    and note that its port list names only four of the five Markdown files:
    `src/opus_import/README.md` has no plan-assigned destination, so PR-21 must decide to
    port or delete it rather than leave it orphaned.**
  - **`cli.py`'s shape and its two intended CLI differences.** The old script body is now
    `_create_argument_parser()` (the argparse block verbatim) plus `main()` (everything
    else, same statements in the same order), so importing the module no longer runs an
    import; `__main__.py` calls `main()`, and **PR-22's `opus_import = opus_import.cli:main`
    console script already resolves**. (1) `prog='opus_import'` is set explicitly —
    otherwise argparse reports `__main__.py`. (2) **`--help` no longer requires an
    `opus_secrets.py`**: `load_secrets()` is called inside `main()` after the arguments
    parse, where the old module-level `from opus_secrets import *` ran before argparse.
    Verified: `--help` output is otherwise byte-identical to the old script's modulo the
    program name (whitespace-collapsed comparison).
  - **Only two shim consumers are left on the import side**, not three: `cli.py` (twelve
    settings, read through `secrets = load_secrets()`) and `import_util.py`
    (`IMPORT_TABLE_TEMP_PREFIX`, read through `load_secrets()` at its use site).
    **`do_dictionary` needs no settings at all now** — its three `DICTIONARY_*` paths
    became package data — so **PR-08's "rewrite consumption in `do_dictionary`" is empty
    work** unless §3's `[dictionary]` TOML section is meant to keep an override, which
    nothing currently needs. The three settings were deleted from
    `opus_secrets_template.py` and from both `*_setup_environment.sh` generators.
  - **Package data is reached through `import_util`:** `TABLE_SCHEMA_DIR`,
    `DICTIONARY_DATA_DIR` (both `importlib.resources` traversables) and
    `table_schema_files(pattern)`, which returns the matching schema files **sorted by
    name** (`glob.glob` returned file-system order). Use these rather than `__file__`
    arithmetic. `read_schema_for_table` reads UTF-8 explicitly; every packaged file is
    ASCII today.
  - **`namespaces = false` is now set in `[tool.setuptools.packages.find]`, and it
    matters for PR-05/PR-06.** Without it, setuptools treats every data directory inside a
    package (`table_schemas`, `dictionary_data`, `docs`) as a **PEP 420 namespace
    package**: they become importable, and — the reason it was found — their contents are
    attributed to *that* package, so `[tool.setuptools.exclude-package-data]` entries
    written against `opus_import` silently do not apply. PR-05's `templates/`, `static/`
    and PR-06's Jinja `templates/` are the same shape; keep the setting.
    `exclude-package-data` keeps `src/opus_import/{README.md,docs/*.md}` out of the wheel.
  - **Tool scope paths after this PR** (the same three files each remaining move PR must
    update): ruff `src opus/application/apps log_analyzer tests` (`opus/import` dropped);
    bandit `src opus log_analyzer` and vulture `src opus log_analyzer tests
    vulture_whitelist.py` are **unchanged** — both already covered the tree under both
    names. `[tool.ruff.lint.per-file-ignores]`'s `opus/**/*.py` row now covers **only the
    Django app**; no `src/**` row was added. Bringing the tree up to the full rule set
    cost 27 `E501` wraps (Cassini phase table, two MySQL SQL strings, a `do_import`
    comment, a regex, and the uranus_occs docstring's shell commands) and nothing else:
    `E722`/`N801`/`N802` never fired here, and the only `F403`/`F405` came from the
    `opus_secrets` wildcard this PR deletes.
  - **`src/opus_import/config_bundle_info.py` carries a file-level `# flake8: noqa`**,
    which ruff honors, so that one file is entirely unlinted (this predates the move).
    **PR-17 should remove it** as part of emptying the ignore table; its long
    `obs_bundle_*` import lines are what it hides.
  - **Vulture unmasked one name when `import_util`'s local `schema_filename` disappeared**
    (the PR-03 lesson repeating): `ImportDBSuper.create_table`'s third parameter was still
    called `schema_filename` although every caller and `ImportDBMySQL.create_table` pass a
    parsed schema. Renamed to `schema`; abstract method, no behavior. **Expect another
    round of unmaskings in PR-05/PR-06.**
  - **`OPUS_SECRETS` is now exported by** `scripts/automated_tests/opus_import_test_database.sh`
    (which no longer `cd`s into `opus/import`), `scripts/server/import_and_deploy/
    _opus_setup_environment.sh` (where the file is written; it is sourced, so the export
    reaches the import step) and `deploy_new_code_only.sh` (which reuses an existing
    checkout). The Django side still finds `opus_secrets.py` through `settings.py`'s
    `sys.path` inserts — **PR-05 owns switching it to the shim**, and
    `opus_run_unittests_coverage.sh` will need the same export then.
  - **The `scripts/import/*` wrappers now run from the repository root**, not from their
    own directory (`import_all.sh` calls `./scripts/import/_import_all_internal.sh`;
    `import_for_tests.sh` greps `"${OPUS_SECRETS:-opus_secrets.py}"` and migrates via
    `opus/application`). PR-19 still reads `import_for_tests.sh` for its bundle list.
  - **`cli.py`'s one import-time side effect is dead code.**
    `pdslogger.TIME_FMT = '%Y-%m-%d %H:%M:%S'` (moved verbatim, and now after
    the step imports rather than before them, which the isort re-sort could only have
    mattered for) assigns an attribute **rms-pdslogger 3.2.1 does not have** — its
    timestamp format is the private `_TIME_FMT` (`'%Y-%m-%d %H:%M:%S.%f'`), which is why
    the import logs still print microseconds. So the statement has been a no-op for some
    time; it was kept because a move PR must not change behavior, and vulture cannot see
    a cross-module attribute assignment. **Owner: the logging PR (PR-13, #512)** — delete
    it or set the format through a supported API. It is the only import-time statement in
    the package that mutates anything *outside* itself, but **the package as a whole is not
    import-safe, and that list is not worth enumerating**: `importdb/mysql.py` runs a
    guarded `import MySQLdb`, `import_util.py` resolves two `importlib.resources`
    traversables, `obs/obs_volume_vg28xx.py` and `obs/obs_cassini_common.py` build
    `julian`-based time tables at module (and, for Cassini, class-body) level, and the two
    `util/` scripts in the next bullet do their entire job at import. **Assume any
    `opus_import` module does work when it is imported** — three review passes each found
    another instance of a closed list being short.
  - **Two latent defects found in the moved code and deliberately NOT fixed** (a pure move
    must not change behavior; the PR-03 precedent applies — the orchestrator should assign
    them, and PR-10, which reopens these files, is the natural home):
    1. `steps/do_dictionary.py:130` — `logger.log('error', 'Bad row in "{ctxfile}": {row}')`
       is missing its `f` prefix, so a malformed `contexts.csv` row is reported with the
       braces literal and names neither the file nor the row. The name it would
       interpolate does not exist either (the variable is `ctx_file`), so adding the
       prefix alone would raise `NameError` — both have to be fixed together. It is the
       **only** un-prefixed format string in `src/`, `opus/` and `log_analyzer/` (found by
       an AST sweep excluding docstrings, `.format()` receivers and f-string parts).
       **`RUF027` does not find it and cannot**: that rule only fires when the placeholder
       name is bound in scope, and `ctxfile` is precisely what is not — so do not read a
       clean `ruff --preview --select RUF027` run as this class being closed.
    2. `util/retrieve_ra_dec.py` does its work at **module level** (a `for` loop issuing
       SIMBAD HTTP requests), and `util/dump_pds_definitions.py` reads `sys.argv[1]` the
       same way. Nothing imports either — they are hand-run authoring tools — but they are
       inside a package now, so `import opus_import.util.retrieve_ra_dec` would hit the
       network. **PR-21 must keep `opus_import.util` out of Sphinx autodoc**, and PR-15
       should give both a `main()` when it annotates them.
  - **Verification evidence.** The full local chain
    (`scripts/automated_tests/opus_main_test.sh`: import of the 30-bundle test set into a
    fresh MySQL schema, then the Django unit tests with the 100% coverage gate) passed,
    which is the only end-to-end oracle the import half has. A built wheel installed into
    a clean venv runs `python -m opus_import --help` from outside the repository and reads
    `table_schemas`/`dictionary_data` out of `site-packages`.
- **2026-08-19 (PR-05 executed):** the Django app is `src/opus_app`, its live-DB suites are
  `integration_tests/`, and both are driven from the repository root. Facts later PRs rely on:
  - **Where everything landed.** `src/opus_app/{__init__,settings,urls,clear_django_cache}.py`,
    `src/opus_app/apps/<app>/`, `src/opus_app/templates/`, `src/opus_app/static/` (from
    `static_media/`), plus a **new** `src/opus_app/wsgi.py`. `manage.py` and
    `run_coverage.sh` are at the **repository root**; `.coveragerc` is
    `integration_tests/.coveragerc`. The live-DB suites are `integration_tests/test_api/`,
    `integration_tests/test_db_data/`, `integration_tests/test_perf/` and
    `integration_tests/apps_db_tests/` — the last is the flattened `apps/*/test_*.py` set,
    whose module basenames were already
    unique; the dictionary app's contentless `tests.py` became
    `apps_db_tests/test_dictionary.py` so the flattened directory keeps naming its origin.
    `integration_tests/`, `integration_tests/test_api/`, `integration_tests/test_db_data/` and
    `integration_tests/apps_db_tests/` all have `__init__.py` (the middle two carried theirs
    through the move, and `manage.py`'s api-* labels depend on `test_api` being a
    package); **`integration_tests/test_perf/` deliberately does not** — it had none
    before, so unittest discovery skipped it, and `test_perf_target.py` does its whole job
    (HTTP requests to a
    live server) in its module body. Adding one would make `manage.py test` run it.
  - **The per-file-ignores glob followed the code, and that contradicts an earlier note.**
    The PR-03 note says "no `src/**` row was added and none should be — code is brought up
    to the full rule set as it moves". That held for `opus_support` (clean) and
    `opus_import` (27 `E501` wraps). For the Django app it does not: with the table emptied,
    ruff reports **1111 `E501` + 180 `N802` + 7 `N801`** across `src/opus_app` and
    `integration_tests` — precisely the legacy-refactor codes PR-01 assigns to **PR-17** ("removed
    as the underlying code is cleaned up through PR-17"; the PR-01 note pins `N801`/`N802` to
    PR-17 by name). Burning them down here would have pre-empted PR-17 and buried the move in
    reformatting. **Resolution (stop-and-report recorded in the PR; the plan body was
    followed over the earlier note):** the `opus/**/*.py` row became `src/opus_app/**/*.py`
    and `integration_tests/**/*.py`, **trimmed to `["E501", "N801", "N802"]`** — `E722` never fired
    in this tree and the `opus_secrets` wildcard that produced its only `F403`/`F405` is gone
    — still retired by PR-17, whose empty-table exit criterion is unchanged. Everything
    outside the legacy set **was** fixed here (see below).
  - **`[tool.ruff] exclude` gained `src/opus_app/static`.** That tree is served assets; its
    one Python file is Django's own vendored `admin/js/compress.py` (already
    `linguist-vendored` in `.gitattributes`). This is a permanent exclusion like
    `perf_test`, not a burn-down entry, and does not affect PR-17's table.
  - **Newly linted files, fixed rather than grandfathered.** `settings.py`, `urls.py`,
    `manage.py`, `clear_django_cache.py`, `test_api/`, `test_db_data/` and `test_perf/` were
    never ruff-scoped under flake8 and entered scope with this move. 55 non-legacy findings
    were fixed: import sorting throughout, `B006` (`ignore=[]` → `None` sentinel in
    `api_test_helper._run_json_equal`), `B011`/`PT015` (`assert False` →
    `raise AssertionError` in `test_result_counts.py`), `UP015`, `F401`, three vestigial
    `F841` `expected = ...` assignments with no reader, `C403`/`C414`/`C416` in
    `test_local_db_integrity.py` (`sorted([n for n in X.__dict__])` → `sorted(X.__dict__)`;
    `mappingproxy` has a real `__iter__`, audited under the §4a duck-typing lens),
    `A001`/`F841` in `test_perf_target.py`, and two `F601` duplicate `reqno` dict keys in
    `test_search_api.py` whose shadowed halves were already dead at runtime. Four `# noqa`
    directives, of three kinds, were added with written justifications (PR-17 revisits them
    with the rest of the suppression sets; all four are individually justified and
    structurally irreducible):
    `# noqa: E402` on `clear_django_cache.py`'s cache import, which has to follow
    `settings.configure()`; `# noqa: SIM115` on the two `tarfile.open` calls
    in `api_test_helper._run_archive_file_equal` (opened in one of four branches, closed once
    where they rejoin) and `# noqa: SIM102` on a nested `if` in `test_search_api.py` (the
    inner test carries its own `# pragma: no cover`; collapsing would put the outer test,
    which the suite does exercise, behind that pragma too). A file's self-naming banner
    comment was repointed wherever it would otherwise have become wrong — that is, wherever
    the file's path relative to its package root changed: the relocated suites
    (`# integration_tests/test_api/test_cart_api.py`) and the project package
    (`# opus_app/urls.py`). The per-app modules keep app-relative banners (`# cart/urls.py`
    in `opus_app/apps/cart/urls.py`), which stay accurate relative to `apps/`; that is the
    convention, not an oversight. `zip()` gained an explicit
    `strict=False` rather than `strict=True`, to keep the suite asserting exactly what it
    asserted before.
  - **`LOGGING`'s logger keys had to be renamed and this is a silent failure mode.** Every
    app module does `logging.getLogger(__name__)`, so the names went from `cart.views` to
    `opus_app.apps.cart.views`; the config's `'cart'`, `'search'`, … keys no longer prefixed
    anything and would have stopped those records reaching the log file with no error
    anywhere. They are now `'opus_app.apps.<app>'` (and `'opus_app.apps.search.forms'`).
    Log lines now carry the longer `%(name)s`; no golden fixture contains a logger name.
  - **`settings.py` consumes the shim explicitly (PR-08 hand-off).** The wildcard is gone;
    the names read from `opus_secrets.py` are exactly `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`,
    `STATIC_ROOT`, `DB_{HOST_NAME,SCHEMA_NAME,USER,PASSWORD}`, `PDS3_DATA_DIR`,
    `PDS4_DATA_DIR`, `RMS_OPUS_PATH`, `OPUS_STATIC_ROOT`, `CACHE_SERVER_PREFIX`,
    `PUBLIC_OPUS_URL`, `PRODUCT_HTTP_PATH`, `VIEWMASTER_ROOT_PATH`, `TAR_FILE_PATH`,
    `MANIFEST_FILE_PATH`, `TAR_FILE_URL_PATH`, `OPUS_LAST_BLOG_UPDATE_FILE`,
    `OPUS_NOTIFICATION_FILE`, `OPUS_LOG_FILE`, `OPUS_LOG_{FILE,CONSOLE,DJANGO}_LEVEL`,
    `OPUS_LOG_API_CALLS` and the three `OPUS_FAKE_*` knobs — 29 names; the TOML schema must
    cover all of them. **`STATIC_ROOT` is read with a `getattr(..., None)` fallback**
    because `scripts/automated_tests/opus_setup_environment.sh` has never written it (only
    the server generator does) and the wildcard silently left it at Django's own default.
    `DB_BRAND`, `DB_DATABASE_NAME`, `OPUS_LOGFILE_DIR`, the `IMPORT_*` settings and
    `DICTIONARY_TERM_URL` are no longer surfaced to Django at all — nothing read them
    through `settings.`. (`OPUS_LOGFILE_DIR` is only a helper the secrets file uses to
    build `OPUS_LOG_FILE`.)
  - **`BASE_DIR` exists now** (`Path(__file__).resolve().parent`) and carries
    `STATICFILES_DIRS` and the template `DIRS`. Two stale entries went with the move: the
    `apps/quide/templates/` directory (gone for years, per the plan) and a bare relative
    `'static_media/'` in `STATICFILES_DIRS`, which only ever resolved because the CWD was
    `opus/application` and would now raise `staticfiles.W004`. `STATIC_URL` stays
    `/static_media/`; `manage.py check` reports the same single pre-existing `urls.W005` as
    before, and no `staticfiles` warning.
  - **The fixture paths in the integration suite are CWD-relative and the CWD is the
    repository root.** `api_test_helper._RESPONSES_FILE_ROOT` is
    `'integration_tests/test_api/responses/'` and `test_ui.py`/`test_result_counts.py` name
    `'integration_tests/test_api/data/...'`. Anything that runs this suite from elsewhere breaks
    silently (the golden comparison would fail to open its files). PR-20, which makes the
    suite pytest-driven, should consider anchoring these on `__file__`.
  - **`COVERAGE_RCFILE=integration_tests/.coveragerc` must be exported by anything that runs
    coverage from the root**, because with no `.coveragerc` in the CWD coverage falls back to
    `pyproject.toml` and would silently pick up the *unit* config (`source` of the four
    non-Django packages, `fail_under = 90`), corrupting the 100% gate. It is exported in
    `run_coverage.sh` (covering its `run`/`xml`/`html`/`report` calls) and in
    `scripts/automated_tests/opus_run_unittests_coverage.sh` (covering its `coverage report
    -m`), rather than only in the workflow, so local runs behave identically.
  - **`manage.py test` from the root needs an explicit label.** Bare `manage.py test` would
    discover the whole repository, so `run_coverage.sh` runs
    `coverage run -a manage.py test -b "${@:-integration_tests}"`. Its optional arguments changed
    meaning from a single `manage.py` verb *prefix* (`manage.py $1 test`, which could never
    have worked — argparse would have read the verb as the subcommand) to **test labels**,
    all of which are forwarded, so the multi-verb form the suite's README documents
    (`./run_coverage.sh api-livetest-dev api-all`) works and resolves through `manage.py`'s
    own verb mapping. The api-* verbs map to `integration_tests.test_api*`.
  - **`opus.wsgi_template` is gone**, replaced by the committed `src/opus_app/wsgi.py`
    (`DJANGO_SETTINGS_MODULE=opus_app.settings`), and `deploy_new_code_and_database.sh` no
    longer seds a generated `opus.wsgi`. **The Apache vhost's `WSGIScriptAlias` still points
    at the old generated path and must be repointed — owner: PR-22**, which rewrites the
    deploy chain around `pip install rms-opus` anyway.
  - **`clear_django_cache.py` is now `python -m opus_app.clear_django_cache`** (both deploy
    scripts updated). It calls `settings.configure()` in its module body, so like
    `opus_import.util`, **PR-21 must keep it out of Sphinx autodoc** — importing it
    configures Django settings as a side effect.
  - **`test_results_api.py` was importing `tools.app_utils` twice**, once as
    `opus.application.apps.tools.app_utils` (resolvable only because `settings.py` inserted
    the repo root on `sys.path` and `opus/` was a namespace package) and once as
    `tools.app_utils`, loading it as two distinct module objects. Both collapse to
    `opus_app.apps.tools.app_utils`; the two statements are merged.
  - **Tool scope paths after this PR** (the same three files each remaining move PR must
    update): ruff `src integration_tests log_analyzer tests manage.py`; bandit
    `src integration_tests log_analyzer manage.py`; vulture `src integration_tests
    log_analyzer tests manage.py vulture_whitelist.py`. `opus/` is gone from all of them,
    and `manage.py` had to be named explicitly since it is a bare file at the root. PR-06
    drops `log_analyzer` from all three (it moves under `src/`).
  - **The wheel already ships the Django app's templates and static files** — no
    `package-data` entry was needed, because `include-package-data` plus setuptools-scm's
    file finder picks up every git-tracked file inside a package directory, and
    `namespaces = false` (PR-04) keeps `templates/`/`static/` as data directories rather than
    namespace packages. `apps/help/{api_guide.md,faq.yaml}` ship, which they must — the help
    views read them via `__file__`. **Not done, left for PR-21/PR-22:** the Django app's
    per-app `README.md` files also ship, where PR-04 excluded `opus_import`'s equivalents via
    `exclude-package-data`; and so do the four `linguist-vendored` asset trees
    (`static/{admin,coreui,cdn_fallback,perfect-scrollbar}`, several MB of third-party
    JS/CSS). Shipping them is what serving the site from an installed distribution requires,
    but PR-22 should decide deliberately rather than by default.
  - **Verification evidence.** Test-by-test discovery equivalence was proved before running
    anything: `DiscoverRunner.build_suite` on the pre-move tree and on `integration_tests` both
    yield **1522** ids, identical after normalizing the module prefix (the one difference is
    a `_FailedTest` for `test_results`, which needs a live DB at import time and fails
    identically on both sides). The full local chain (`opus_main_test.sh`: 30-bundle import
    into a fresh MySQL schema, then the Django suite under the 100% gate) then ran
    end-to-end with exit code 0 and **zero golden-fixture diffs** (`git status
    integration_tests/test_api/responses` empty afterwards). The pre-move baseline on the same
    machine was `Ran 1576 tests` / `OK` / `TOTAL 25645 stmts, 1876 branches, 100%`; the
    post-move run is `Ran 1576 tests` / `OK` / `TOTAL 22228 stmts, 1872 branches, 100%`.
    The whole 3,417-statement/4-branch delta is accounted for file by file: 3,411 statements
    and 4 branches are the eight per-app test modules leaving the coverage `include` scope
    when they moved to `integration_tests/apps_db_tests/` (they were 100%-covered, so the gate is
    unaffected), and the remaining 6 are the dead statements the lint fixes deleted
    (`test_help_api.py` -1, `test_metadata_api.py` -2, `test_results_api.py` -2 — one
    `expected` assignment plus the merged duplicate import — `test_results_contents.py` -1).
    `scripts/run-all-checks.sh` is clean (ruff, pytest 847 passed, pyroma 10/10, bandit,
    vulture, pymarkdown). A built wheel installed into a clean venv (with `django<5` and
    `djangorestframework` added by hand — see the next bullet) loads
    `opus_app.wsgi:application` from `site-packages`, resolves `ui/base.html` to
    `site-packages/opus_app/apps/ui/templates/` and `js/opus.js` to
    `site-packages/opus_app/static/`, and builds the same four root URL patterns.
  - **The wheel's runtime dependencies alone still cannot start the app**, and that is the
    plan's documented standing assumption, not a regression: `rest_framework` sits in
    `INSTALLED_APPS` until PR-09 removes it while `djangorestframework` lives in the dev
    extras. A clean-venv wheel install therefore fails with
    `ModuleNotFoundError: No module named 'rest_framework'` at `django.setup()`. Do not
    "fix" this by re-adding DRF to the runtime dependencies (§1 standing assumptions).
  - **The directory is `integration_tests/`, not `integration/`** (orchestrator's call,
    2026-08-19, taken inside PR-05 while the tree was still unmerged). `integration/` reads
    as third-party service connectors at a repository root, whereas `tests/` and
    `integration_tests/` are visibly a pair; it is also a top-level importable package,
    since `manage.py`'s api-* verbs map to dotted labels, so the generic name squatted an
    import name for nothing. **It stays a sibling of `tests/`** — PR-18's selection model is
    `testpaths = ["tests"]` exactly so a bare `pytest` never collects the holdings- and
    DB-dependent suite, and moving it under `tests/` would break that. Everything the
    earlier bullets say about `integration/` — the `__init__.py` layout, the CWD-relative
    fixture paths, `COVERAGE_RCFILE`, the explicit `manage.py` label, the tool scope
    lists — holds unchanged under the new name. The rename was done as a second pure
    `git mv` commit (445 files, all `R100`) plus a string-update commit, so the original
    703-file move commit was left untouched.

# Critique: Fresh-Eyes Executability Critique (second pass)

- **Reviewer:** Fable-class agent, no prior context; lens = "will an opus-class executor succeed?"
- **Date:** 2026-07-18
- **Reviewed:** modernization plan rev 3
- **Outcome:** produced rev 4 (2 blockers + majors fixed; decision tables added; the only fable-leaning task de-escalated)

---

# Fresh-Eyes Critique: rms-opus Modernization Plan (rev 3)

Verification basis: full read of the plan; ~60 targeted reads/greps against the repo, the template, rms-pdsfile, and GitHub issues. The plan's file:line hygiene is generally excellent — of ~35 specific claims sampled, nearly all check out exactly. The defects below are what remains.

## Category 1 — Ambiguities an opus-class executor would resolve wrongly or stall on

**1.1 (Major) PR-16's alias scheme does not cover what field functions actually return.** There are 1,204 `field_obs_*` methods; `do_import.py:1236-1253` permits mult-column functions to return a bare value, a single dict, or a list of dicts; schemas also contain `mult_idx`, `mult_list`, `flag_*`. Fix: add a decision table mapping field_type → alias, give `MultField` TypedDict value types, and state whether bare-value returns are normalized to `_create_mult` first.

**1.2 (Major) PR-12's acceptance criterion cannot be mechanically checked as worded.** "grep for cursor.execute shows raw SQL nowhere" — whether a site is "raw SQL assembly" is a judgment call; constant `%s` statements assemble nothing. Fix: exempt constant literal statements; make the criterion "no string concatenation or f-string interpolation builds SQL outside sql_builder.py" with a concrete grep.

**1.3 (Major) PR-13's 400-vs-404 boundary is a one-line rule governing ~103 individual decisions.** Unresolved: bad opus_id as a query parameter vs URL path; unknown slug in `?cols=`; ringobsid conversion failure; non-numeric limit/startobs. Fix: add a decision table and require a per-endpoint fixture-diff report annotated against it.

**1.4 (Minor) PR-01 "ruff-clean" vs seeding ignores** — gaming incentive with no bound; the burn-down list's location/format are unspecified. Fix: the per-file-ignores table IS the burn-down list; seed only named codes; Phase D exit = empty table.

**1.5 (Minor) PR-04 does not say where the shell wrappers land** (`import_for_tests.sh` etc.). Fix: move them to `scripts/import/`.

**1.6 (Minor) PR-21 "port" of docs — move or copy?** Fix: ported files are deleted at their old locations.

**1.7 (Minor) PR-07's `_meta` diff cannot run in one process** (Django registry loads once). Fix: dump `_meta` to JSON pre- and post-, diff the files.

## Category 2 — Flow problems (PR-01 → PR-23 simulation)

**2.1 (Blocker) PR-19 adds a Sphinx docs-build CI step two PRs before docs exist** (docs/ is created in PR-21). Fix: move the docs-build step (and pymarkdown's docs/ arg) to PR-21.

**2.2 (Major) The single `[tool.coverage]` cannot serve both coverage regimes; the plan never reconciles them.** coverage.py ignores `include` when `--cov` is set. Fix: two configs — pyproject for the unit run, `integration/.coveragerc` for the 100% gate.

**2.3 (Major) The secrets-shim consumer list omits two direct `import opus_secrets` consumers** (`import_util.py:21`, `do_dictionary.py:15`), so PR-04 breaks the pipeline. Fix: rewrite all four consumers; done-check `grep -rn "import opus_secrets" src/` empty.

**2.4 (Major) `manage.py migrate` on a pip-only deployment is self-contradictory** (`manage.py` isn't in the wheel; §6 says no repo checkout). Fix: `django-admin migrate` with settings module + OPUS_CONFIG, or an `opus-manage` console script.

**2.5 (Major) Nothing in CI can run mypy(django-stubs), Sphinx autodoc, or `tests/opus` without an `OPUS_CONFIG` — and no PR provides one.** Fix: PR-08 checks in `tests/fixtures/opus_ci.toml`; lint/test/docs jobs export it.

**2.6 (Major) PR-18's pytest port can destroy the live imported DB.** `@pytest.mark.django_db(transaction=True)` flushes tables. Fix: integration tests stay `unittest.TestCase`; `django_db_blocker.unblock()`; `django_db` marker forbidden in integration/ (asserted).

**2.7 (Major) After PR-18 the integration 100% gate silently loses its opus_support contribution** unless the workflow still runs those tests. Fix: integration coverage runs `pytest tests/opus_support integration` combined.

**2.8 (Minor) PR-08's "removes the last sys.path manipulation" is false by then** (already removed in PR-04/05). Fix: restate as a standing invariant.

**2.9 (Minor) `test_all_venv.sh`/`create_all_venv.sh`/`scripts/releases/` have no disposition.** Fix: delete the obsolete venv scripts in PR-01; keep releases.

**2.10 (Minor) `test_db_data/` and `test_perf/` moves are in the layout but assigned to no PR.** Fix: add to PR-05's move list.

## Category 3 — Internal inconsistencies & cross-reference errors

**3.1 (Major) PR-22's `opus-log-analyzer = opus_log_analyzer.cli:main` points at a module no PR creates.** Fix: PR-06 renames `log_analyzer.py` → `cli.py`.

**3.2 (Minor) PR-12's ranges overlap themselves and undercount cart** (~13 more sites at `cart/views.py:1149-1512`; `file_utils.py` at 62 and 124). Fix: regenerate from grep or drop the enumeration.

**3.3 (Minor) §7 says log_analyzer ~1,900 lines; it is 2,955.** §1 says import is 72 files; it is 79. Fix: correct.

**3.4 (Nit) `LICENSE.md` → `LICENSE` rename assigned to no PR.** Add to PR-01.

**3.5 (Nit) §3's `[dictionary]` omits `DICTIONARY_JSON_SCHEMA_PATH`** (replaced by importlib.resources — say so).

## Category 4 — Disagreements with the codebase

**4.1 (Blocker, feeds PR-19) `Pds3File.require_shelves(True)` is unconditional — the spike's premise is wrong.** Only `use_shelves_only()` is inside the `dont_use_shelves_only` guard; `require_shelves(True)` runs unconditionally (`main_opus_import.py:419-423`), and the import hits missing-shelf exceptions via `file.size_bytes` (`do_import.py:1591`). A shelf-less fixture fails regardless of the flag. Fix: move `require_shelves(True)` inside the guard (PR-02 one-liner).

**4.2 (Major) `python -m opus_log_analyzer` will import the Django `opus` package** (default `--configuration 'opus.configuration'` via `importlib.import_module`, `log_analyzer.py:80,109`). Fix: default becomes `opus_log_analyzer.opus.configuration`; cron templates rewritten; import test.

**4.3 (Major) `RMS_OPUS_PATH` has a runtime consumer the plan never reassigns: `get_git_version`** (`app_utils.py:178-212` chdir + git). Fix: PR-08 replaces internals with `importlib.metadata.version('rms-opus')`.

**4.4 (Minor) "DRF only test_api" is incomplete** — it's in INSTALLED_APPS + REST_FRAMEWORK block until PR-09. Note it.

**4.5 (Minor) `obs/typing.py` shadows a stdlib module (ruff A005).** Name it `obs/field_types.py`.

**4.6 (Nit) PR-03's `.coveragerc` glob `*/opus_support/*` also matches `tests/opus_support/*`.** Use `*/src/opus_support/*`.

## Category 5 — Bad smells

**5.1 (Major) PR-05's per-app-split fallback contradicts its own "pure move" doctrine** (needs both import roots resolvable, which the plan bans). Fix: drop the fallback (accept the mega-PR) or specify a bridging alias package.

**5.2 (Major) Phase D annotates 1,204 obs methods before the import pipeline has unit tests.** Schema-validation ≠ behavior. Fix: PR-16's test also calls sample field functions against fixtures (per mission).

**5.3 (Minor) The `ruff format` exemption isn't pinned** — the copied template workflow has a `ruff format --check` step to delete. Say so.

**5.4 (Minor) `perf_test/` is "outside the gates" but nothing excludes it.** Add to ruff/mypy/pytest excludes in PR-01.

**5.5 (Minor) `tests/opus/` and `tests/opus_config/` are in the layout but no PR writes them.** Assign opus_config loader tests to PR-08 and `tests/opus` to PR-18.

## Category 6 — Fable-required sections, and the specs that de-escalate them

**6.1 PR-19 mini-holdings fixture spike — the only genuinely fable-leaning task; de-escalatable.** Respecification: subset real bundles (COISS_2002 + a PDS4 bundle), edit only ROWS/FILE_RECORDS in the labels; ship referenced data files as 1-byte stand-ins (never 0 bytes — `do_import.py:1624-1626`); move `require_shelves(True)` under the guard in PR-02; mechanical success criterion (exit 0, empty ERRORS.log, obs_general count == N); time-boxed fallback to `FakePds3File` with method list incl. `size_bytes`/`is_local`. With this spec: opus-class. Without it: fable-required.

**6.2 PR-16 schema-validation test — opus-class with the 1.1 decision table.** The resolver logic is mechanical once field_type→alias and the mult-return normalization are written down.

**6.3 PR-11 ImportContext — opus-class with one worked example added** (route obs `_log_*` through `self._ctx`; free functions take `ctx`; three module caches become context fields).

**6.4 PR-12 SQL builder — opus-class.** Bounded design space, golden suite as oracle, byte-identical criterion. Needs only 1.2's acceptance rewrite.

**6.5 PR-09 Django 5.2 — opus-class.** Every deprecation item verified against the code; `_meta` re-diff and integration suite gate it.

**6.6 PR-07 models generator — opus-class** given 1.7's two-process note.

**6.7 PR-13 @api_view — opus-class with 1.3's decision table**, plus a note that injection now fires pre-handler.

## Verdict

**Conditionally executable — not as-is.** Four defects will stop or misdirect an opus executor mid-sequence: docs-build-before-docs (2.1), the unconditional `require_shelves` contradiction (4.1), missing-`OPUS_CONFIG`-in-CI (2.5), and the pytest-django DB-wipe trap (2.6); plus the secrets-shim gap (2.3), the migrate contradiction (2.4), and the coverage-config collision (2.2) — seven items for a rev 4. With those fixes plus the three decision tables (mult typing, 400/404, SQL-builder acceptance), every PR is within opus-class reach.

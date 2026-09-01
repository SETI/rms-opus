# Critique: Adversarial Review (first pass)

- **Reviewer:** Fable-class agent, adversarial ("try hard to break the plan")
- **Date:** 2026-07-18
- **Reviewed:** modernization plan rev 2
- **Outcome:** produced rev 3 (fixed 3 blockers + 11 majors)

---

# Defect Report: rms-opus Modernization Plan

## BLOCKERS

**1. The plan's core safety net never fires: both CI workflows only trigger on PRs to `main`, but every PR targets `rewrite`.**
(a) Plan §4/§5/§7: "Every PR: targets `rewrite`; keeps **both** CI workflows green"; "The self-hosted workflow must stay green on **every** rewrite PR — it is the safety net."
(b) Reality: `.github/workflows/run-app-tests.yml` and `run-lint.yml` both have `pull_request: branches: [ main ]` (and push to main only). The template `run-tests.yml` the plan copies in PR-01 also has `branches: [ main ]`.
(c) No PR against `rewrite` will run either workflow. The entire "golden-response suite runs on every PR" invariant, the strongest behavior-preservation guarantee in the plan, is silently void for all 22 PRs.
(d) Fix: PR-01 (or a PR-00) must add `rewrite` to the `pull_request`/`push` branch filters of *both* workflows (and keep them in the new `run-tests.yml`/`run-integration.yml` until PR-23 removes them).

**2. The ≥90% unit-coverage gate over `src/` is arithmetically unachievable as specified.**
(a) Plan PR-19: "≥90% coverage gate"; §7: "the 90% gate applies to `src/` only".
(b) Reality: the Django app is ~26,360 lines, vs ~16,700 for import, 2,305 for opus_support, ~1,900 for log_analyzer. The Django app is >50% of future `src/`, and its only real test coverage (the 8 per-app DB suites + test_api, all requiring the populated real-holdings DB) is explicitly moved to `integration/` and excluded from the GitHub-hosted run. Even 100% coverage of everything else plus ~10% of `src/opus` yields a total near 50–55%.
(c) PR-19's gate fails permanently; an executor either cheats (mass `# pragma: no cover`) or stalls.
(d) Fix: scope the unit gate explicitly, e.g. `--cov=opus_support --cov=opus_config --cov=opus_import --cov=opus_log_analyzer` (excluding `src/opus`), or set separate per-package `fail_under`s, and state that `src/opus` coverage is owned by the integration 100% gate.

**3. PR-03 breaks the self-hosted workflow: `run_coverage.sh`, `.coveragerc`, and the workflow's install step are not covered by the plan's "move PRs update `scripts/automated_tests/*`" clause.**
(a) Plan PR-03: move `lib/opus_support.py` → `src/opus_support/`, extract inline unittests, "delete `RMS_OPUS_LIB_PATH` sys.path inserts on both sides." The blanket clause only promises updates to `scripts/automated_tests/*`.
(b) Reality:
- `opus/application/run_coverage.sh` line 1: `coverage run ../../lib/opus_support.py` — hard failure once the file is gone. This script lives in `opus/application/`, not `scripts/automated_tests/`.
- `opus/application/.coveragerc` includes `*/opus_support.py` — matches nothing after the split into `sclk.py`/`orbits.py`/etc.
- `run-app-tests.yml` installs only `python -m pip install -r requirements.txt` — after deleting the sys.path inserts, `opus_support` is importable only via `pip install -e .`, which no CI step performs.
(c) The very first move PR turns the integration workflow red three different ways.
(d) Fix: PR-03 must explicitly (i) add `pip install -e .` to `run-app-tests.yml`, (ii) rewrite `run_coverage.sh` to run the new pytest opus_support tests, and (iii) update `.coveragerc` include patterns. The same blind spot recurs in PR-05 — generalize the blanket clause to "all CI-reachable scripts and workflow files," enumerated per PR.

## MAJOR

**4. PR-12's "five hand-rolled sites" materially under-enumerates the raw SQL surface.** Hand-rolled SQL with `cursor.execute` exists outside every listed range (e.g. `search/views.py:288-365, 994-1043`, `results/views.py:1123-1143, 1199-1220, 1507-1509, 1623-1645`, `cart/views.py:515-516, 1088, 1134-1139`, and more). Fix: replace the five-site list with a grep-defined scope and cite the grep as the acceptance criterion.

**5. The `static_media` → `static` rename (PR-05) is unsafe as written and breaks golden fixtures before PR-13.** `STATIC_URL='/static_media/'`; `opus.js:1120` hardcodes `/static_media`; help pages embed it; golden fixtures embed it; Apache aliases it. Fix: rename the directory but keep `STATIC_URL='/static_media/'` permanently.

**6. Open decisions remain, violating the "no judgment calls" requirement.** PR-02 "(+ decide `dump_pds_definitions.py`)"; §3 "`term_url` dropped if unused"; PR-09 monkeypatch "keep or replace"; PR-11 "if needed split"; PR-05 "if too large split." Fix: decide each in the plan text.

**7. PR-16's `MultField` is factually wrong: mult field methods return a dict, not a tuple, and the cited lines are the wrong location.** `obs_base.py:349-367` `_create_mult()` returns a dict; `do_import.py:1244-1246` unpacks it. Fix: define `MultField` as a TypedDict citing `obs_base.py:349`.

**8. PR-05 leaves the integration invocation between the move and PR-18 unspecified.** The workflow chain `cd opus/application` → `run_coverage.sh` → `manage.py test`, `.coveragerc` includes, `opus_check_coverage.sh`, coverage.xml path — none in `scripts/automated_tests/`. Fix: PR-05 must enumerate all of these.

**9. pytest-django (or an equivalent bootstrap) is never mentioned.** None of the Django-dependent suites run under plain pytest without pytest-django. Fix: add pytest-django to dev extras and specify DB-lifecycle handling that preserves the imported live DB.

**10. The new deploy flow (PR-22) drops `manage.py migrate` with no replacement for Django's own tables.** `django_session`/auth/contenttypes/admin tables are created by `manage.py migrate` today; the import pipeline does not create them. Sessions are load-bearing (cart keyed by session_id). Fix: retain a migrate step.

**11. Stale/incorrect factual claims.** `obs_profile_pds4.py` missing-return bug no longer exists (file rewritten since #1434); dictionary secrets template has no `DB_BRAND`; memcache probe is already in `settings.py:4-21` not the wsgi template; `do_import.py` is 1,782 lines not 1778; opus_support has 22 importer files not ~15. Fix: correct these.

**12. PR-07 cannot be executed/verified where it sits.** `create_opus_models.sh` needs a live imported DB, unavailable GitHub-side until PR-19. Fix: state that PR-07 restructures the checked-in models by hand with a script-based `_meta` diff (no DB); generator changes validated on the self-hosted runner; PR-09 re-runs under 5.2.

**13. setuptools-scm version file with five `src/` packages is unaddressed.** Template `write_to` targets one package. Fix: name the canonical location and how each `__init__` surfaces the version.

**14. The `opus_secrets` "temporary shim" (PR-04→PR-08) is undefined.** "One temporary shim" is a design, not an instruction. Fix: specify it (env var + CWD fallback module in `opus_config`, deleted in PR-08) and update the CI script that `cd`s into `opus/import`.

## MINOR

**15.** PR-01 "ruff-clean" understates the burn-down (E501/E722/F403/F405 across ~46K lines); seed per-file-ignores explicitly.
**16.** No GitHub-hosted CI runs the new pytest suites until PR-19; add the pytest job at PR-03.
**17.** `.cursor/rules` contains 17 rules, not 18; template also runs `ruff format --check` and pymarkdown/pyroma — declare those deviations.
**18.** `u28_…xml` is untracked; PR-02 cannot "delete" it in a commit.
**19.** Legacy root files unaddressed (CODING_STYLE.md, CODE_OF_CONDUCT.md, CODE_REVIEW_TEMPLATE.txt, browserstack png, install.md).
**20.** `_read_opus_secrets.sh` is a second, shell-format secrets file; the deploy chain consumes shell variables — PR-08/PR-22 must acknowledge.
**21.** Marker exclusion mechanics unspecified (addopts `-m` vs directory separation).
**22.** Top-level package name `opus` collides with a generic import name; declare accepted.

## NITS

**23.** Issue #383's title is "API needs to be stress tested"; the plan implements only the body (exception architecture) — don't claim #383 wholesale.
**24.** `config_targets.py` is 1,003 lines — the split is mandatory, not optional.
**25.** Verified-correct claims (for the record): `main_opus_import.py:442` get_db/DB_BRAND; `importdb/super.py:113` `showarning`; hstjx unbound wr/bw; hstox None comparison; covims code-after-return; dictionary consumers = paraminfo/ui/cart; DRF used only by test_api; `hurry.filesize` single site; the CLI flags; `metadata/views.py:533-546` `extra()`; tag_re monkeypatch; `quide` stale dir; ~400 (411) golden fixtures; surface-geometry normalization at `do_import.py:1454-1456`.

## Verdict

Well-researched — most factual claims check out — but **not executable as written**. Three structural blockers (no CI on rewrite PRs; impossible 90% gate; the first move PR reds the integration workflow) plus specification-gap majors. With the blockers fixed and the major ambiguities pinned down, the PR sequence itself (ordering, move/modify separation, phase structure) is sound and executable.

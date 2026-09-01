# The rms-opus modernization: outcome compared against the pre-modernization critiques

**Date:** 2026-09-01
**Tree assessed:** `2bfc2a0e57d4ccb1465775e8e32a7f564d1f2bb1` (branch `pr-24-merge-to-main`), verified
with `git rev-parse HEAD`.
**Pre-modernization baseline:** `origin/main` at `1e11d9948bcaf59be353f5480013fd15f2786c55`
(2026-05-07), the last commit before the rewrite branch diverged. Every "before" figure below
was measured against that tree, not copied from a report.

**Inputs compared**

| Era | Document | Scope |
| --- | --- | --- |
| Before | `critiques/archive/2026-02-17_opus_import_codebase_analysis.md` | `opus/import` — 43 findings |
| Before | `critiques/archive/2026-02-17_opus_apps_codebase_analysis.md` | `opus/application/{apps,test_api,templates}` — 49 findings |
| Before | `critiques/archive/2026-02-17_opus_js_codebase_analysis.md` | `opus/application/static_media/js` — 37 findings |
| Before | `critiques/archive/2025-11-25_css_html_modernization_report.md` | CSS and HTML templates |
| After | `2026-09-01_opus_import_codebase_analysis.md` | `src/opus_import`, `src/opus_support`, `src/opus_config` |
| After | `2026-09-01_opus_app_codebase_analysis.md` | `src/opus_app`, `src/opus_log_analyzer` |
| After | `2026-09-01_documentation_critique.md` | README, `docs/`, docstrings, both build gates |

The three 2026-09-01 critiques were written by independent agents against this exact tree; none of
them read the 2026-02-17 material. Where a 2026-09-01 finding lands on the same line of code as a
2026-02-17 finding, that is independent rediscovery, and it is called out as such below — it is the
strongest available evidence that something was genuinely not addressed.

Every "Fixed" classification below was checked against the tree at HEAD rather than inferred from
the new reports. Where a file moved (most of them did — `opus/import/` → `src/opus_import/`,
`opus/application/apps/` → `src/opus_app/apps/`), the current location was found before anything was
declared gone.

---

## Executive summary

### What the modernization demonstrably fixed

**The type and lint story was inverted.** The pre-modernization tree had zero type annotations
across both Python codebases and a `.flake8` whose `extend-ignore` silenced, by name, E722 (bare
except), F403/F405 (wildcard imports) and E501 — the exact rules whose violations the 2026-02-17
critiques listed as Critical and High. At HEAD, an AST walk of `src/` finds **1,537 of 1,537
functions in `opus_import` and 214 of 214 in `opus_app` carrying complete parameter and return
annotations**, with zero unannotated functions in `opus_import`, `opus_app`, `opus_support` or
`opus_config`; `mypy` runs `strict = true` with no `ignore_errors` entry anywhere; and
`[tool.ruff.lint.extend-ignore]` is down to `["PT011", "SIM105", "SIM108", "PT009", "PT027",
"E501"]` with `per-file-ignores` empty. Bare `except:` and `import *` are both at **zero** in `src/`.

**The SQL and credential findings are closed on both sides, by the same design.** Both 2026-02-17
critiques raised SQL construction; both 2026-09-01 critiques independently attacked the result and
could not break it. `src/opus_import/importdb/mysql.py:281-296` and
`src/opus_app/apps/tools/sql_builder.py:100-115` each validate an identifier against
`\A[A-Za-z0-9_]+\Z` *before* backtick-quoting it, and each explains that the validation, not the
quoting, is what closes the hole. `bandit` reports zero findings over the import packages. The two
util scripts the old import critique flagged for f-string SQL and `from secrets import *`
(`get_opus2_mults.py`, `obs_table_to_schema.py`) no longer exist; neither does `opus_secrets.py` nor
`dictionary/secrets_template.py`. Configuration is now one TOML file located by `OPUS_CONFIG` with
no default path, copied via `install -m 600` because it holds a password.

**The import pipeline's structural findings were addressed as recommended.** `impglobals.py` and its
12 mutable globals are gone, replaced by `ImportContext` at `src/opus_import/context.py:141` —
precisely the remedy the old critique proposed. `do_import.py` (1,778 lines) is now thirteen modules
under `src/opus_import/steps/`; `config_targets.py` (1,003 lines) is a four-module package.
The ~18 duplicated SCLK try/except/log blocks collapsed into one `ObsBase._parse_sclk`
(`obs_base.py:915`) with per-mission wrappers, and `except Exception` in `src/opus_import/obs/` fell
from roughly 18 sites to 4. **All five specific runtime bugs the old import critique named are
fixed**: the `warnings.showarning` typo, the unbound `wr`/`bw` path in `obs_volume_hstjx_xxxx.py`,
the unguarded `wr1 > wr2` comparison in `obs_volume_hstox_xxxx.py`, the fall-through in
`obs_profile_pds4.field_obs_profile_occ_type`, and the code after `return` in
`obs_volume_covims_0xxx.py`.

**"Zero automated tests" became a three-tier suite.** 395 test functions in the holdings-free tier
(36 files), 65 in `import_tests/`, 1,580 in `integration_tests/` — 2,040 in all, against a
pre-modernization count of zero for the import package. `opus_support` and `opus_config` are at 100%
statement and branch coverage (measured by the 2026-09-01 import reviewer). The distribution is
pip-installable with three console scripts, `py.typed` in all five packages, and no `sys.path`
manipulation outside `docs/conf.py`.

### What it did not fix

**The largest functions got larger.** The single highest-priority recommendation in both 2026-02-17
critiques was to split oversized modules and functions. On the web side, all five view modules the
old critique named grew: `ui/views.py` 1,827 → 2,278, `search/views.py` 2,034 → 2,222,
`results/views.py` 1,894 → 2,128, `cart/views.py` 1,561 → 1,839, with `metadata/views.py` newly over
at 1,085. `api_normalize_url`, the old critique's eighth priority at 825 lines, is now **1,028 lines
with 197 branch nodes in one function**. On the import side the two functions the old critique named
for extraction both grew: `import_one_index` 540 → **612 lines at nesting depth 8**,
`import_observation_table` 270 → **350 lines at depth 8**. `search/models.py` is still one
709,805-character file (703,286 before).

**No *fast* tier reaches the code the old critiques were worried about — but the gated slow tier
covers it completely.** The app reviewer has withdrawn the original framing: `opus_app` is not
untested. The self-hosted integration run holds `src/opus_app/apps/*` at **100% line and branch**,
enforced at exactly 100% by `scripts/automated_tests/opus_check_coverage.sh` and green on this PR
(run 33534739355: TOTAL 22,240 statements, 1,874 branches, 0 missed, 2,576 tests in 4m01s). What
survives is narrower: the holdings-free `pytest` executes none of those 3,762 statements, and
`opus_app` is not in `[tool.coverage.run] source`, so the GitHub-hosted Unit Tests job measures none
of it — the view layer has no tier a contributor without the terabyte holdings can run, which is a
feedback-loop constraint rather than a coverage gap. `opus_import`'s fast tier reaches 40%, with
`do_import_index.py` at 3% and `do_import_obs.py` at 6% — the two functions above; that half of this
item belongs to the import reviewer and is unchanged. The old apps critique's judgment that "current
tests provide almost no coverage of actual functionality" is **not** carried forward for the
application: it is false of the suite that gates it.

**A set of small defects survived verbatim.** `_PARAMINFO_CACHE` is still unbounded
(`search/views.py:1231`); `added = []` is still a list membership-tested per file
(`cart/views.py:723`, `:790`); `manifest_fp = open(...)` and `url_fp = open(...)` still have no
context manager (`cart/views.py:713`, `:719`, now carrying `# noqa: SIM115`); `__unicode__` is still
at `paraminfo/models.py:63`; `# this is not being used` is still line 1 of `cart/models.py`;
`.find(x) != -1` still appears 31 times in `src/`; and "compatability" (2) and "contraints" (3) are
still misspelled. The first three were independently rediscovered by the 2026-09-01 app reviewer,
two of them at a higher severity than in February.

### What was deferred by decision

**The front end was not modernized, and this is verifiable rather than asserted.** Diffing the
pre-modernization static tree against HEAD produces **six lines of difference in total**. Twelve of
the thirteen JavaScript files are **byte-identical** to `origin/main`; `opus.js` differs by five
deleted lines (the in-app API guide page, which moved to Sphinx); `dictionary.js` was deleted with
the dictionary app. On the CSS side `opus.css` differs by 85 lines and three files were deleted
(`api_guide.css`, `dictionary.css`, `slidingPanel.css`). Of 35 HTML templates, 30 survive and 26 are
byte-identical. Consequently **36 of the 37 findings in the 2026-02-17 JavaScript critique still
stand exactly as written**, and the CSS/HTML report's findings stand except where a whole file was
deleted. This is recorded as a deliberate deferral — issues #1436 (bundler) and #1489 (front-end dev
docs) — not a failure; the modernization plan scoped itself to Python.

The public web API's backwards-compatibility paths (`ring_obs_id`, old slugs, `api/metadata_v2/`)
also survive, under the waiver recorded at `docs/dev_guide_conventions.rst:74-79`. The old apps
critique's tenth priority — "assess whether old-format support is still needed" — was assessed and
answered: it is kept.

### Tallies

| Old critique | Findings | Fixed | Partially fixed | Not fixed | Superseded | Deferred / out of scope by decision | Affirmations still true |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2026-02-17 import | 43 | 25 | 7 | 5 | 3 | 0 | 3 |
| 2026-02-17 apps | 49 | 16 | 8 | 18 | 5 | 1 | 1 |
| 2026-02-17 JavaScript | 37 | 0 | 0 | 0 | 1 | 36 | 0 |
| 2025-11-25 CSS/HTML | (by category) | 0 | 0 | 0 | 3 files deleted | all | 0 |

---

## 1. The 2026-02-17 import critique (`opus/import`)

The old critique's summary sentence — "zero automated tests, zero type annotations, near-zero
docstrings across all 72 files, two modules exceeding the 1000-line limit, pervasive mutable global
state via `impglobals`, bare `except:` clauses, and wildcard imports" — is false in every clause at
HEAD except the docstring one, which is now a narrow, written-down exemption.

### Classified findings

| § | Finding (severity) | Class | Evidence at HEAD |
| --- | --- | --- | --- |
| 1 | Two modules over 1,000 lines: `do_import.py` 1,778, `config_targets.py` 1,003 (High) | **Fixed** | `do_import.py` split into 13 modules under `src/opus_import/steps/`, largest `do_import_index.py` at 888; `config_targets/` is a 4-module package, largest `target_name_info.py` at 476. Two *different* modules now exceed the limit — see §7 below. |
| 1 | No package `__init__.py`; imported via `sys.path` (Medium) | **Fixed** | `src/opus_import/__init__.py` exists and deliberately imports nothing; the package is installed, not path-injected. |
| 1 | 12 mutable globals in `impglobals` plus 3 in `do_import` (High) | **Fixed** | `impglobals.py` does not exist. `ImportContext` at `src/opus_import/context.py:141` is the recommended remedy, implemented. |
| 1 | SCLK try/except duplicated 18+ times (Medium) | **Fixed** | One `ObsBase._parse_sclk` (`obs_base.py:915`); `_parse_cassini_sclk`/`_parse_voyager_sclk`/`_parse_galileo_sclk` wrap it; `tests/opus_import/test_obs_sclk_call_sites.py` guards the call sites. |
| 1 | Deep, undocumented MRO (Low) | **Fixed as recommended** | The hierarchy is unchanged, which is what the critique wanted; its remedy ("document the MRO explicitly in a class hierarchy diagram") is met by four Mermaid `classDiagram` blocks and `dev_guide_import_obs{,_classes}.rst`. |
| 1 | `instruments.py` effectively dead code (Low) | **Partially fixed** | `PDSTABLE_PREPROCESS` is still an empty list, the loop that would consume it is still commented out at `import_util.py:426-430`, and the unreachable `else` at `:442-450` is the module's only use of `pdsparser`. The module now documents its own deadness candidly. **Independently rediscovered** (new import critique §1, "a pocket of dead machinery"). |
| 1 | `importdb/postgresql.py` an empty stub (Low) | **Partially fixed** | Still a stub, but its docstring now says outright that nothing is implemented and `get_db` has no branch returning it. The new critique flags only the commented-out imports around it. |
| 2 | `from opus_secrets import *`, `from config_data import *`, `from secrets import *` (Critical) | **Fixed** | Zero `import *` anywhere in `src/`; no secrets module exists. |
| 2 | Bare `except:` at four named sites (High) | **Fixed** | Zero bare `except:` in `src/`. The pre-modernization `.flake8` listed E722 in `extend-ignore`; the current ruff config does not. |
| 2 | Broad `except Exception` for SCLK, 18 instances (High) | **Fixed** | Consolidated into the one helper. Note a partial disagreement with the old remedy: the helper still catches `Exception`, and the new critique defends two other broad catches as correct — see §7. |
| 2 | `assert` for validation; `assert False` as must-override (Medium) | **Partially fixed** | `assert False` is gone — `importdb/super.py` raises `NotImplementedError` in 35 places. But 317 `assert` statements remain in `src/`, and the new critique finds a public parser validating its argument with one (`sclk.py:391`). |
| 2 | Three `sys.path.insert` calls in the entry point (Medium) | **Fixed** | The only `sys.path` mutation in the repository is in `docs/conf.py`. |
| 2 | `.find(x) != -1` instead of `in`, 15+ instances (Medium) | **Not fixed** | 31 `.find(` sites in `src/`, e.g. `import_util.py:319`, `obs_cassini_common_pds3.py:83,124,172-182`, `search/views.py:2132`. Neither 2026-09-01 critique mentions it. |
| 2 | Mutable default `mult_form_types=[]` (Low) | **Fixed** | `super.py:91` is now `mult_form_types: Sequence[str] \| None = None`. |
| 2 | `warnings.showarning` typo (Low) | **Fixed** | Every occurrence in `super.py` and `cli.py` is `showwarning`. |
| 3 | Zero type annotations across 72 files (Critical) | **Fixed** | Measured: 1,537/1,537 `opus_import` functions fully annotated, 0 unannotated. `mypy strict = true`, no `ignore_errors`. |
| 3 | Near-zero docstrings (Critical) | **Partially fixed** | Measured: modules 91/91, classes 67/67, non-`field_*` functions 100% documented. **1,186 `field_*` methods remain undocumented** — now a deliberate policy stated at `docs/dev_guide_conventions.rst:88-93`, and re-raised as High by the documentation critique (F2.1) because `:undoc-members:` publishes all of them. |
| 3 | No `__all__` anywhere (High) | **Fixed** | Five packages declare one, including `importdb/__init__.py` and `opus_support/__init__.py`'s sorted 54-name list. |
| 4 | Zero automated tests for the import package (Critical) | **Partially fixed** | `tests/opus_import/` (14 files) plus `import_tests/` (65 test functions) plus a mini-holdings golden suite. But the fast tier reaches 40% of `opus_import`, and the two functions the critique named first are at 3% and 6%. |
| 5 | `upsert_rows` upserts one row at a time (Medium) | **Fixed** | `mysql.py:960` groups by column set and writes 1,000-row packets with `ON DUPLICATE KEY UPDATE` using the MySQL 8.0.19 row alias, with the floor's reason documented. |
| 5 | `NoDupLogger` uses lists for dedup (Medium) | **Fixed** | `import_util.py:722-725` — four `ClassVar[set[str]]`. |
| 5 | `table_exists` rebuilds a lowered list per call (Low) | **Not fixed** | `super.py:398` still `[x.lower() for x in self.table_names(namespace)]` on every check. Not rediscovered. |
| 5 | Good use of `lru_cache` (affirmation) | **Still true** | The new critique lists caching as a strength and notes each instance documents its own reason. |
| 6 | `impglobals` coupling defeats testing (High) | **Fixed** | Same remedy as above; `tests/opus_import/conftest.py` builds a context per test. |
| 6 | Obs hierarchy well-designed; add an architecture diagram (affirmation) | **Still true, and acted on** | The new critique calls it "a genuinely good design for this problem"; four class diagrams now exist. |
| 6 | `import_observation_table` 270 lines (Medium) | **Not fixed — regressed** | `steps/do_import_obs.py:42`, **350 lines at nesting depth 8**. |
| 6 | `import_one_index` 540 lines (Medium) | **Not fixed — regressed** | `steps/do_import_index.py:45`, **612 lines at nesting depth 8**; 17 of 1,604 functions in scope exceed 100 lines, so these two are extreme outliers. |
| 6 | Dead/unreachable code in `cassini_occ_common`, `covims_0xxx` (Low) | **Fixed** | The commented-out multi-target block is gone; `field_obs_general_ring_obs_id` (`covims_0xxx.py:141`) ends at its `return`. |
| 7 | SQL injection risk in `util/get_opus2_mults.py`, `util/obs_table_to_schema.py` (High) | **Superseded** | Both scripts are deleted. `src/opus_import/util/` holds only `dump_pds_definitions.py` and `retrieve_ra_dec.py`. |
| 7 | `from secrets import *` in those util scripts (High) | **Superseded** | Same deletion; no `secrets` module exists anywhere. |
| 7 | Credentials via parameters from `opus_secrets` (Medium) | **Fixed, beyond the recommendation** | The critique suggested environment variables; the tree went further — one TOML file named by `OPUS_CONFIG` with **no default path**, so a server hosting several installations cannot pick up a neighbor's settings. |
| 7 | SQL identifiers interpolated as f-strings without validation (Medium) | **Fixed** | `_IDENTIFIER_RE = \A[A-Za-z0-9_]+\Z` enforced in `quote_identifier` (`mysql.py:281-296`) before quoting; every value bound as `%s`; `bandit` clean; four `# nosec B608` markers each name their rule and reason. |
| 7 | Unescaped `bundle_id` in a `WHERE` clause (Low) | **Fixed** | The new reviewer traced all six caller-supplied `where` fragments: each is a literal built from `quote_identifier` with `%s` placeholders, values travelling in `where_params`. |
| 8 | Dependencies not declared in a `pyproject.toml`/`requirements.txt` (Medium) | **Fixed, with a live caveat** | `pyproject.toml` declares every dependency and justifies every floor. The caveat is a new failure of the same kind: `rms-pdsfile>=0.0.18` is not what CI installs — see §6. |
| 8 | Entry point assumes a specific repo layout (Medium) | **Fixed** | Three console scripts; package data reached through `importlib.resources`, not `__file__`. |
| 8 | `opus/import/README.md` is a scratchpad TODO list (Low) | **Fixed** | The file is gone. Its content — `apt-get` lines and a twelve-item TODO list, verified on `origin/main` — is replaced by eight `dev_guide_import*.rst` chapters. |
| 8 | Good internal docs exist (`database_schema.md`, `opus_id_format.md`) (affirmation) | **Still true — carried forward** | Both files are gone from their old location; their content lives in `docs/dev_guide_database.rst` (the chapter the reviewer's suggestion to "cross-reference from README" now points at) and `docs/dev_guide_opus_id.rst` (533 lines). |
| 9 | 13 TODO/TODOPDS4/XXX markers (High) | **Partially fixed** | **27 marker lines.** Rule, stated inline so the figure is checkable: *lines* under `src/` matching any of `TODO`, `FIXME`, `XXX` or `HACK`, restricted to Python source with `--include=*.py`. Breakdown, same units: 5 `TODO` + 9 `TODOPDS4` + 13 `XXX` = 27; `FIXME` and `HACK` are zero. Of the 13 `XXX` lines, three (`search/views.py:611`, `:639`, `:664`) use `XXX` as a slug placeholder — `# XXX=5 then they also say qtype-XXX=all` — not as a marker, so **24 lines carry a genuine marker**. The `--include=*.py` restriction is deliberate and load-bearing: sweeping every file type under `src/` gives 25 `XXX` lines and 11 `TODO` lines, but the additions are in the front end this report treats as deferred (§3), in four JSON table schemas where `XXX` is data (a NAIF-ID or MIPL-code placeholder inside a product definition), and in vendored third-party code — Django's bundled admin JavaScript and the tooltipster CDN fallback. `TODOPDS4` now functions as a searchable category (9 of the 27). Cross-checks hold: the new app critique's 8 unlinked `XXX` in `ui/views.py` is confirmed exactly, and the new import critique counts 13 within its own package scope. |
| 9 | Five specific potential bugs (High) | **Fixed — 5 of 5** | Verified individually; see the executive summary. |
| 9 | Pervasive magic numbers (Medium) | **Partially fixed** | `MICRONS_PER_CM = 10000.0` (`obs_wavelength.py:16`) and `EIGHT_/TWELVE_/SIXTEEN_BIT_IMAGE_LEVELS` (`obs_type_image.py:14-16`) exist and are imported across files. But `* 10000  # cm -> micron` still appears twice in `obs_volume_corss_8xxx.py:60,63`, and there is no shared constants module. |
| 9 | README TODO list indicates deferred work (Medium) | **Fixed** | The list is gone with the file. |
| 9 | Deprecated one-time migration util scripts still in tree (Medium) | **Superseded** | Deleted. |
| 9 | "compatability", "contraints" (Low) | **Not fixed** | `obs_volume_nhxxlo_xxxx.py:115` and `obs_volume_nhxxmv_xxxx.py:115`; `steps/do_import_tables.py:60,97,156`. Not rediscovered. |

### Discussion

The import package received the deepest work of the modernization and the classification reflects
it: 25 of 40 defect findings closed, including every one the old critique nominated as a runtime
risk. What did not close divides cleanly into two groups.

The first is cosmetic and simply was not swept: `.find()`, two misspellings, a per-call list rebuild.
Neither new reviewer noticed any of them, which is fair evidence that they are low-value; they are
listed here because the old report raised them and nothing retired them.

The second is the one that matters. The old critique's fifth and sixth priorities were "split
`do_import.py`" and "extract shared SCLK parsing" — both done. Its recommendations to extract
sub-functions from `import_one_index` and `import_observation_table` were not, and both functions
are now larger than when the recommendation was written. The 2026-09-01 reviewer reached the same
conclusion from a standing start and connected it to something the February reviewer could not have
known, because the tests did not exist yet: these two functions are also the least-covered code in
the package. The debt did not merely persist; it concentrated.

Two 2026-02-17 remedies were declined in favor of better ones and should be read as over-delivery
rather than as gaps. Credentials moved past environment variables to a single required
configuration file. And the MRO complexity finding, whose remedy was "document it in a diagram," got
four diagrams plus a chapter.

---

## 2. The 2026-02-17 apps critique (`opus/application/apps`, `test_api`, `templates`)

This is where the record is most mixed. The tooling and safety findings closed comprehensively; the
structural findings — which were the critique's own top two priorities — did not.

### Classified findings

| § | Finding (severity) | Class | Evidence at HEAD |
| --- | --- | --- | --- |
| 1 | Nine apps is a reasonable separation (affirmation) | **Still true** | Eight apps now; `dictionary` was folded into `apps/tools/dictionary.py` (87 lines). |
| 1 | Five oversized files (—) | **Not fixed — regressed** | `ui/views.py` 1,827→**2,278**; `search/views.py` 2,034→**2,222**; `results/views.py` 1,894→**2,128**; `cart/views.py` 1,561→**1,839**; `metadata/views.py` newly at **1,085**; `search/models.py` 703,286→**709,805 chars**. **Independently rediscovered** (new app critique §1). |
| 1 | `search/test_search.py` 175,885 chars (—) | **Not fixed** | Now `integration_tests/apps_db_tests/test_search.py` at **185,422 chars**. |
| 1 | Dead/commented code in `dictionary/{admin,views,urls,tests}.py` (—) | **Superseded** | The `dictionary` Django app no longer exists. |
| 1 | Empty `__init__.py` files without docstrings (—) | **Fixed** | Measured: 40 of 41 `opus_app` modules carry a docstring; the exception is the generated `search/models.py`. |
| 1 | `tools/` is a utility grab-bag (—) | **Not fixed** | Still `tools/`, now with `sql_builder.py`, `dictionary.py` and `file_size.py` added. Not rediscovered as a defect; the new critique names `sql_builder.py` and `api_view` as the best work in the scope. |
| 2 | No type annotations (Critical) | **Fixed** | 214/214 functions annotated. |
| 2 | Heavy raw SQL string concatenation (High) | **Fixed** | `apps/tools/sql_builder.py` (714 lines, 99% covered by a 448-line unit test) is used by `cart`, `search`, `results`, `metadata` and `file_utils`. The only surviving `sql +=` lines in `opus_app` are the eleven inside `sql_builder.py` itself. |
| 2 | Bare `except:` (High) | **Fixed** | Zero in `src/`. |
| 2 | `import settings` as a bare module name (Medium) | **Fixed** | `from django.conf import settings` in 14 modules; no bare `import settings`. |
| 2 | Built-in shadowing (Medium) | **Fixed** | Ruff's `A` category is in `select` and the tree passes. |
| 2 | `from __future__ import unicode_literals` (Medium) | **Superseded** | Gone with `dictionary/models.py`. |
| 2 | `get_search_results_chunk` has 12+ parameters (Medium) | **Not fixed** | `results/views.py:1385` now takes **13**, none keyword-only, returning a 7-tuple. **Independently rediscovered** (new app critique §2, which adds that the shape already has a `TypeAlias`). |
| 2 | Inconsistent import ordering (Low) | **Fixed** | Ruff's `I` rules are enforced repo-wide. One blanket exemption survives, on the import side — see §5. |
| 2 | `throw_random_http404/500_error` inline in every handler (Low) | **Fixed as recommended** | Folded into the `api_view` decorator (`app_utils.py:402-424`), driven by settings knobs — the "move to a testing/middleware layer" the critique asked for. |
| 3 | Zero annotations, no `py.typed`, no mypy config (Critical) | **Fixed** | `py.typed` ships in `opus_app` and `opus_log_analyzer`; `mypy strict` with `warn_unused_ignores`. |
| 3 | No ruff or mypy configuration (High) | **Fixed** | Both configured, run by `scripts/run-all-checks.sh` and by CI over the same path lists. |
| 3 | Docstrings omit Google-style sections (High) | **Partially fixed** | Every hand-written module, class and function is documented. But the documentation critique measures **131 documented functions with parameters and no `Parameters:` section, 244 that return with no `Returns:`, 35 that raise with no `Raises:`** — concentrated in `sql_builder.py` (44), `app_utils.py` (24) and `url_to_search_params`. |
| 4 | Unit tests cover only null-request edge cases (High) | **Partially fixed** | The null-request checks are factored into `integration_tests/apps_db_tests/_broken_requests.py` and the suites around them grew substantially (1,580 integration test functions, 410 stored responses vs 347). But the holdings-free `tests/opus_app/` tier covers only six modules, and **3,762 view-layer statements measure 0%** under `pytest`. **Independently rediscovered and escalated** (new app critique §4, High). |
| 4 | `test_api/` is thorough but slow; add fast isolated tests (Medium) | **Partially fixed** | `tests/opus_app/` exists (6 files, 1,627 lines) but reaches only `settings` and four `tools` modules. |
| 4 | Tests use `unittest.TestCase`, not `django.test.TestCase` (Medium) | **Not fixed, and the recommendation is now known-unsafe** | See "Contradictions" below. |
| 4 | Test class names are lowercase (`cartTests`) (Medium) | **Fixed** | `CartTests`, `HelpTests`, `MetadataTests`, `ResultsTests`, `UiTests`, `SearchTests`, `FileUtilsTests`. |
| 4 | `print()` in tests (Low) | **Partially fixed** | 5 in `tests/`, 11 in `import_tests/`, **788 in `integration_tests/`**. |
| 4 | `dictionary/tests.py` empty (Low) | **Superseded** | App removed; `tools/dictionary.py` is reached by the integration suite. |
| 5 | `open()` without `with` in `api_create_download` (High) | **Not fixed** | `cart/views.py:713`, `:719`, now with `# noqa: SIM115`. **Independently rediscovered** (new app critique §7), which adds that `_create_csv_file`'s return value is discarded at `:649`, turning a clean 500 into a `FileNotFoundError` with leaked handles. |
| 5 | `_get_download_info` runs two queries with ~200 lines of hand-built SQL (Medium) | **Partially fixed** | Now `cart/views.py:856`, built through `sql_builder`; still two queries. |
| 5 | Temporary MySQL tables created and dropped per call (Medium) | **Fixed / restructured** | Replaced by named cache tables built once via `sql_builder.create_table_from_select_sql` (`search/views.py:1067`) and memoized in the Django cache. |
| 5 | `_PARAMINFO_CACHE` is unbounded (Medium) | **Not fixed** | `search/views.py:1231`, with nine touch points and no eviction. **Independently rediscovered and escalated to High** — the new critique traces an unauthenticated path (`/__normalizeurl.json?a1=x&a2=x&…`) that interns one permanent entry per unknown slug, with an ERROR log line each. |
| 5 | `added = []` gives O(n) membership (Low) | **Not fixed** | `cart/views.py:723`, `:790`, `:815`. **Independently rediscovered and escalated to Medium** (the cart admits 10,000 observations). |
| 6 | Tight coupling between apps (High) | **Not fixed** | `cart/views.py` still imports from `metadata.views`, `results.views`, `search.views`, `search.models` and four `tools` modules. |
| 6 | ~20 error-message functions imported individually (High) | **Not fixed as recommended** | 24 module-level `http4xx_`/`http5xx_` builders, still imported by name. The new critique names the prefix convention a strength, so the design was kept deliberately rather than overlooked. |
| 6 | `enter_api_call`/`exit_api_call` boilerplate (Medium) | **Fixed** | `api_view` (`app_utils.py:430`), 37 uses; the new critique calls it one of the three best things in the scope. |
| 6 | `api_normalize_url` is 825 lines (Medium) | **Not fixed — regressed** | `ui/views.py:922`, **1,028 lines, 197 branch nodes**. **Independently rediscovered** (new app critique §1, High). |
| 6 | Deprecated Django `.extra()` (Low) | **Fixed** | Zero `.extra(` calls in `src/`. |
| 7 | `subprocess` + `os.chdir` in `get_git_version` (Medium) | **Superseded** | `app_utils.py:571` is now one line: `importlib.metadata.version('rms-opus')`. |
| 7 | `dictionary/secrets_template.py` holds placeholder credentials (Medium) | **Superseded** | Replaced by `opus.toml.template`, whose header instructs `install -m 600` and explains why. |
| 7 | No path validation in archive creation (Low) | **Not fixed** | The new critique finds `path.index(settings.PDS3_HOLDINGS_DIR)` unguarded at `cart/views.py:743`, `:775`, raising `ValueError` when a configured root is absent from a stored path. |
| 7 | `StripWhitespaceMiddleware` regex on every response (Low) | **Not fixed** | `tools/opus_middleware.py:27`, still in the chain; now at 100% coverage, and the documentation critique flags its change-log module docstring. |
| 8 | No `requirements.txt` or `pyproject.toml` found (High) | **Fixed; the original claim was scope-limited** | See "Contradictions". |
| 8 | `opus_support` location and maintenance status unclear (Medium) | **Fixed** | `src/opus_support/` — 7 modules, a sorted 54-name `__all__`, and 100% statement and branch coverage. |
| 8 | `re_path` everywhere; migrate simple routes to `path()` (Low) | **Not fixed** | All six `urls.py` files use `re_path` exclusively. Not rediscovered. |
| 9 | `search/models.py` is 700K+ characters (Critical) | **Not fixed** | 709,805 characters, 12,093 lines, one file, still generated by `scripts/models/create_opus_models.sh` and still `managed = False`. The split into a `models/` package did not happen. It is now *handled* rather than fixed: `docs/_ext/opus_api_reference.py:68-76` excludes it from the API reference with a stated reason, and the new app critique explicitly declines to assess it. |
| 9 | `__unicode__` in `paraminfo/models.py` (High) | **Not fixed** | Still at line 63. **Independently rediscovered** (new app critique §1, as dead code — `integration_tests/.coveragerc:28` already excludes it from the coverage gate). |
| 9 | Backwards-compatibility paths: `ring_obs_id`, old slugs, `metadata_v2` (High) | **Out of scope by decision** | `results/views.py:75,93,546,548,894` and `results/urls.py:36`. Kept under the waiver at `docs/dev_guide_conventions.rst:74-79`; `CLAUDE.md` scopes the waiver to the public web API only. |
| 9 | TODO/FIXME/XXX comments and the "Bakwards compatibility" typo (Medium) | **Partially fixed** | 8 `XXX` remain in `ui/views.py`; the typo is still at `results/views.py:296`. |
| 9 | `managed = False` prevents migrations (Medium) | **Partially fixed** | 236 occurrences. The schema-management approach the critique asked to have documented now is, in `cart/models.py`, `tools/dictionary.py` and `dev_guide_database.rst`. |
| 9 | `cart/models.py` opens with a misleading `# this is not being used` (Low) | **Not fixed** | Still line 1 — now sitting directly above a correct, detailed module docstring, which makes it more contradictory than it was. Not rediscovered by either new critique. |
| T | Widget template overrides undocumented (Low) | **Not fixed** | `templates/django/forms/widgets/{input,input_option,multiple_input}.html` carry no explanatory comment. |
| T | `multilines_template_tags.py` monkey-patches `base.tag_re` (Low) | **Partially fixed** | Still a monkeypatch. Now documented to an unusual standard — why it must never be `{% load %}`ed, the Django version verified against, and the three checks run. The new critique's residual objection is different: **no test guards it**, and the failure mode is silent. |

### Discussion

The web application's *safety* and *tooling* debts closed and its *shape* did not. That is a
coherent outcome rather than a random one: everything the modernization could gate — annotations,
lint rules, SQL construction, import hygiene, credential handling, error-response discipline — is
gated and passing, while everything requiring a large behavior-preserving refactor of code with no
fast test net was left alone.

The causal link between those two facts is visible in the record. `api_normalize_url` is the only
place the URL-migration rules exist; it cannot be split safely without tests that execute it; the
tests that execute it need the terabyte holdings; so it was not split, and it grew by 203 lines
instead. The same pattern explains `search/views.py`, `results/views.py` and `cart/views.py`. The
2026-09-01 app reviewer names this as its second priority and identifies the cheap entry point — the
pure query-string paths (`url_to_search_params`, `parse_order_slug`, `get_param_info_by_slug`,
`labels_for_slugs`) need only a `RequestFactory` and three fakes.

The three small findings that survived verbatim and were independently re-found — `_PARAMINFO_CACHE`,
`added = []`, the two unguarded `open()` calls — deserve their top billing in "what remains". Each
was rated Low or High in February with a one-line fix; each is still there; and in two of three cases
the 2026-09-01 reviewer, working blind, raised the severity after finding a consequence the February
reviewer had not traced.

---

## 3. The 2026-02-17 JavaScript critique — deliberate deferral

The front end was excluded from the modernization by decision, tracked as issues #1436 (bundler) and
#1489 (front-end developer documentation). This was verified rather than assumed.

Extracting `opus/application/static_media/` from `origin/main` and diffing it against
`src/opus_app/static/` at HEAD produces **six lines of `diff -rq` output for the entire tree**:

| File | Status |
| --- | --- |
| `browse.js`, `cart.js`, `detail.js`, `hash.js`, `menu.js`, `mutationObserver.js`, `search.js`, `selectMetadata.js`, `sortMetadata.js`, `stringUtils.js`, `utils.js`, `widgets.js` | **byte-identical** |
| `js/README.md` | **byte-identical** |
| `opus.js` | 5 lines deleted (the in-app `apiguide` case) |
| `dictionary.js` | deleted with the dictionary app |
| `css/opus.css` | 85 lines changed |
| `css/api_guide.css`, `css/dictionary.css`, `css/slidingPanel.css` | deleted |

Everything else under `static/` — `admin/`, `cdn_fallback/`, `coreui/`, `feedback/`, `img/`,
`perfect-scrollbar/`, `robots.txt` — is unchanged.

**Therefore 36 of the 37 JavaScript findings still stand verbatim**, including all five the critique
ranked highest:

- No test framework and **zero JavaScript tests** (Critical). Confirmed: no `package.json`,
  `vite.config`, `webpack.config`, `.eslintrc` or `tsconfig.json` anywhere in the repository, and no
  `*.test.js`/`*.spec.js`.
- No ES modules and no bundler (High). Confirmed: the `/* jshint varstmt: false */` global-namespace
  pattern is intact in all thirteen files.
- Oversized files (High). Confirmed unchanged: `browse.js` **3,216** lines, `widgets.js` **1,824**,
  `opus.js` **1,509**, `search.js` **1,302**, `cart.js` **971**, `hash.js` **826**,
  `selectMetadata.js` **556**. (The critique's figures were each one higher — a line-counting
  convention difference, not a change to the code; `opus.js` additionally lost its five lines.)
- JSHint rather than ESLint (Medium). Confirmed: 7-9 `jshint` directives per file, no ESLint.
- HTML built by string concatenation without escaping, an XSS surface (High). Confirmed present.
- `String.prototype.toTitleCase` (Medium). Confirmed at `stringUtils.js:1`.

The one finding retired is the `dictionary.js` half of the two `String.prototype`-extension findings,
which is **Superseded** by that file's deletion.

One item is worth carrying forward with special emphasis. The critique's Critical technical-debt
finding cited `README.md:7` — *"#Todo This needs tests! Also a redux that incorporates a framework
(such as REACT) would provide easier testing…"* — as "a long-standing acknowledged debt item." That
README is **byte-identical** to the pre-modernization tree, including that line. The 2026-09-01
documentation critique found the same file from a completely different direction (F6.1) and called it
"the one file the modernization did not reach," noting that it also documents only 9 of the 13
JavaScript files and so is now the stale duplicate of `docs/dev_guide_webapp_ui.rst:356-395`. Two
independent reviewers, eighteen months apart, on the same forty-five lines.

---

## 4. The 2025-11-25 CSS/HTML modernization report — deliberate deferral

Same disposition, same evidence. Quantitatively, paired against the report's own headline table:

| The report's count | Then | Now | Where the change came from |
| --- | ---: | ---: | --- |
| `!important` declarations | 152 | **145** | The 7 that went were inside deleted files; `opus.css` is essentially unchanged in this respect. |
| Vendor-prefixed declarations | 160 | **73** | Entirely from deleting `slidingPanel.css`, `dictionary.css` and `api_guide.css`. In the two surviving prefixed files (`opus.css`, `loader.css`) the count is **68 → 68**. |
| Deprecated properties, float layouts, inline styles | 15+ / 10+ / 5+ | unchanged | — |

The HTML side is likewise untouched: of 35 templates under the apps tree, 30 survive and only
`ui/base.html` differs; `help/apiguide.html` and `help/apiguide_print.html` were deleted when the API
guide moved to Sphinx, and `400.html`/`404.html` were added. Spot-checking the report's named
instances at HEAD: `valign="top"` still appears **10 times** in `help/about.html`; `splash.html`
still carries **4** inline `style` attributes; `base.html` still has **no `<main>` element**; and
`detail.html:27` still opens the `<ul class="op-detail-list">` the report flagged for containing an
`<h4>`. The accessibility findings (WCAG, 10+ items rated High) are untouched.

Nothing in the report was addressed, and nothing in it was invalidated except by file deletion. It
should be read as a live backlog against issue #1436, not as a closed review.

---

## 5. Where the documentation stands now

**The 2026-09-01 documentation critique has no predecessor.** No pre-modernization document reviewed
the documentation as a subject. The only baseline available is what the 2026-02-17 code critiques
said in passing, which was this: the import package's README "is a scratchpad TODO list, not
documentation… No usage instructions, no architecture overview, no Python version or venv
requirements" (Low), against which "good internal documentation exists for DB schema and OPUS ID
format" (Low). The apps critique said nothing about documentation at all beyond docstrings.

That baseline is verifiable on `origin/main`:

| | Pre-modernization (`origin/main`) | HEAD |
| --- | --- | --- |
| Documentation system | none | Sphinx under `docs/`, one `conf.py`, published to Read the Docs |
| Narrative documentation | **4,087 lines of Markdown total**, scattered: `README.md` (16 lines), `install.md` (68), `CODING_STYLE.md`, 11 per-app `README.md` files, `opus/import/README.md` (a TODO list), `opus/import/docs/{database_schema.md (625), opus_id_format.md (300), adding_an_instrument_or_mission.md (17)}`, `apps/help/api_guide.md` (2,161) | **13,875 lines** across 39 `.rst`/`.md` files: a 3-chapter public API guide, a 30-chapter developer guide, and a generated API reference |
| API reference | none | generated by walking the packages (`docs/_ext/opus_api_reference.py`), so a new module cannot be silently missing |
| Metadata-field appendix | none | generated from the checked-in table schemas (`docs/_ext/opus_field_tables.py`), so it cannot drift |
| Build gate | none | `-W -n` enforced in four independent places: `conf.py:103` (`nitpicky = True`), `docs/Makefile:8`, `run-tests.yml:385`, `.readthedocs.yaml:36` |
| Root `README.md` | 16 lines | 153 lines, all nine `doc_readme.mdc` sections in order, both Quick Start examples executed by the reviewer and confirmed runnable |
| Diagrams | none | 10 Mermaid diagrams across 8 chapters, rendered client-side so CI needs no browser |

The reviewer measured the build: all three invocations (`-W`, `-n`, and a clean `-W -n -E` rebuild)
exit 0 with **zero warnings of any category**, no unresolved cross-reference, and no document outside
a `toctree`. Docstring presence on hand-written code is total — 158/158 modules, 134/134 classes,
243/243 private functions, 32/32 dunders, 566/566 non-`field_*` public functions — and there are
**zero `Args:` sections** anywhere in `src/`, against 476 `Parameters:`. I reproduced the docstring
figures independently by AST walk and got the same shape.

Against that, three structural gaps, none of which the February baseline could have named:

1. **There is no user guide** (F5.1). No `docs/user_guide/` tree, no user-guide chapters. The
   distribution publishes three console scripts to PyPI, and the material a user of them needs —
   installation from PyPI, the configuration model, the CLI references — is filed under the
   *developer* guide, which addresses itself to "people who modify, extend, build, test, release or
   deploy OPUS." The rule is not applied and the decision not to apply it is not recorded in the
   chapter that records deviations.
2. **1,186 public methods carry no docstring and `:undoc-members:` publishes every one** (F2.1).
   Verified in the rendered HTML: 1,185 bare, description-free entries on a single 1.5 MB page. This
   is the same population as the import critique's §3 finding, seen from the other end. The policy
   behind it is deliberate and written down (`dev_guide_conventions.rst:88-93`) and the reviewer
   agrees with the reasoning; the objection is that the published artifact carries no on-page
   explanation.
3. **Code objects are marked up as text rather than linked** (F3.1). `default_role` is unset in
   `docs/conf.py` — confirmed — so the single-backtick convention used throughout `src/` renders as
   italic prose linking nowhere: **418 such spans over 269 distinct targets**, every one from a
   docstring and none from a `.rst` file. The nitpicky gate is structurally blind to them, because a
   `title_reference` is not a cross-reference. A related 142 prose mentions name symbols the API
   reference gives no target to, chiefly because 130 of 138 module-level constants under `src/` carry
   no attribute docstring — so `BUNDLE_INFO`, the registry the entire import pipeline turns on,
   appears nowhere in the published reference.

Plus a handful of factual defects, of which one is served on the documentation site: `CONTRIBUTING.md:68`
states **"Ensure compatibility with Python 3.10+"** — confirmed at HEAD — against `requires-python =
">=3.12"` and five other statements of 3.12, and `docs/dev_guide_contributing.rst:9` includes the file
whole. Two public API parameters (`hierarchical`, and `tar`/`tgz` as download formats), one public
route (`api/metadata_v2/`) and all seven `opus_error_analyzer` command-line entries are documented
nowhere.

**Net assessment.** Documentation went from an unbuilt, ungated, four-thousand-line scatter of
Markdown to a fourteen-thousand-line Sphinx tree with four independent zero-warning gates, two
generators that make whole classes of drift structurally impossible, and total docstring coverage on
hand-written code. It is the most complete single improvement in the modernization. Its remaining
gaps are of a kind that only exists once you have a documentation system at all.

---

## 6. What the fresh critiques found that predates no old report

Ordered by significance, with convergence noted.

**1. The declared `rms-pdsfile` dependency is not what CI tests, and a docstring asserts the
opposite. Found independently by both new code critiques.** `pyproject.toml:31` declares
`rms-pdsfile>=0.0.18`; `[[tool.mypy.overrides]]` (`:343-346`) deliberately omits `pdsfile`; and
**six** CI steps across `run-tests.yml` (`:102`, `:196`, `:296`, `:377`, `:455`) and
`run-integration.yml` (`:141`) replace the declared dependency with
`rms-pdsfile @ git+https://github.com/SETI/rms-pdsfile@rewrite`, an unpinned branch tip. The import
reviewer downloaded the current PyPI release (0.1.2) and confirmed it ships no `py.typed`; running
mypy against the declared dependency set produces 20 `import-untyped` errors in 14 files. And
`src/opus_import/obs/obs_base.py:183-185` states as fact that *"`pdsfile` ships `py.typed`, so it
carries no `ignore_missing_imports` entry and every call on the returned object is type-checked."*
Two reviewers with disjoint scopes reached this independently; it is the only finding that affects
everyone who installs the distribution as published, and it is the single strongest item in "what
remains." Its ancestor is the old import critique's §8 "dependencies not declared" — the same class
of defect, recreated one level up.

> **[Note added after analysis.]** This report is a dated snapshot of `2bfc2a0e` and every citation
> in it is anchored there. Two of this paragraph's anchors have since moved within the same pull
> request that ships it. The `obs_base.py:183-185` docstring sentence quoted above was **deleted by
> commit `67714dfc`**, so the "and a docstring asserts the opposite" half of this finding is fixed;
> it is left standing as the record of what the two independent critiques found, not as an open
> defect. The workflow line numbers were invalidated by commit `f91c6ec0`, which trimmed both files;
> the six install steps themselves were deliberately kept as infrastructure, so the finding's
> substance is unchanged — locate them with `grep -n "rms-pdsfile @ git" .github/workflows/*.yml`
> rather than by line number — and note that a single-line `grep` for `pip install "rms-pdsfile`
> finds only five, because the sixth, in the `package` job, is split across a line continuation.
> Six is the correct count.

**2. Three unauthenticated query strings turn into HTTP 500s, and one public parameter does the
opposite of what it documents** (app §2, High). `parse_order_slug(',')` raises `IndexError`
(`search/views.py:2175`); `?=x` on any search endpoint raises `IndexError`
(`search/views.py:1382`); and `?hierarchical=x` on `__cart/download.json` is unguarded
(`cart/views.py:729`). Each of those three writes a full traceback through `log.exception`.
Separately, `url_file_only = request.GET.get('urlonly', 0)` (`cart/views.py:569`) tests a raw
query-string value for truth, so the documented spelling `urlonly=0` returns HTTP 200 carrying an
archive with no data products — a wrong result rather than a 500, and one the golden suite pins
(`test_cart_api.py:4054-4067`). The reviewer notes that
`api_normalize_url` handles the empty order component correctly — the two parsers disagree about the
same input.

**3. Any caller can read and write any session's cart** (app §7, High). `get_session_id`
(`app_utils.py:173-181`) prefers `?__sessionid=<S>` over the real session with no validation and no
environment gate, and every cart handler keys on its return. `docs/dev_guide_webapp_tools.rst:93-95`
documents the hazard plainly — which the reviewer credits as the right instinct while observing that
documenting a hole does not close it. The affordance cannot simply be deleted, because
`integration_tests/test_api/test_cart_api.py:2080-2134` depends on it.

**4. The `integration_tests/` database guard does not cover `tests/`** (app §4, High).
`DATABASES['default']['TEST']['NAME']` is the live schema (`settings.py:374-376`).
`integration_tests/conftest.py` refuses every route to `setup_databases` session-wide, with the full
argument written out — but that conftest loads only when a command line reaches into that directory,
so a `@pytest.mark.django_db` test added under `tests/` and run by a developer with a production
`OPUS_CONFIG` would still reach it.

**5. `opus_log_analyzer` was never critiqued in February and is the weakest package now.** Three of
its four documented modes cannot run (`log_analyzer.py:245` branches on `args.glob`, and no `--glob`
argument is defined), while `--summary` and `--realtime` are still advertised in `--help`. Its 4,158
lines sit in the `fail_under = 75` denominator at 13-44% coverage. `pytz` is used the way pytz's own
documentation forbids, producing a **measured 53-minute UTC-offset error** (`cronjob_utils.py:18`,
`:106-119`). Its docstrings are the only ones below the tree's standard, and none of its 22 + 7
command-line entries beyond eight are documented.

**6. The only blanket lint exemption in the repository, in a project whose configuration claims
none.** `src/opus_import/config_bundle_info.py:11` is `# flake8: noqa`, which ruff honors as a
file-level suppression of every present and future rule and which `RUF100` cannot keep honest — while
`pyproject.toml:423-430` states that `per-file-ignores` is empty and that "a row here is not the way
to land code that does not pass." The reviewer verified both halves: removing the line makes `I001`
fire on an unsorted import block.

**7. Two latent database-layer defects** (import §6, §7). `create_table` maintains its name cache
*inside* an `if self.logger:` block (`mysql.py:714-723`), so with `logger=None` — which `get_db`
accepts by default — the table is created but never enters `_table_names`; `drop_table` gets this
right, so creation and deletion disagree. And `_enter`/`_exit` replace the process-global
`warnings.showwarning` with no `try`/`finally` and no context manager anywhere in the package, so
every one of ~14 raising paths leaks the handler.

**8. Golden suites that pin defects and depend on ordering.**
`import_tests/test_goldens.py:293`'s session-scoped `reimport` fixture mutates the database the
module's own comparisons read, and its docstring states the collection-order dependence rather than
removing it. `integration_tests/test_api/test_cart_api.py:4065-4067` asserts the `urlonly=0` archive
shape from item 2 above — so fixing that public-API bug means changing a golden.

**9. Performance findings on the request path** (app §5). `api/fields.json` issues roughly three
database queries per metadata field on a public, `@never_cache` endpoint; the search menu re-queries
per rendered field **from the template**; importing `settings.py` opens a memcached connection with
no timeout (`:35-40`); the application log holds at most ~150 KB
(`RotatingFileHandler(maxBytes=50000, backupCount=2)`), so any error burst rotates the history away.

**10. A whole documentation critique.** Covered in §5.

A convergence worth naming on the positive side: both new code critiques, independently, singled out
the *same* security design as the best work in their scopes — identifier validation before quoting,
values always parameterized — and both noted that the code explains why the validation and not the
quoting is what protects. That pattern is applied on both sides of the tree from two different
modules, and it is what closed the 2026-02-17 SQL findings on both sides.

---

## 7. Residual risk

Ranked by consequence, combining what the modernization left open with what the fresh critiques
added. Items marked **(rediscovered)** were raised in February, survive at HEAD, and were found again
independently in September.

**Ships a broken PDS4 import path, and an unreproducible type gate, to anyone who installs as
declared**

1. **`rms-pdsfile>=0.0.18` vs the `@rewrite` branch tip — two distinct failures, both on the declared
   floor.**
   *Runtime.* `opus_import` calls `Pds4File.use_shelves_only()` at `src/opus_import/cli.py:561` on
   its default path — `--dont-use-shelves-only` is `store_true` with `default=False`
   (`cli.py:120-124`) — so an ordinary run enables it. That the declared floor cannot serve that
   call is corroborated structurally by the workflows themselves: six steps across `run-tests.yml`
   and `run-integration.yml` replace `rms-pdsfile` with a branch tip before anything runs, and a CI
   that could use the declared dependency would not need to replace it six times. So a PDS4 import
   from a released dependency set fails at runtime, not merely at type-check time.
   The mechanism was written down in the tree this report analyzes. At `2bfc2a0e` each
   `Install the pdsfile rewrite` step read: *"`opus_import` enables `Pds4File.use_shelves_only()`,
   and 0.0.18's empty-key branch returns False with no fall-through, so `from_path` raises there on
   the first PDS4 existence check."* That is a **dated quotation, not a current one**: this PR's
   workflow trim replaced every such block with the single line *"From the branch tip; temporary
   until that work is released,"* keeping all six installs and dropping the explanation for them.
   Two caveats, both deliberate. The mechanism is the project's own written statement rather than a
   reproduction of mine — I had no environment with a released `rms-pdsfile` to run it against. And
   with that explanation now gone from the workflows, the surviving record of *why* CI cannot use
   the declared dependency is this report and the commit history, which is worth knowing before the
   six install steps look like an arbitrary habit to whoever next tries to remove them.
   *Development reproducibility.* Separately and additionally, no released `rms-pdsfile` ships
   `py.typed`, so `pip install -e ".[dev]"` followed by `scripts/run-all-checks.sh` cannot reproduce
   the green mypy gate — 20 `import-untyped` errors in 14 files. That is a type-check gap, not an
   import failure, and the two should not be conflated.
   The docstring that asserted the opposite was deleted in this PR by `67714dfc`; see the note in
   §6.

**Reachable by an unauthenticated caller**

2. **Four query-string paths returning 500 instead of 400**, each writing a full traceback into a log
   that holds ~150 KB.
3. **`_PARAMINFO_CACHE` as a memory-exhaustion vector** — unbounded, keyed on raw query-string slugs,
   amplified by `api_normalize_url`'s continue-past-unknown-slug loop. **(rediscovered)**
4. **`?__sessionid=` reads and writes any session's cart**, and creates unbounded rows under invented
   session ids.
5. **`urlonly=0` silently returns a data-free archive** on a public, documented route — and a golden
   test pins the behavior.
6. **`qtype=regex` runs a user-supplied regular expression against the observation tables with no
   `max_execution_time`**, unlike the string-choices queries a few hundred lines away.

**Structural: change is riskier than it should be**

7. **`api_normalize_url` (1,028 lines / 197 branches) and `url_to_search_params` (570 / 99)** — the
   only place the URL-migration rules exist, unreviewable as a unit, and at 0% under any test a
   contributor without the holdings can run. Both grew during the modernization.
   **(rediscovered)**
8. **`import_one_index` (612 lines) and `import_observation_table` (350)** at nesting depth 8, at 3%
   and 6% fast-tier coverage. Both grew. **(rediscovered)**
9. **3,762 `opus_app` view-layer statements at 0%**, with `opus_app` absent from
   `[tool.coverage.run] source` — so no CI job measures it at all. Every input-validation bug above
   lives in this gap and is reachable from a pure query string with no database row involved.
   **(rediscovered)**
10. **Five modules over the 1,000-line ceiling on the web side, two on the import side**
    (`opus_support/units.py` 1,176, `importdb/mysql.py` 1,191), and `search/models.py` at 709,805
    characters. **(rediscovered)**
11. **Cross-app coupling unchanged** — `cart/views.py` still reaches into four other apps' views and
    models. **(rediscovered)**

**Latent — correct today, wrong under a plausible change**

12. `create_table`'s cache maintenance inside `if self.logger:`; `_enter`/`_exit` without
    `try`/`finally`; `if where:` deciding whether a `DELETE` gets a `WHERE` clause.
13. The `django_db` guard covering `integration_tests/` but not `tests/`, over a test database name
    that is the live schema.
14. The Django template-lexer monkeypatch with no regression test and a silent failure mode.
15. `str(settings.PREVIEW_GUIDES)` emitted as a JavaScript object literal — valid only because the
    shipped value happens to be a flat `dict[str, str]`.
16. `import urllib` followed by `urllib.parse.quote_plus`, working only because Django imported the
    submodule first.
17. Sixteen text-mode `open()` calls with no `encoding=` across both packages, two of them reading
    attacker-controlled Apache log bytes and three of them writing files that ship inside every user
    download.

**Deferred by decision, and still a live backlog**

18. **The entire front end.** No tests, no bundler, no module system, no ESLint; `browse.js` at 3,216
    lines; HTML built by unescaped string concatenation. Verified byte-identical to the
    pre-modernization tree. Issues #1436 and #1489.
19. **The CSS/HTML report** — 145 `!important`, 68 vendor-prefixed declarations in the two files that
    matter, no `<main>` element, `valign` attributes, and the accessibility findings.
20. **Public web API back-compat** (`ring_obs_id`, old slugs, `api/metadata_v2/`) — kept under a
    recorded waiver. The residual risk here is documentary rather than technical:
    `api/metadata_v2/` is a route the project has committed to keep working and it appears in no
    public manual.

**Documentation**

21. `CONTRIBUTING.md`'s "Python 3.10+", served on the documentation site.
22. 418 docstring spans that look like cross-references, are not, and that no gate can see.
23. 1,185 description-free entries on a 1.5 MB published page.
24. `opus_error_analyzer`'s entire command-line surface, and 14 of `opus_log_analyzer`'s.

**Small, verbatim survivors nobody re-found**

25. `.find(x) != -1` × 31; "compatability" × 2 and "contraints" × 3; `table_exists` rebuilding a
    lowered list per call; `re_path` for every route; the undocumented Django widget-template
    overrides; and `# this is not being used` as line 1 of `cart/models.py`, now contradicting the
    accurate docstring directly beneath it.

---

## Appendix: where the old and new records disagree

Four places where a 2026-02-17 statement does not survive contact with the tree or with the
2026-09-01 analysis. None is a large error; all four are worth recording so that the archived
critiques are not read as uniformly authoritative.

**1. "Use `django.test.TestCase` for proper test isolation" is now known to be unsafe.** The old apps
critique (§4, Medium) recommended migrating the app test classes from `unittest.TestCase` to
`django.test.TransactionTestCase`/`TestCase`. The tree did not do it, and the 2026-09-01 app critique
establishes why acting on that advice would have been destructive:
`DATABASES['default']['TEST']['NAME']` is the *live* schema (`settings.py:374-376`), so any
`django.test.TestCase` would hand `setup_databases` a production database to drop and recreate.
`integration_tests/conftest.py:1-52` now refuses `@pytest.mark.django_db`, the `db`,
`transactional_db` and `live_server` fixtures, a direct `django_db_setup` request, and any
`SimpleTestCase` subclass — session-wide — precisely to prevent it. The old recommendation is
superseded by a hazard it did not know about; the finding should be read as closed-by-refutation, not
as outstanding.

**2. "No `requirements.txt` or `pyproject.toml` was found" was a scoping artifact.** The old apps
critique rated this High. Verified on `origin/main`: `requirements.in` and `requirements.txt` both
existed at the repository root, pinning `django == 4.*`, `numpy >= 1.26`, `pillow >= 10.1` and the
rest. The critique's own evidence line ("no lint/type-check configuration files in analyzed
directories") shows it was reasoning from the directories it was handed. The finding's substance —
nothing declared the distribution's dependencies as *metadata* — was real and is fixed; the literal
claim was not accurate.

**3. The two critiques disagree about whether documenting a defect closes it.** The old import
critique's remedy for `instruments.py` was "Remove or explain purpose"; the tree chose *explain*, in
a candid module docstring. The 2026-09-01 import reviewer rejects that resolution explicitly — "a
comment describing a defect does not retire it" — and files the same code as a live finding, adding
the unreachable `else` branch and the orphaned `pdsparser` import that the explanation does not
address. The same disagreement recurs on `postgresql.py`, on `--cronjob`'s deprecation, and on
`get_session_id`'s documented hazard. This is a genuine methodological difference between the two
eras, not a factual conflict, and it is worth deciding deliberately: the current tree's house style
is to document rather than delete, and the fresh reviewers do not accept that as closure.

**4. The old critique wanted narrower SCLK exception handling; the new one defends two broad
catches.** The old import critique (§2, High) asked for `except ValueError` in place of
`except Exception` around SCLK parsing. The tree consolidated 18 sites into one helper but kept
`except Exception` (`obs_base.py:941`). The 2026-09-01 reviewer does not raise it, and separately
argues that two *other* broad catches (`do_import_obs.py:457` around a field method, `cli.py:691` as
the sanctioned top-level handler) are correct and should not be narrowed — the opposite emphasis. The
one broad catch the new reviewer does object to is a different pair (`obs_base.py:863`, `:900`, where
a `TypeError` from an unhashable masked column is misreported as a bad time format).

Two smaller mechanical divergences, noted and set aside: the old JavaScript critique's per-file line
counts are each one higher than a `wc -l` of the byte-identical files gives, a line-counting
convention difference; and the old import critique's `import_observation_table` figure (270 lines,
"lines 1178-1448") counts a span the split has since redistributed, so the 270 → 350 comparison is
between the function then and the function now, not between two identical measurements.

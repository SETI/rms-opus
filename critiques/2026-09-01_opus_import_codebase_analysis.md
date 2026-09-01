# Codebase analysis: rms-opus import side (`opus_import`, `opus_support`, `opus_config`)

**Date:** 2026-09-01
**Tree analyzed:** `2bfc2a0e57d4ccb1465775e8e32a7f564d1f2bb1` (branch `pr-24-merge-to-main`), verified with
`git rev-parse HEAD`.
**Scope:** `src/opus_import/` (21,525 lines), `src/opus_support/` (2,531), `src/opus_config/` (738)
— 100 Python modules — plus `tests/opus_import/`, `tests/opus_support/`, `tests/opus_config/` and
`import_tests/` as context on the packages' quality.
**Out of scope, not assessed:** `src/opus_app/`, `src/opus_log_analyzer/`, `integration_tests/`,
the JavaScript/CSS front end.
**Standards applied:** the repository's own `.cursor/rules/*.mdc`, cited by filename. The rule set
ships no `logging.mdc` or `filecache.mdc`, so per the analysis skill those two dimensions are
skipped rather than invented.
**Method:** every finding below was verified by reading the cited source. Numbers come from a
command, named where it is not obvious; nothing is estimated.

---

## Summary

This is a well-run codebase. Every automated gate the project sets for itself passes on this tree:
`ruff check` and `ruff format --check` are clean over all 100 modules, `bandit` reports zero
findings, `vulture` is clean, and `mypy --strict` over `src tests import_tests` (226 source files)
produces **no error of any kind except one repeated `import-untyped` for `pdsfile`**. Every one of
the 1,604 functions in scope carries complete parameter and return annotations, and every module
and every class carries a docstring. The SQL layer validates every identifier against
`\A[A-Za-z0-9_]+\Z` before backtick-quoting it and binds every value as a `%s` parameter; I could
not construct an injection path through it. `opus_config` and `opus_support` are at **100%
statement and branch coverage**, measured.

Three things are worth acting on. First, the declared dependency on `rms-pdsfile>=0.0.18` is not
what CI tests and does not typecheck: every CI job replaces it with an unpinned git branch tip, no
PyPI release of that package ships `py.typed`, and a docstring in `obs_base.py` asserts as fact that
it does. Second, the two functions that perform the actual import — `import_one_index` (612 lines)
and `import_observation_table` (350 lines) — are by a wide margin the largest and most deeply
nested code in the tree and are the least covered by the fast test tier (3% and 6%); the pipeline's
real coverage lives in a suite that needs a MySQL server, so a developer running the documented
default gets almost no feedback on the code most likely to break. Third, a `# flake8: noqa` on
`config_bundle_info.py:11` is a whole-file lint exemption that `ruff` honors, in a project whose
`pyproject.toml` states in prose that no per-file exception exists.

Below that tier the findings are ordinary and mostly small: some duplication that should be pulled
up a class, optional parameters that are not keyword-only, message-less exceptions on
`opus_support`'s public parsers, and one pocket of dead machinery.

A recurring pattern is worth naming, because it is unusual and it is mostly to the tree's credit:
this codebase writes down what it knows. Comments and docstrings routinely explain *why* — why table
names are sorted, why the row alias puts a floor on the MySQL version, why `numpy.int64` needs
converting and `numpy.float64` does not, why a dependency floor is where it is, why a warning
suppression that suppresses nothing would be a false claim. Several of my findings are cases where
the tree has honestly documented a problem instead of fixing it: the unreachable preprocessing
branch, the message-less exceptions, the order dependence in the golden suite. Documented is much
better than hidden, and it made this review far easier — but a comment describing a defect does not
retire it.

---

## 1. Structure and layout

- **Finding (Medium): Two modules exceed the hard 1,000-line limit.** `python.mdc` §2: *"ALWAYS keep
  modules under 1000 lines. Split larger modules into a package with multiple files."*
  **Evidence:** `src/opus_support/units.py` (1,176 lines) and
  `src/opus_import/importdb/mysql.py` (1,191 lines); measured with `wc -l`, and they are the only
  two in scope over the limit. **Suggestion:** `units.py` splits along a seam that already exists —
  lines 115–600 are the `UNIT_FORMAT_DB` literal (486 lines, 41% of the file) and lines 612–1176
  are the logic that reads it. Moving the table to `opus_support/_unit_db.py` puts both halves
  comfortably under the limit with no behavior change. `mysql.py` splits less naturally; the DDL
  rendering (`create_table`, `table_info`) is the obvious candidate.

- **Finding (High): The two functions that do the importing are the least tractable code in the
  tree.** **Evidence:** measured by AST over the scope —
  `src/opus_import/steps/do_import_index.py:45` `import_one_index` is **612 lines** at nesting depth
  8; `src/opus_import/steps/do_import_obs.py:42` `import_observation_table` is **350 lines** at depth
  8. For context, 17 of the 1,604 functions in scope exceed 100 lines, so these are extreme
  outliers, not the norm. A representative slice: `do_import_index.py:239` sits seven indent levels
  deep inside `import_one_index`, parsing an inventory CSV inline. **Suggestion:** `import_one_index`
  has visible seams — duplicate-row resolution (lines 102–160), associated-metadata discovery
  (lines 201–300), per-row observation import — each of which is a nameable function taking the
  bundle context. This matters more than usual because the fast test tier barely reaches them (see
  §4).

- **Finding (Medium): A pocket of dead machinery spans two modules.**
  **Evidence:** `src/opus_import/import_util.py:424-425` sets `preprocess_label_func = None` and
  `preprocess_table_func = None`; the loop that would assign them is commented out at lines 426–430.
  Consequently `if preprocess_label_func is None:` at line 438 is always true and the `else` branch
  at lines 442–450 is unreachable. That branch holds the module's only use of `pdsparser`
  (imported at line 37) — confirmed with `grep -rn "pdsparser" src/`, which finds it elsewhere only
  in the unrelated `util/dump_pds_definitions.py`. The commented-out loop's data source,
  `instruments.PDSTABLE_PREPROCESS` (`src/opus_import/instruments.py:17`), is an empty list
  referenced from nothing but its own definition and that comment. `instruments.py`'s own docstring
  is candid about this. **Suggestion:** delete `PDSTABLE_PREPROCESS`, the commented-out loop, the
  unreachable `else`, and the `pdsparser` import; keep `PDSTABLE_REPLACEMENTS`, which is live
  (consumed at `import_util.py:433`). `python.mdc` §2 forbids carrying code for a future that has
  not arrived.

- **Finding (Low): `retrieve_ra_dec.py` carries 24 lines of commented-out code and two dead module
  globals.** **Evidence:** `src/opus_import/util/retrieve_ra_dec.py:229-252` is a commented-out
  block; `simbad_pat` (line 189) and `name_pat` (line 190) are compiled and referenced *only* from
  inside that block. **Suggestion:** delete all three.

- **Finding (Low): Two more commented-out import lines, in a module at 0% coverage.**
  **Evidence:** `src/opus_import/importdb/postgresql.py:13-14` are `# import csv` and
  `# import psycopg2 as pg`; the module measures 0% (6 statements, 6 missed) in the unit run, and
  `importdb/__init__.py:24,81-86` carries the matching commented-out import and dispatch branch.
  The stub itself is legitimate and its docstring is admirably direct about being unimplemented —
  it is only the commented-out code around it that should go.

- **Finding (Low): 22 lines of module documentation are written twice.** **Evidence:**
  `src/opus_import/config_bundle_info.py:44-65` is a block comment describing the `BundleInfo` keys;
  `config_bundle_info.py:68-85` is the `BundleInfo` TypedDict docstring describing the same keys,
  in different words. **Suggestion:** delete the comment; the docstring is the copy Sphinx renders.

- **Strength.** The package boundaries are clean and enforced by construction.
  `src/opus_import/__init__.py` deliberately imports nothing, and says why ("an empty package root
  keeps that graph free of import cycles"); `opus_config` exists as its own tiny package precisely
  so that `opus_import` and `opus_app` can both read configuration without importing each other.
  `opus_support/__init__.py` re-exports its entire public surface with a sorted `__all__` of 54
  names, so both consumers import from one place. All five packages ship `py.typed`.

- **Strength.** Naming discipline is near-total. An AST scan for module-level assignments that are
  neither `ALL_CAPS`, `_private`, nor TitleCase type aliases returns exactly **three** names across
  100 files — `radec_pat`, `simbad_pat`, `name_pat` in `retrieve_ra_dec.py:185,189,190` — which
  should be `ALL_CAPS` per `python.mdc` §1 (and two of which are dead, above). Nothing else in scope
  deviates.

---

## 2. Best practices alignment

- **Finding (Medium): Optional and configuration parameters are not keyword-only anywhere in
  `opus_import`.** `python.mdc` §2: *"Optional and configuration parameters MUST be keyword-only
  (after `*`)."* **Evidence:** an AST scan of the scope finds **68 of 1,604** functions with a
  defaulted positional-or-keyword parameter and no `*` separator. The worst are on the pipeline's
  main seams: `src/opus_import/obs/obs_base.py:745` `_create_mult(col_val, disp_name, disp,
  disp_order, grouping, group_disp_order, tooltip, aliases)` — seven optional parameters, all
  positionally passable; `src/opus_import/importdb/__init__.py:31` `get_db(...)`, which additionally
  takes six *required* positionals before them (the same rule says that a leading group larger than
  about five should make everything keyword-only), mirrored at
  `src/opus_import/importdb/mysql.py:65` and `super.py:85`; and
  `src/opus_import/steps/do_import_mult.py:200` `update_mult_table(..., aliases, disp, disp_order,
  grouping, group_disp_order)`. **Suggestion:** insert `*` before the optional group. This is
  mechanical and mypy will find every call site that needs updating. Note the contrast:
  `opus_config/config.py` gets this right throughout — `read_str(self, key, *, default=_REQUIRED)`
  at line 293 and every sibling reader.

- **Finding (Medium): `opus_support`'s public parsers raise exceptions with no message at all.**
  The analysis skill's dimension 2 asks for *"exceptions [that] include enough context to
  diagnose"*; `security.mdc` §3 asks for *"clear `ValueError` or `TypeError` exceptions for invalid
  arguments"*. **Evidence:** `grep -rnE "raise (ValueError|KeyError|...)\s*$"` over the scope returns
  12 context-free raises, 11 of them in `opus_support`:
  `units.py:635,648,675,688,1085`, `angles.py:187,199,201,216,218,234`, `time_parsing.py:86`.
  Two are worse than bare: `angles.py:212` and `angles.py:232` catch a `float()` `ValueError` whose
  message names the offending text and deliberately re-raise an empty one
  (`raise ValueError from err`). These are not internal helpers — `parse_dms`, `parse_hms`,
  `parse_time`, `parse_unit_value` and `convert_to_default_unit` are all in `opus_support.__all__`,
  and `src/opus_app/apps/search/views.py:771,775,788` calls them on user-typed search input.
  `units.py:635` also uses `KeyError` to report an argument-combination error, where `ValueError` is
  the right class. **Suggestion:** give each raise a message naming the value and the constraint.
  The docstring at `angles.py:136-142` defends the empty message as *"one rejection contract"* so
  callers "never have to tell them apart" — but a uniform contract and an informative message are
  orthogonal: `raise ValueError(f'not a valid angle: {s!r}')` is still exactly one contract. The
  rest of the repository already knows how to do this — `opus_config`'s messages name the file, the
  table and the key (`config.py:251`), and `time_parsing.py:58,73,75,84` writes
  `f'Invalid time syntax: {iso}'` at four of its five raise sites. It is only the fifth, the
  out-of-range case at line 86, that is bare — which is the one an ordinary user is most likely to
  hit by typing a year-3000 date.

- **Finding (Low): A public parser validates its argument with `assert`.** **Evidence:**
  `src/opus_support/sclk.py:391` `assert planet in (None, 5, 6, 7, 8), f'Invalid planet value:
  {planet}'` inside `parse_voyager_sclk`, which is exported in `opus_support.__all__`; same shape at
  `sclk.py:485-486` in `format_voyager_sclk`. `python -O` removes all three, taking the validation
  with them — and `pyproject.toml:483-491` already flags that exposure when it skips bandit's B101
  (*"if that ever changes, these become real checks and this skip has to be revisited"*). Every
  other rejection in this module raises `ValueError`. There is a neat inversion here worth noticing:
  these three `assert`s carry **good** messages naming the offending value, while the `ValueError`s
  a few functions away carry none at all (above). **Suggestion:** raise `ValueError` with the
  message these asserts already write.

- **Finding (Medium): Two `open()` calls omit `encoding=`.** **Evidence:**
  `src/opus_import/import_util.py:376` `with open(filename) as csvfile:` (a PDS4 index CSV) and
  `src/opus_import/steps/do_import_index.py:239` `with open(table_filename) as table_file:` (a PDS3
  inventory CSV). These are the *only* two unqualified `open()` calls in the scope — every other
  read is explicit (`import_util.py:665` and `do_param_info.py:60` pass `encoding='utf-8'`;
  `do_dictionary.py:139` and `config.py:636` use `Path.open` with an explicit mode or encoding).
  **Suggestion:** add the encoding these PDS files actually use. The current behavior depends on the
  process locale, so the same holdings decode differently on two machines: a non-UTF-8 byte raises
  `UnicodeDecodeError` under a UTF-8 locale and is silently mis-decoded under a Latin-1 one.

- **Finding (Medium): Truthiness is used where `is not None` is meant, including on a `DELETE`.**
  `python.mdc` §1 requires explicit checks *"when the intent could be ambiguous"*.
  **Evidence:** `src/opus_import/importdb/mysql.py:1077` `if where:` decides whether a
  `DELETE FROM <table>` gets a `WHERE` clause — a caller passing `where=''` deletes every row in the
  table; same shape at `mysql.py:1126` for `copy_rows_between_namespaces`.
  `src/opus_import/importdb/super.py:248` `if cur:` decides whether to reuse the caller's cursor or
  open a new one and commit; DB-API cursors are not guaranteed to be truthy, and an implementation
  that defines `__len__` would silently take the wrong branch. `importdb/__init__.py:87` `if logger:`
  and the ~30 `if self.logger:` in `mysql.py` are the same pattern on an object.
  I confirmed the `DELETE` case is not live today — all four call sites
  (`do_import_tables.py:101,105,160,164`) pass a non-empty literal built by `quote_identifier` — so
  this is latent risk, not a present bug. **Suggestion:** `if where is not None:`,
  `if cur is not None:`, `if self.logger is not None:`.

- **Finding (Medium): Bundle-descriptor expansion is a data table written as control flow.**
  **Evidence:** `src/opus_import/import_util.py:164-257` is a 94-line `if/elif` chain in which each
  shorthand appends a hard-coded list of bundleset names; `python.mdc` §2 says *"NEVER hardcode
  magic constants. Define them as module-level constants"* and *"ALWAYS apply DRY"*. `COISS_1xxx`
  alone appears three times (lines 165, 194, 206), and `desc.upper()` is recomputed on every branch
  test. Two of the lists were already lifted out as `_NHXXLO_BUNDLES` and `_NHXXMV_BUNDLES`
  (lines 111–129), which is the pattern the rest should follow. **Suggestion:** one module-level
  `BUNDLE_DESC_EXPANSIONS: dict[str, tuple[str, ...]]` and a single `.get()`; this replaces 94
  lines with about 30 of data and 3 of code, and makes the ALL/CASSINI overlap visible.

- **Finding (Medium): `sys.exit()` in library code.** The skill's dimension 2: *"No `sys.exit()` in
  library code; raise exceptions instead."* **Evidence:** `src/opus_import/import_util.py:294`
  calls `sys.exit(-1)` from inside the generator `yield_import_bundle_ids`. The other four exits
  (`cli.py:542,600,625,696`) are in `main()` and are correct there. The docstring does honestly
  declare `Raises: SystemExit`, so this is documented rather than hidden. **Suggestion:** raise a
  pipeline exception and let `cli.main` translate it, which also lets a caller test the validation
  without trapping `SystemExit`. Separately, `sys.exit(-1)` reaches the shell as status 255; if a
  specific status is meant, say `1`.

- **Finding (Low): Broad `except Exception` on paths where a narrower catch would surface real
  bugs.** `python.mdc` §2: *"ALWAYS catch exceptions at the smallest granularity possible."*
  **Evidence:** `src/opus_import/obs/obs_base.py:863` and `:900` wrap
  `import_util.cached_tai_from_iso(the_time)` and report any failure as
  `f'Bad {column} format "{the_time}"'`. That function is `@lru_cache`-decorated
  (`import_util.py:911`), so a masked column arriving as an unhashable list raises
  `TypeError: unhashable type` and is reported as a bad *time format* — a misdiagnosis of a
  different fault. **Suggestion:** catch `(ValueError, TypeError)` explicitly, or better, the
  julian exception type. Note that two other broad catches are correct and I would not change them:
  `do_import_obs.py:457` around a field method is deliberate and explained
  (`obs_base.py:58-62` says a field method's exception must be a bad field rather than an aborted
  import), and `cli.py:691` is the sanctioned application-level top handler `python.mdc` §2 asks
  for, with a comment saying why it catches `Exception` rather than `BaseException`.

- **Strength.** `print()` is confined exactly where the rules allow it. The only two modules using
  it — `util/dump_pds_definitions.py` and `util/retrieve_ra_dec.py` — are documented developer
  tools with `if __name__ == '__main__':` guards (lines 53 and 261) and `util/__init__.py` says so.
  Everything else logs through `ImportLog`, which prefixes every message with the bundle, index row
  and filespec being processed, and deduplicates messages that would otherwise repeat hundreds of
  thousands of times.

- **Strength.** `python.mdc` §2's `getattr` rule is respected. The one dynamic `getattr` in the
  pipeline (`do_import_obs.py:448`) is genuine dispatch on a method name computed from the table
  schema, not defensive access — and `field_function_name` (line 395) is documented as *"the
  pipeline's only rule for finding a field method"*, with a test that resolves the hierarchy through
  that function rather than restating the rule.

---

## 3. Types and static checks

- **Finding (High): The declared `rms-pdsfile` dependency does not typecheck, and a docstring says
  otherwise.** **Evidence, all measured:**
  - `pyproject.toml:31` declares `rms-pdsfile>=0.0.18`, and `[[tool.mypy.overrides]]`
    (`pyproject.toml:343-346`) lists `julian`, `pdfkit`, `pdslogger`, `pdsparser`, `pdstable` and
    `rest_framework` — **not** `pdsfile`.
  - `OPUS_CONFIG=... mypy src tests import_tests` on this tree reports **20 errors in 14 files, all
    of them `import-untyped` for `pdsfile`** (8 of them in `src/opus_import/`). There is no other
    mypy error of any kind.
  - The installed `rms-pdsfile` is 0.0.18 — exactly the declared floor — and has no `py.typed`.
    I downloaded the current release, 0.1.2, and inspected the wheel: **also no `py.typed`.** No
    published release satisfies the docstring's claim.
  - Every CI job replaces the declared dependency: `.github/workflows/run-tests.yml:102,196,296,377`
    and `run-integration.yml:141` each run
    `pip install "rms-pdsfile @ git+https://github.com/SETI/rms-pdsfile@rewrite"` — an unpinned
    branch tip — *after* `pip install -e ".[dev]"` and before `mypy` runs at line 138.
  - `src/opus_import/obs/obs_base.py:183-185` states as fact: *"``pdsfile`` ships ``py.typed``, so
    it carries no ``ignore_missing_imports`` entry and every call on the returned object is
    type-checked."*

  **Impact:** the type gate passes only against an unreleased branch. Anyone who installs the
  distribution as declared gets a `pdsfile` that CI has never tested, and running the project's own
  `scripts/run-all-checks.sh` against the declared dependency set fails. This is the exact failure
  mode `pyproject.toml` already guards against elsewhere and explains at length — the `types-requests`
  comment (lines 97–101) says the stubs exist *"so [that] the type gate [is] independent of which
  requests a resolve happens to pick."* **Suggestion:** either floor `rms-pdsfile` at the first
  release that ships `py.typed` (and pin CI to it rather than a branch), or add a `pdsfile.*` entry
  to `[[tool.mypy.overrides]]` with the reason, and correct the `obs_base.py` docstring either way.

- **Finding (Medium): 1,186 functions have no docstring, all of one kind.** `python.mdc` §6:
  *"ALWAYS include a docstring for every module, class, function, and method."* **Evidence:** an AST
  scan over the scope: modules **100/100** documented, classes **75/75**, functions **418/1,604**
  (26.1%). Broken down, **every one** of the 1,186 undocumented functions is a `field_*` method under
  `src/opus_import/obs/`; the count of non-`field_*` functions without a docstring is **zero**. So
  this is one uniform decision, not scattered neglect — and it is defensible in part, since each
  method computes one schema-defined column and `field_types.py` documents the annotation rule that
  binds method to schema. But the docs render them: `docs/_ext/opus_api_reference.py:145-147` emits
  `automodule` with both `:members:` and `:undoc-members:`, and `opus_import.obs` is not in
  `EXCLUDED_MODULES` (lines 68–76) — which excludes `opus_app.apps.search.models` for the stated
  reason that its generated classes are *"none docstringed."* The published reference therefore
  carries 1,186 bare signatures. **Suggestion:** either exclude the leaf obs modules from the
  reference with that same rationale, or docstring the field methods whose logic is not obvious
  from the name (the wavelength and geometry computations, not the one-line accessors).

- **Finding (Low): `Any` concentrates at three genuine boundaries, but two uses are avoidable.**
  **Evidence:** 54 `: Any` / `-> Any` occurrences in scope, mostly honest — PDS index rows
  (`IndexRow = dict[str, Any]`), DB rows, and the DB-API connection, each of which really is
  untyped. Two are not boundary-forced: `obs_base.py:957,966,976` declare `_log_warning`,
  `_log_nonrepeating_warning` and `_log_nonrepeating_error` as `(*args: Any, **kwargs: Any) -> None`
  passthroughs, but their targets take exactly one `str`
  (`context.py:107` `nonrepeating_error(self, msg: str)`), so `**kwargs` can only ever produce a
  runtime `TypeError`. These are the most-called methods in the obs hierarchy and mypy checks none
  of their call sites. **Suggestion:** `(self, msg: str) -> None`.

- **Finding (Low): Regex group indices are coupled across two patterns by padding.**
  **Evidence:** `src/opus_support/angles.py:163-176` reads `match[1]`, `match[2]`, `match[6]`,
  `match[8]` from either of two alternative patterns; the second (line 171) contains `()()()` and
  `()` — five empty groups whose only purpose is to make the indices line up with the first
  pattern's. Nothing says so. **Suggestion:** named groups (`(?P<deg>...)`) remove the padding and
  the coupling together.

- **Strength.** **All 1,604 functions in scope carry complete parameter and return annotations**
  (measured by AST; zero unannotated). `mypy strict = true` with no `ignore_errors` list anywhere,
  and `pyproject.toml:348-359` states that claim in a form that can be checked and points at the two
  lists that *do* suppress. `ruff check` and `ruff format --check` pass over all 100 modules, and
  only **4 lines** in 21,525 exceed the 100-character limit (`do_import.py:271` and three copies of
  the same `# nosec` comment in `mysql.py`).

- **Strength.** `src/opus_import/obs/field_types.py` is the best-reasoned module in the tree. It
  explains why the *form* type and not the storage type decides a field method's annotation, why
  `numpy.int64` needs `as_int` while `numpy.float64` and `numpy.str_` do not (they subclass `float`
  and `str`; `numpy.integer` does not subclass `int`), and why `as_int` raises rather than truncates
  — *"Truncating instead would store a value the source never held and pass every check
  downstream"* (lines 77–86). It deliberately does **not** restate the alias-selection rule, which
  lives once in `tests/opus_import/test_obs_field_annotations.py`, because *"two copies of a
  decision table drift, and these two had already begun to."*

---

## 4. Testing

*(Assessed against `python_testing.mdc`. Coverage figures are my own measurements on this tree. A
second reviewer covered the suites in depth; every claim reproduced below I re-read in the source
before keeping, and I note where I graded a finding differently.)*

- **Finding (High): The fast, hermetic tier reaches under half of the pipeline, and almost none of
  its two largest functions.** **Evidence:** the default suite with coverage
  (`pytest --cov` under `PYTHONPATH=<worktree>/src`) gives **40%** for `opus_import` (8,084
  statements, 4,316 missed). The step modules are the gap: `do_import_index.py` **3%**,
  `do_import.py` **4%**, `do_validate.py` **4%**, `do_import_obs.py` **6%**, `do_import_tables.py`
  **7%**, `do_param_info.py` and `do_partables.py` **10%**, `importdb/mysql.py` **21%**. The 612-
  and 350-line functions from §1 sit in the first and fourth. `python_testing.mdc` §9 asks for 90%
  *"measured over the ENTIRE suite"*; `pyproject.toml:288` sets the floor at 75, which the Import
  Tests job reaches — so the shortfall against the rule is 15 points and it is entirely in
  `opus_import`. **Impact:** a developer without MySQL — running what `CLAUDE.md` calls *"the
  default run"* — gets almost no feedback on the code most likely to break. **Suggestion:** the
  mini-holdings suite is the right long-term answer, but a few pure-function extractions out of
  `import_one_index` (duplicate-row resolution, the inventory-CSV reader) would be unit-testable
  without a database and would move the number where it matters. Note the floor is *honestly*
  derived — `pyproject.toml:276-287` says it is *"the run's own figure rounded down, not an
  aspiration"* and gives the command that regenerates it.

- **Finding (High): `import_tests/test_goldens.py` depends on its own collection order.**
  `python_testing.mdc` §2: *"no reliance on execution order … no dependence on artifacts another
  test produced."* **Evidence:** the session-scoped `reimport` fixture
  (`import_tests/test_goldens.py:293`) re-imports a fixture volume into the same database every
  golden comparison in the module reads, and its docstring states the dependence rather than
  removing it (lines 304–306): *"It mutates the finished database, so it is deliberately the last
  thing this module does: the golden comparisons above are defined before it and run before it."*
  This holds only because pytest collects in definition order and the module runs serially; any
  reordering plugin, or running `test_table_matches_its_golden` by name after `reimport` in one
  session, breaks it. **Suggestion:** import into a second schema. The suite already builds three
  schemas for the negative cases via `fixture_layout.schema_name(pid, case)`, so the machinery
  exists; the cost is one extra import run and the ordering constraint disappears.

- **Finding (Medium): Ten assertions pin a message-less exception as the contract.** **Evidence:**
  `grep -rn "str(excinfo.value) == ''"` returns 10 hits — `test_angles.py:168,193,217,224,290`,
  `test_units.py:51,95,397,410`, `test_time_parsing.py:116` — each with a docstring of the form
  *"The empty message is asserted rather than glossed over because it is the module's current
  contract; giving it text would be a behavior change"* (`test_units.py:44-48`). **This is the right
  way to test a contract you have decided to keep**, and I want to be clear that the tests are
  honest: they assert the emptiness rather than faking a message match. The problem is the
  underlying decision (§2), and the stated reason for it does not survive contact with the
  project's own rules — `python.mdc` §2 says *"NEVER include backwards-compatibility code"*,
  `CLAUDE.md` scopes the compatibility waiver to *"the public API only"* meaning the web API, and
  `opus_support/__init__.py:7-8` says the package *"carries no API stability guarantees for outside
  users."* By those three, the messages are free to improve and these ten assertions with them.

- **Finding (Medium): The `config_targets` tables are validated only in the MySQL tier, though the
  validation needs no database.** **Evidence:** the five semantic checks on those tables —
  `test_target_name_round_trips_through_its_encoding`,
  `test_every_target_names_a_planet_group_that_exists`,
  `test_every_mapped_spelling_resolves_to_a_known_target`,
  `test_every_target_class_is_a_value_the_general_table_accepts`,
  `test_surface_geometry_table_name_is_a_safe_identifier` — are at
  `import_tests/test_unit_layers.py:43-127`, and I confirmed they take no database fixture and
  import only `config_targets` and `import_util`. The module docstring concedes it at line 3:
  *"The first two need no database."* Because `testpaths = ["tests"]`, they never run in the default
  suite or the GitHub-hosted unit job. (The modules themselves show 100% statement coverage, but
  only because they are dict literals that executing the import runs end to end — statement
  coverage says nothing about them.) **Suggestion:** move those five to `tests/opus_import/`, where
  they cost nothing and run on every commit.

- **Finding (Medium): The obs-values golden can be regenerated with no clean-run gate, into the
  repository.** **Evidence:** `tests/opus_import/test_obs_field_annotations.py:993-997` — under
  `--regenerate-obs-values`, `_VALUES_FIXTURE.write_text(...)` overwrites a 138 KB checked-in JSON
  with whatever the code currently produces, then `pytest.skip`s. `python_testing.mdc` §5 says
  `tmp_path` and *"never write into the repo."* Contrast the end-to-end suite's regenerator,
  which is the model: `import_tests/tools/make_mini_goldens.py` is a separate program (unreachable
  from a pytest run) whose `check_run_is_clean` (line 70) verifies every step's exit status, that
  both logs were written, that `ERRORS.log` is empty, that every warning is whitelisted with no
  stale entries, and that expected-products passes — *before* writing anything, printing
  `Refusing to write goldens...` otherwise (lines 180–189). **Suggestion:** gate the in-pytest
  regenerator the same way; the sibling tests in that file already compute the `raised` and `wrong`
  sets it would need.

- **Finding (Medium): Four float comparisons use `==` where the same files define a tolerance.**
  `python_testing.mdc` §7 requires `pytest.approx` or an explicit tolerance. **Evidence:**
  `test_sclk.py:231`, `test_sclk.py:419`, `test_angles.py:92`, `test_units.py:416`. The first is
  the sharpest: it compares `parse_new_horizons_sclk('3/9999999999:49999')` against the literal
  `9999999999.99998` (case at line 224) — ten significant figures before the point and five after,
  passing only because the parser's sum happens to round to the same double. `SCLK_ABS_TOL` is
  defined in that very file (lines 25–29, with an excellent rationale about why `approx`'s relative
  default is wrong for TAI magnitudes) and used at lines 129 and 393. **Suggestion:** use it at
  these four sites too; the knowledge is already there.

- **Finding (Medium): Five database doubles across four files, none in `conftest.py`.**
  `python_testing.mdc` §8: *"keep a minimal fake defined once in `conftest.py`."* **Evidence:**
  `test_do_dictionary.py:21` `_FakeDatabase`, `test_do_update_mult_info.py:25` `_RecordingDatabase`,
  `test_import_context.py:345` `_FakeDatabase` (defined *inside* a test function),
  `test_importdb_mysql.py:28` `_RecordingDB` and `:339` `_FailingDB`. The package already has the
  right home — `tests/opus_import/conftest.py:14-70` correctly holds `RecordingLogger`,
  `make_context` and `default_arguments`. **Suggestion:** one parameterizable recording double
  beside them.

- **Finding (Medium): `test_obs_field_annotations.py` is 1,384 lines covering five concerns.**
  `python.mdc` §2's 1,000-line limit applies to tests too (`python_testing.mdc` preamble: *"Tests
  are first-class code"*), and §3 asks for *"one focused area of behavior per file."* **Evidence:**
  the file holds a schema/annotation cross-check, a driven-value type check, a JSON golden
  comparison (line 971), a numpy-coercion runtime check (line 1085), an AST sweep (line 1331), and
  460 lines of literal fixture data (`_GEOMETRY_COLUMNS` 348–492, `_MISSION_FIXTURES` 533–757).
  **Suggestion:** the fixture tables are the natural first split.

- **Finding (Low): Three of 43 `pytest.raises` assert no message.** **Evidence:**
  `test_importdb_mysql.py:263` (the SQL-injection guard, parametrized over 7 hostile identifiers —
  a `match=` would distinguish "rejected the backtick" from "rejected for some other reason"),
  `test_obs_field_annotations.py:1183`, `test_config.py:169`. The 40 that do assert are the norm,
  and some are exemplary — `test_orbits.py:14-21` defines an `_exactly()` anchoring helper because
  *"`match` searches rather than fullmatches, so an unanchored pattern for 'Invalid Cassini orbit 1'
  would also accept 'Invalid Cassini orbit 10'."*

- **Finding (Low): An exact-count source test makes dead code undeletable.** **Evidence:**
  `tests/opus_import/test_do_import_index.py:87-127` asserts `len(guards) == 4` against the AST of
  `do_import_index.py`, and its own docstring (lines 94–99) says one of those four guards is
  unreachable. Deleting genuinely dead code therefore fails a test. I grade this Low rather than
  Medium — the reviewer's severity — because the exact count is what makes "a fifth guard was added
  and got its key wrong" detectable, which is the defect the test exists for. **Suggestion:** assert
  the property (every guard initializes the key it tested) without pinning the count.

- **Finding (Low): A mutable `ImportContext` is `@functools.cache`d across tests.** **Evidence:**
  `import_tests/test_unit_layers.py:130-139`, used at lines 183 and 197. `ImportContext` carries
  mutable per-run state (`import_has_bad_data`, `logged_import_errors`, `mult_table_cache`). No
  current test asserts on that state, so nothing fails today. The stated reason — a
  `pdslogger.PdsLogger` name can be created once per process — argues for a module-scoped fixture
  rather than a module-level cache.

- **Strength (verified independently).** `opus_support` and `opus_config` are at **100% statement
  and branch coverage**: `coverage report --include="*/opus_support/*,*/opus_config/*"` gives 766
  statements, 306 branches, **0 missed** across all nine modules. The claim in
  `opus_support/__init__.py:11-12` is true.

- **Strength.** Several categories the rules police are *clean*, which is worth stating as a result
  rather than a silence. Measured over the scoped suites: **zero** tests that execute a path without
  asserting (the 24 `test_*` functions with no `assert` statement are all `pytest.raises` context
  managers); **zero** assertions joining two conditions with `and`; **zero** direct `os.environ`
  mutation (36 uses of `monkeypatch.setenv`/`delenv`/`setattr` instead); **zero** missing type
  annotations; **zero** missing docstrings anywhere in `import_tests/`. The process-global
  `get_config` cache is cleared on both sides by an autouse fixture (`tests/conftest.py:14-23`),
  which is exactly `python_testing.mdc` §5's prescription. CI runs the unit tier
  `-n auto --dist loadscope` (`run-tests.yml:201`) and it passes — real evidence of
  order-independence rather than a claim.

- **Strength.** The end-to-end golden suite is the best-engineered part of the testing.
  Comparison is byte-exact TSV (`test_goldens.py:289`), not fuzzy. The three normalizations are
  each defended at their definition and one of them (`golden_io.py:311`) reads *which* columns to
  drop from `information_schema` at run time rather than hard-coding a list. The one column dropped
  for size is not lost coverage — `test_goldens.py:238-260` re-derives it in SQL and asserts every
  row matches, and `test_no_derivation_rebuilds_a_column_from_itself` (line 222) blocks the obvious
  cheat with a worked example of it in the docstring. `EXCLUDED_TABLES` is **empty**
  (`golden_io.py:87`), `test_goldens.py:137` asserts `sorted(GOLDENED_TABLES) == sorted(run_tables)`
  so no table can escape comparison, and an excused table would have to both exist and hold rows
  (line 151). Beyond that, `import_tests/test_obs_execution.py` enforces a gate the rules do not
  even ask for: every function under `src/opus_import/obs/` must have executed or be whitelisted
  with a written reason, with three tests that fail if an entry goes stale.

- **Note found while reading the source, not the tests.** The only unit harness for the MySQL
  backend (`tests/opus_import/test_importdb_mysql.py:28-35`) constructs the class with
  `logger=None` — exactly the configuration that triggers the `create_table` cache defect in §7 —
  but never calls `create_table`, so that defect is untested.

---

## 5. Performance and resource use

- **Finding (Low): `opus_support` pulls in numpy for two scalar calls that `math` already covers.**
  **Evidence:** `src/opus_support/units.py` imports numpy at line 14 and uses it exactly twice —
  `DEG_RAD = np.degrees(1)` (line 45) and `int(np.ceil(np.log10(...)))` (line 927). `math` is
  already imported at line 10 and provides both. `opus_support` is on the web application's request
  path (`src/opus_app/apps/search/views.py:71-76`), so this is import-time cost paid by every worker
  process. **Suggestion:** `math.degrees(1)` and `math.ceil(math.log10(...))`. (`angles.py:333` uses
  `np.round`, which I am not proposing to change — numpy is a hard dependency of the distribution
  regardless, so this is tidiness rather than a dependency removal.)

- **Finding (Low): Per-row work in the insert hot path.** **Evidence:**
  `src/opus_import/importdb/mysql.py:825` recomputes `sorted(rows[0].keys())` inside the
  packet loop rather than once, and line 830 sorts *every* row's keys for an equality assertion on
  the insert path — `O(n·k log k)` over the millions of rows an import writes.
  **Suggestion:** hoist the first out of the loop; the second is a real invariant check, but
  comparing `row.keys() == first_keys` (dict views compare as sets) is the same check without the
  sort.

- **Finding (Low): Exception-driven type inference allocates the column three times.**
  **Evidence:** `src/opus_import/import_util.py:388-405` tries `[int(x) for x in col_data]`, then
  `[float(x) for x in col_data]`, discards both (`_ = ...`), and finally re-converts the column into
  the rows. `python.mdc` §1 also asks for *"explicit membership or presence checks over catching
  exceptions for control flow."* **Suggestion:** convert once and keep the result.

- **Strength.** Caching is deliberate and each instance is documented where it lives:
  `import_util.py:911` `@lru_cache(maxsize=64)` on the ISO→TAI conversion, with the reason (*"An
  index row's times repeat across the rows of one observation"*); `ObsBase.opus_id`
  (`obs_base.py:246-274`) re-derives whenever the filespec changes and the comment explains why the
  `None` check must precede the cache hit; `mysql.py:114` caches `table_info` per table and clears
  it on every create and drop. `import_util.py:16-18` states which state deliberately outlives a
  call. There is no threading or multiprocessing anywhere in the scope (`grep` for
  `threading|multiprocessing|concurrent.futures` returns nothing), so the module-level mutable state
  the skill asks about — `NoDupLogger`'s class-level sets at `import_util.py:722-725` — is safe as
  written, and it says so.

- **Strength.** `ImportDBMySQL.table_names` returns sorted names and the comment
  (`mysql.py:370-378`) explains that this is a correctness requirement, not tidiness: the cache is a
  set, and a caller handing out row ids in iteration order *"would otherwise give the same database
  different ids on different machines."* That is exactly the kind of non-obvious rationale
  `python.mdc` §4 asks comments to carry.

---

## 6. Maintainability and extensibility

- **Finding (Medium): Duplication that should be pulled up a class.** `python.mdc` §2: *"ALWAYS
  apply DRY. NEVER duplicate code."* An AST scan for identical function bodies (docstrings stripped,
  bodies under ~120 characters of AST ignored) finds 125 duplicate groups totalling **971 redundant
  lines** out of 21,525 — about 4.5%. Most of that is 2- and 3-line accessors where each instrument
  independently declares the same value for its own reason, and mechanical de-duplication would be
  wrong. Four groups are not:
  - **`primary_filespec`, six byte-identical 17-line copies:**
    `obs_cassini_common.py:627`, `obs_volume_ebrocc_xxxx.py:73`, `obs_volume_hubble_common.py:82`,
    `obs_volume_nhxxlo_xxxx.py:41`, `obs_volume_nhxxmv_xxxx.py:40`,
    `obs_volume_voyager_common.py:50`. Body, comment and docstring are the same; only an example
    path inside the comment differs. The docstrings already cross-reference one another *"for the
    reason `ObsCassiniCommon.primary_filespec` gives"* — the rationale was shared, the code was not.
  - **`_ring_geo_index_col` / `_surface_geo_index_col`:** `obs_base.py:475-530` and
    `obs_base.py:549-599` are ~55 lines each, differing only in the metadata key
    (`'ring_geo_row'` vs `'surface_geo_row'`) and two message strings. Both carry the same
    message defect: with `col2=None` but `col3` supplied, the error names only `col`, and with all
    three supplied it never names `col3`.
  - **`convert_to_default_unit` / `convert_from_default_unit`:** `units.py:612-649` and
    `units.py:652-689`, 38 lines each, differing only in `*` versus `/` at lines 646 and 686.
  - **`delete_bundle_from_obs_tables` / `delete_opus_id_from_obs_tables`:**
    `do_import_tables.py:80-105` and `:139-164`, 25 lines each, differing in one column name and one
    log message — in the delete path, where a divergence would be expensive.

  **Suggestion:** one parameterized implementation each, with thin named wrappers. **Caveat on my
  own measurement:** the same scan flags `_time_from_index` in `obs_base_pds3.py:131` and
  `obs_base_pds4.py:65` as duplicates, but they are not — the bodies match while the *defaults*
  differ (`'START_TIME'` vs `'pds:start_date_time'`), which is correct specialization. The 971-line
  figure is an upper bound; the four groups above are the part I verified by reading.

- **Finding (Medium): The OPUS↔MySQL type map is written twice, in opposite directions, and the two
  copies disagree.** **Evidence:** `mysql.py:603-651` renders an OPUS `field_type` as MySQL DDL;
  `mysql.py:450-477` maps the server's `DATA_TYPE` back to an OPUS `field_type`. They are not in
  step:
  - `create_table` renders `varchar255`, `varchar32` and six other `varchar*` types
    (line 632); `table_info` has **no `varchar` branch**, so reading such a table back raises
    `NotImplementedError(data_type)` at line 477. The schemas do use them —
    `grep -l varchar src/opus_import/table_schemas/*.json` finds `param_info.json`,
    `user_searches.json`, `django_session.json` — but `table_info` is only ever called on `obs_`
    tables (`do_validate.py:64,155,205,295`), so this is latent, not live.
  - `table_info:474` has a branch for `data_type == 'mult_list'`. `mult_list` is an OPUS type name,
    not a MySQL one; `create_table:636` renders it as `JSON`, so the server reports `json` and
    line 468 handles it. The `mult_list` branch is unreachable.

  **Suggestion:** one module-level bidirectional table, so a new type cannot be added to one
  direction alone. That also shortens `create_table` from 180 lines to something reviewable.

- **Finding (Medium): The `_enter`/`_exit` pair is not exception-safe.** **Evidence:**
  `ImportDBSuper._enter` (`super.py:307`) pushes onto `_enter_stack` and, at depth 1, replaces the
  process-global `warnings.showwarning`; `_exit` (`super.py:326`) pops and restores. There is **no
  `try`/`finally` and no context manager anywhere in the package** — `grep -c "finally:"` returns 0
  for both `super.py` and `mysql.py`, and `grep -rn "contextmanager|__enter__"` over the whole scope
  returns nothing. Every error path therefore leaks: `mysql.py:521` (`raise ImportDBError()` in
  `drop_table`), `:712` (`create_table`), `:279`, `:529`, `:752`, `:793`, `:849`, `:901`, `:956`,
  `:1045`, `:1085`, `:1138` all raise between an `_enter` and its `_exit`. **Impact:** in production
  an `ImportDBError` aborts the run, so the leak is terminal and harmless. It matters in tests and
  in `import_tests`, where an instance survives a caught error: `_enter_stack` never empties, so
  warning collection silently stops for the rest of the process, and `warnings.showwarning` stays
  pointed at a dead list — cross-test global-state leakage of exactly the kind
  `python_testing.mdc` §5 warns about. **Suggestion:** make it a context manager
  (`with self._operation('drop_table'):`), which makes all ~14 call sites correct by construction
  and deletes the `_exit()` calls entirely.

- **Finding (Low): `main()` mixes three jobs.** **Evidence:** `src/opus_import/cli.py:447-696` is
  250 lines covering option-implication expansion (468–501), logging construction (509–532) and the
  run itself. The dictionary `{'info': args.log_info_limit, 'debug': args.log_debug_limit}` is
  written out **seven** times (lines 512, 556, 614, 633, 648, 661, 671). **Suggestion:** extract
  `_apply_option_implications(args)` and `_configure_logging(config, args)`, and bind the limits
  dict once.

- **Finding (Low): `import_util`'s `log_*` functions are a second spelling of `ImportLog`.**
  **Evidence:** `import_util.py:832-903` defines seven one-line functions that forward to
  `ctx.log.<name>`; `import_util.py:828-829` acknowledges *"Both spellings are one
  implementation."* Two ways to do the same thing is two things to keep in step.
  **Suggestion:** pick one — `ctx.log.error(...)` reads better and is what the obs classes already
  use.

- **Finding (Low): A loop variable is read after its loop.** **Evidence:**
  `do_import_index.py:129` sets `ctx.current_index_row_number = row_no + 1`, where `row_no` is left
  over from the `for row_no in row_nos:` loop that ended at line 120. The logged row number is
  whichever duplicate happened to be last. **Suggestion:** name the row deliberately, or drop the
  assignment.

- **Finding (Low): Substring containment used where a path match is meant.** **Evidence:**
  `do_import_index.py:143` `if orig_filespec in deriv_filespec:` decides which of several duplicate
  index rows is the real one. `in` matches anywhere in the string, so a filespec that is a proper
  substring of a longer one (`.../N123.IMG` inside `.../N123.IMG.bak`) matches.
  **Suggestion:** `deriv_filespec.endswith(orig_filespec)`.

- **Strength.** The obs hierarchy is a genuinely good design for this problem. One `field_<table>_<column>`
  method per column, composed by multiple inheritance across PDS-version, mission, instrument and
  bundle layers, with `config_bundle_info.BUNDLE_INFO` as a typed dispatch table keyed by a regex on
  the bundle id. Adding an instrument means adding one module and one `BUNDLE_INFO` entry — no
  existing file needs editing, which is the extensibility property the skill asks about.
  `obs_base.py:17-21` states the one invariant a new obs class must respect (one instance per
  bundle, metadata replaced per row, so nothing derived from it may be cached) and points at
  `opus_id` as the model for the caching that *is* allowed.

- **Strength.** The database layer's brand abstraction is honest about being a stub rather than
  pretending: `importdb/postgresql.py`'s docstring says outright *"Nothing here is implemented … and
  `opus_import.importdb.get_db` has no branch that returns it."*

---

## 7. Security and robustness

- **Finding (Medium): `create_table` maintains its name cache inside a logging conditional.**
  **Evidence:** `src/opus_import/importdb/mysql.py:714-723`:

  ```python
  if self.logger:
      if self.read_only:
          self.logger.log('debug', f'[SIM] Created table "{table_name}"')
      else:
          self.logger.log('debug', f'Created table "{table_name}"')
          # Don't pretend the table has been created if it really hasn't
          # because we might try to read from it later expecting it to
          # really be there!
          assert self._table_names is not None
          self._table_names.add(table_name)
  ```

  With `logger=None` — which `get_db` accepts by default (`importdb/__init__.py:40`) — the table is
  created on the server but never enters `_table_names`. `table_exists` then reports False for a
  table that exists, and the next `create_table(..., ignore_if_exists=True)` re-issues the DDL and
  fails with a server error. `drop_table` gets this right: its cache removal at lines 537–544 is
  *outside* the `if self.logger:` block, so creation and deletion disagree. **Impact:** latent —
  `cli.py:595` always passes a logger, so it cannot fire in production as shipped; but as noted in
  §4 the only unit harness for this class uses `logger=None`. **Suggestion:** move
  `self._table_names.add(table_name)` out to sit beside `self.tables_created.append(table_name)` at
  line 725, guarded on `not self.read_only` rather than on the logger.

- **Finding (Low): Prefix stripping replaces every occurrence, not the prefix.** **Evidence:**
  `src/opus_import/importdb/super.py:205-207`:
  `table_name.replace(self.import_prefix, '').replace(self.import_prefix.lower(), '')`.
  `str.replace` is global, so a table name containing the prefix anywhere else loses that too.
  The line above (204) already asserts the name starts with the prefix, which is what makes the
  correct form available. **Suggestion:** `table_name[len(self.import_prefix):]`.

- **Finding (Low): A session is opened without a context manager.** **Evidence:**
  `src/opus_import/util/retrieve_ra_dec.py:208` `session = requests.Session()` is never closed.
  **Suggestion:** `with requests.Session() as session:`. (The request itself is fine — line 216
  passes `timeout=SIMBAD_TIMEOUT`, and the docstring at lines 204–206 says why.)

- **Strength — this is the part of the codebase I tried hardest to break, and could not.**
  Every identifier that reaches a statement goes through `ImportDBMySQL.quote_identifier`
  (`mysql.py:281-296`), which rejects anything not matching `_IDENTIFIER_RE = \A[A-Za-z0-9_]+\Z`
  (line 52) *before* backtick-quoting it — and the comment at lines 47–51 gives the precise reason
  the validation rather than the quoting is what protects: *"Backticks quote an identifier but do
  not escape a backtick inside one."* Every row value is bound as `%s` through `param_list`
  (`_row_placeholders`, lines 312–329, which explicitly parameterizes `None` too rather than writing
  `NULL` into the text). `_execute`'s docstring (lines 219–230) states the rule as a contract and
  records the subtlety that an empty parameter sequence is not the same as `None`. I traced every
  caller-supplied `where` fragment: all six (`do_import_tables.py:94,153,299,324` plus the two
  `general_select` builders at `do_import_tables.py:130-134` and `:355`) are literals built from
  `quote_identifier` with `%s` placeholders, and the values travel in `where_params`. `bandit -c
  pyproject.toml -r` over the three packages returns **zero results**, and each of the four
  `# nosec B608` markers names its rule and gives a specific reason — including
  `mysql.py:885-888`, which honestly records that `update_row`'s `where` fragment *is* appended
  verbatim and that the method is for trusted callers.

- **Strength.** `opus_config` validates external input the way `security.mdc` §3 asks. Every key is
  taken by a type-specific reader that removes it from the table, and `finish()` (`config.py:461-470`)
  reports whatever is left — so a misspelled key is a startup error naming the file, the table and
  the key rather than a silently-ignored setting. Booleans are rejected where integers are expected
  (`config.py:415`) even though Python counts one as an integer. Nothing is defaulted silently: the
  `OPUS_CONFIG` variable has no fallback path and says so in the error (`config.py:670-674`), for the
  stated reason that a server hosting several installations must not pick up a neighbor's settings.
  No credential appears in source; the two `"..."` strings in the module docstring's example
  (lines 25, 39) are placeholders, as `security.mdc` §4 requires.

---

## 8. Dependencies and tooling

- **Finding (High): CI does not test the declared dependency set.** See §3 for the full evidence.
  In short: `pyproject.toml:31` declares `rms-pdsfile>=0.0.18`; all five CI jobs overwrite it with
  `rms-pdsfile @ git+https://github.com/SETI/rms-pdsfile@rewrite`, an unpinned branch tip.
  **Suggestion:** the workflow comments call this temporary (*"until it ships to PyPI"*), and 0.1.0
  and 0.1.2 have now shipped — so the question is whether the branch and the releases have
  converged. If they have, drop the five override steps and raise the floor. If they have not, the
  declared floor is fiction and should say so.

- **Finding (Medium): A whole-file lint exemption exists in a project that documents having none.**
  **Evidence:** `src/opus_import/config_bundle_info.py:11` is `# flake8: noqa`, which ruff honors as
  a blanket file-level suppression. I verified both halves: `ruff check` on the file as it stands
  passes; the same command on a copy with only that line removed reports **`I001` (un-sorted import
  block)** — the import list at lines 13–42 is not alphabetized (`cocirs_56xxx` precedes
  `cocirs_01xxx`; `hstjx`, `hstnx`, `hstox`, `hstix`, `hstux`), against `python.mdc` §2's
  *"three alphabetically-sorted groups."* It is the **only** blanket noqa in the repository
  (`grep -rn "# flake8: noqa\|# ruff: noqa"` over `src tests import_tests integration_tests docs
  manage.py` returns this one line). Meanwhile `pyproject.toml:423-430` states:
  *"[per-file-ignores] Empty. Every tree in RUFF_PATHS passes with no per-file exception. That is
  what an empty table means and all it means … Fix the code, or suppress the one rule on the one
  line with `# noqa: <CODE>` and the reason, which `RUF100` then keeps honest."* A file-level
  `# flake8: noqa` is a per-file exception that carries no reason, suppresses every present and
  future rule, and is invisible to `RUF100`. **Suggestion:** the author's intent was almost
  certainly to preserve the semantic grouping of volume classes and bundle classes. Say that:
  `# ruff: noqa: I001 - imports are grouped by bundle kind, not alphabetized`, or `# isort:
  skip_file`. Either keeps the grouping, names the one rule, and leaves every other rule enforced.

- **Strength.** `pyproject.toml` is the most carefully justified dependency file I have read. Every
  floor states the observation that set it and how to re-derive it: `rms-julian>=3.0.2` (lines
  25–30) because 3.0.1 used pyparsing's deprecated `setParseAction` and `filterwarnings = ["error"]`
  would turn that into a failure; `coverage>=7.6` (lines 82–87) because the executed-functions check
  needs JSON report format 3; `pytest>=9.0.3` (lines 115–120) with the CVE identifier;
  `ruff>=0.9` (lines 126–137) because the 2025 style guide changed two constructs this tree contains
  many of — and it tells the reader to *measure* rather than trust the claim. `mypy` deliberately
  carries no bound because `django-stubs[compatible-mypy]` already pins it, *"and a second bound
  here would only go stale."* The `filterwarnings` block (lines 183–191) explains why it is empty
  and states that *"a suppression that suppresses nothing is a claim about the code that is false."*

- **Strength.** CI and metadata agree where the skill asks them to. `requires-python = ">=3.12"`,
  the classifiers list 3.12 and 3.13, and the unit-test matrix (`run-tests.yml:157`) is
  `["3.12", "3.13"]`. The lint job runs the same tools as `scripts/run-all-checks.sh` over one
  shared `RUFF_PATHS`/`MYPY_PATHS`/`VULTURE_PATHS` triple (lines 46–56), so local and CI scope
  cannot drift. There is no stale `[tool.black]` or `[tool.isort]`, no `setup.py` beside the
  `pyproject.toml`, and `line-length = 100` matches `python.mdc` §1.

- **Strength.** `vulture` is clean over the configured paths, and `vulture_whitelist.py` holds
  exactly two entries, each with its own justification — including one that documents its own
  fragility: the `lineno` entry notes that at the configured paths it suppresses nothing on its own
  (an unrelated tree marks the name used) and tells a future maintainer to re-check with
  `vulture src` before removing it. I ran that check: it reports `lineno` at `cli.py:64` and
  `super.py:289`, exactly as the comment predicts.

---

## 9. Technical debt and risk

- **Finding (Low): TODO markers are few and one is a tracked category.** **Evidence:** 13
  TODO/FIXME/XXX/HACK comments across the scope — **7** spelled `TODOPDS4` and **4** plain `TODO`.
  The `TODOPDS4` prefix is a searchable category for the unfinished PDS4 work (e.g.
  `import_util.py:370-374`, which explains that PDS4 index files carry no label yet and types are
  inferred from the data). The 4 plain `TODO`s are the ones without an owner or an issue link.
  **Suggestion:** give the four plain ones an issue reference, which `python.mdc` §4 explicitly
  welcomes once a comment already says what the behavior is.

- **Finding (Low): Assertions carry load, and `-O` would remove them.** **Evidence:** 211 `assert`
  statements in scope. Most are mypy-narrowing (`assert ctx.db is not None`), which is what
  `pyproject.toml:483-491` describes when it skips bandit's B101 — and that comment already flags
  the risk: *"Python's `-O` strips asserts, and nothing here is deployed with `-O`; if that ever
  changes, these become real checks and this skip has to be revisited."* A few are not narrowing but
  data validation on schema input: `mysql.py:640` `assert enum_str, (raw_table_name, column)` and
  `mysql.py:681` `assert not foreign_key or key_type == 'foreign'` check the packaged JSON schemas.
  **Suggestion:** none needed while the deployment constraint holds; the risk is documented where it
  belongs. Worth converting the two schema checks to real raises if that ever becomes convenient.

- **Finding (Low): A default-value branch in `create_table` is never exercised.** **Evidence:**
  `mysql.py:668` quotes a default unless it `.isdigit()`. Across the packaged schemas,
  `grep -ho '"field_default": *[^,}]*' src/opus_import/table_schemas/*.json | sort | uniq -c` gives
  288 `null` and 2 `"Y"` — no numeric default exists, so the `isdigit()` branch has never run. It
  would also mishandle a negative or fractional default (`-1` and `0.5` are not `isdigit()`, so both
  would be emitted quoted). **Suggestion:** leave it, or handle the numeric case properly if a
  numeric default is ever added; the current code is not wrong for the data that exists.

- **Finding (Low): Two internal names are stale copies.** **Evidence:**
  `mysql.py:875` `update_row` opens with `super()._enter('insert_row')` — the wrong name;
  `mysql.py:1159` `general_select` uses `_enter('cmd')`. The value is only pushed onto
  `_enter_stack` and never displayed, so nothing observable is wrong today. Four sites also spell
  the same call `self._exit()` (lines 1087, 1140, 1162, 1190) where the rest write `super()._exit()`;
  identical in effect, inconsistent to read. **Suggestion:** fix the two names; pick one spelling.

- **Strength.** There is essentially no compatibility debt. `python.mdc` §2's *"NEVER include
  backwards-compatibility code"* is honored — I found no shim, no deprecated alias, and no
  version-conditional branch in the scope. The one place a version is consulted
  (`mysql.py:220`, adding `NO_AUTO_CREATE_USER` to the SQL mode for MySQL 5) is server-side
  capability handling, not code compatibility.

---

## 10. Packaging and distribution

- **Finding (Low): The wheel's package-data story is documented but not checked.** **Evidence:**
  `pyproject.toml:202-236` is an excellent 35-line audit of what ships and why, including the
  command that regenerates the inventory and a candid note that the per-directory `README.md` files
  under the Django app *"are kept because the alternatives are worse, not because they earn their
  place."* Nothing runs that command. **Suggestion:** `tests/opus_packaging/` already exists; a test
  that builds the wheel and asserts the four `opus_import` data patterns are present would turn the
  comment into a gate. (This is a small point precisely because the reasoning is already written
  down.)

- **Strength.** Metadata is complete against the skill's checklist: `description`, `readme`,
  `license`, `keywords`, 13 classifiers, `requires-python`, and a full `[project.urls]` block with
  Homepage, Documentation, Repository, Source and Issues (lines 59–64). Version is single-sourced
  through `setuptools_scm` writing `src/opus_config/_version.py` (line 251), with every other
  package reading `importlib.metadata.version("rms-opus")` — stated in
  `opus_config/__init__.py:4-6` — so there is no second copy to disagree. `py.typed` is present in
  all five packages and shipped via `[tool.setuptools.package-data]` `"*" = ["py.typed"]`.
  `namespaces = false` is set with the reason given (lines 196–200): without it the
  `table_schemas` and `dictionary_data` directories would become importable namespace packages.
  Package data is reached through `importlib.resources` (`import_util.py:99-100`), not `__file__`,
  so it resolves inside an installed wheel — and the comment says that is why.

---

## Recommended priorities

1. **Reconcile `rms-pdsfile` between `pyproject.toml`, CI and the docstring** (§3, §8). This is the
   only finding that affects everyone who installs the distribution: the declared dependency does
   not typecheck, no released version ships `py.typed`, five CI jobs replace it with a branch tip,
   and `obs_base.py:183-185` asserts the opposite. Raise the floor to a `py.typed`-shipping release
   and delete the override steps, or add the `[[tool.mypy.overrides]]` entry — and fix the docstring
   either way.

2. **Break up `import_one_index` and `import_observation_table`, starting with the pieces that can
   be unit-tested without MySQL** (§1, §4). 612 and 350 lines at nesting depth 8, covered 3% and 6%
   by the fast tier. Duplicate-row resolution and the inventory-CSV reader are the two cleanest
   extractions and would move the coverage number where it matters. While there, move the five
   `config_targets` checks from `import_tests/test_unit_layers.py:43-127` into `tests/` — they need
   no database and currently never run in the default suite.

3. **Give the golden suite its own schema for the re-import** (§4). `test_goldens.py:293`'s
   `reimport` fixture mutates the database the module's comparisons read and relies on collection
   order to stay correct. The suite already builds per-case schemas for the negative tests, so the
   fix is one more of those.

4. **Replace the blanket `# flake8: noqa`** at `config_bundle_info.py:11` with `# ruff: noqa: I001`
   plus the reason (§8). One line, and it restores the property `pyproject.toml` already claims in
   prose — the only file-level lint exemption in the repository.

5. **Fix the two database-layer defects** (§7, §6): move the `_table_names.add()` at
   `mysql.py:723` out of the `if self.logger:` block, and turn `_enter`/`_exit` into a context
   manager so the ~14 call sites become exception-safe by construction.

6. **Give `opus_support`'s public parsers real exception messages** (§2), and update the ten
   assertions that currently pin `str(excinfo.value) == ''` (§4). The package's own `__init__.py`
   disclaims API stability, so nothing is owed to the empty contract.

7. **Pull up the four verified duplication groups and unify the OPUS↔MySQL type map** (§6), then
   add `*` before the optional parameters in the 68 signatures that need it (§2), and split the two
   over-length modules (§1) — `units.py` along the seam at line 600 that already exists, `mysql.py`
   by lifting the DDL rendering out. All three are mechanical, and mypy finds every affected call
   site.

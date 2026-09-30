# Codebase analysis: opus/import

## Summary

The `opus/import` package is the OPUS data import pipeline: a 15,500-line (72 Python
files) system that reads PDS3/PDS4 planetary science data and populates a MySQL database
with observation, mult, and auxiliary tables. The architecture is centered on a clear
class hierarchy (`ObsBase` -> `ObsGeneral`/`ObsPds`/... -> instrument-specific classes)
and a JSON-driven table-schema system, which makes adding new instruments straightforward.

However, the codebase has significant gaps relative to the project's own coding standards:
**zero automated tests**, **zero type annotations**, **near-zero docstrings** across all
72 files, **two modules exceeding the 1000-line limit**, **pervasive mutable global
state** via `impglobals`, **bare `except:` clauses**, and **wildcard imports**. The
util/ scripts have SQL injection risks and credential wildcard imports.

Top 3 priorities: (1) add tests for critical paths and pure helpers, (2) add type
annotations and docstrings starting with core modules, (3) eliminate bare except/wildcard
imports and narrow exception handling.

---

## File inventory

| Category | Count | Total lines | Files |
|---|---|---|---|
| Core pipeline | 6 | 3,277 | `main_opus_import.py` (546), `do_import.py` (1778), `import_util.py` (530), `impglobals.py` (24), `config_data.py` (133), `config_bundle_info.py` (270) |
| Config/data | 2 | 1,026 | `config_targets.py` (1003), `instruments.py` (23) |
| Database layer | 4 | 909 | `importdb/__init__.py` (22), `importdb/super.py` (183), `importdb/mysql.py` (696), `importdb/postgresql.py` (8) |
| Auxiliary do_* | 7 | 786 | `do_cart.py` (38), `do_dictionary.py` (178), `do_django.py` (21), `do_param_info.py` (120), `do_partables.py` (131), `do_table_names.py` (182), `do_update_mult_info.py` (56), `do_validate.py` (256) |
| Obs hierarchy (base) | 14 | 1,203 | `obs_base.py` (433), `obs_base_pds3.py` (121), `obs_base_pds4.py` (48), `obs_general.py` (184), `obs_general_pds3.py` (21), `obs_general_pds4.py` (14), `obs_pds.py` (52), `obs_pds_pds3.py` (47), `obs_pds_pds4.py` (35), `obs_common_pds3.py` (23), `obs_common_pds4.py` (23), `obs_cassini_common.py` (362), `obs_cassini_common_pds3.py` (106), `obs_cassini_common_pds4.py` (17) |
| Obs table mixins | 7 | 862 | `obs_type_image.py` (55), `obs_wavelength.py` (107), `obs_profile.py` (86), `obs_profile_pds3.py` (56), `obs_profile_pds4.py` (77), `obs_ring_geometry.py` (479), `obs_surface_geometry.py` (70), `obs_surface_geometry_name.py` (41), `obs_surface_geometry_target.py` (330) |
| Obs volumes (instruments) | 28 | 7,104 | `obs_volume_coiss_12xxx.py` (527), `obs_volume_cocirs_01xxx.py` (465), `obs_volume_cocirs_56xxx.py` (210), `obs_volume_corss_8xxx.py` (190), `obs_volume_couvis_0xxx.py` (426), `obs_volume_couvis_8xxx.py` (157), `obs_volume_covims_0xxx.py` (324), `obs_volume_covims_8xxx.py` (155), `obs_volume_cassini_occ_common.py` (157), `obs_volume_couvis_covims_occ_common.py` (128), `obs_volume_ebrocc_xxxx.py` (268), `obs_volume_galileo_common.py` (36), `obs_volume_go_0xxx.py` (322), `obs_volume_hubble_common.py` (254), `obs_volume_hstix_xxxx.py` (129), `obs_volume_hstjx_xxxx.py` (148), `obs_volume_hstnx_xxxx.py` (125), `obs_volume_hstox_xxxx.py` (138), `obs_volume_hstux_xxxx.py` (113), `obs_volume_new_horizons_common.py` (117), `obs_volume_nhxxlo_xxxx.py` (168), `obs_volume_nhxxmv_xxxx.py` (167), `obs_volume_vg28xx.py` (199), `obs_volume_vg2801_vg2802.py` (285), `obs_volume_vg2803.py` (182), `obs_volume_vg2810.py` (179), `obs_volume_vgiss_5678xxx.py` (227), `obs_volume_voyager_common.py` (110) |
| Obs bundles (PDS4) | 3 | 560 | `obs_bundle_occ_common.py` (160), `obs_bundle_uranus_occs_earthbased.py` (199), `obs_bundle_cassini_uvis_solarocc_beckerjarmak2023.py` (201) |
| Util scripts | 4 | ~460 | `util/dump_pds_definitions.py`, `util/get_opus2_mults.py`, `util/obs_table_to_schema.py`, `util/retrieve_ra_dec.py` |

---

## 1. Structure and layout

- **Finding (High)**: Two modules exceed the project 1000-line limit. **Evidence**:
  `do_import.py` is 1,778 lines; `config_targets.py` is 1,003 lines. Project rule:
  "ALWAYS keep modules under 1000 lines." **Suggestion**: Split `do_import.py` by
  responsibility into submodules: table preparation (~lines 1-270), mult table handling
  (~lines 271-533), import-one-bundle / import-one-index (~lines 534-1175), observation
  table import / field functions (~lines 1176-1630), main import loop (~lines 1645-1778).
  `config_targets.py` could be split by section (mapping, target info, star RA/DEC,
  planet groups).

- **Finding (Medium)**: No package `__init__.py` for `opus/import`. **Evidence**: Only
  `importdb/__init__.py` exists. The rest of `opus/import` is a flat set of modules
  imported via `sys.path` manipulation in `main_opus_import.py`. **Suggestion**: If the
  package is intended only as a CLI tool invoked via `main_opus_import.py`, document
  this clearly. Otherwise, add `__init__.py` and consider making it installable.

- **Finding (High)**: Pervasive mutable module-level globals used as shared state.
  **Evidence**: `impglobals.py` defines 12 mutable globals: `DATABASE`, `LOGGER`,
  `ARGUMENTS`, `PYTHON_WARNING_LIST`, `LOGGED_IMPORT_WARNINGS`, `LOGGED_IMPORT_ERRORS`,
  `IMPORT_HAS_BAD_DATA`, `MAX_TABLE_ID_CACHE`, `CURRENT_BUNDLE_ID`,
  `CURRENT_INDEX_ROW_NUMBER`, `CURRENT_PRIMARY_FILESPEC`, `TRY_CART_LATER`. These are
  accessed by virtually every module. Additionally, `do_import.py` has module-level
  mutable globals: `_MULT_TABLE_CACHE`, `_CREATED_IMP_MULT_TABLES`,
  `_MODIFIED_MULT_TABLES`. **Suggestion**: Introduce an `ImportContext` dataclass
  containing database, logger, arguments, and current-state tracking. Pass it through
  entry points into do_* and obs_* code incrementally.

- **Finding (Medium)**: Duplicate SCLK-parsing patterns across many obs_volume files.
  **Evidence**: The try/except pattern for `opus_support.parse_cassini_sclk(sc)` with
  `_log_nonrepeating_error` is duplicated in `obs_volume_coiss_12xxx.py`,
  `obs_volume_couvis_0xxx.py`, `obs_volume_covims_0xxx.py`, `obs_volume_covims_8xxx.py`,
  `obs_volume_couvis_8xxx.py`, `obs_volume_cocirs_01xxx.py`, `obs_volume_cocirs_56xxx.py`,
  `obs_volume_corss_8xxx.py` (at least 16 instances). Similar patterns for Voyager SCLK
  in `obs_volume_voyager_common.py`, Galileo SCLK in `obs_volume_go_0xxx.py`, and New
  Horizons SCLK in `obs_volume_new_horizons_common.py` (6+ instances). **Suggestion**:
  Extract a shared `_parse_sclk_safe(self, sc, mission)` method in the appropriate
  common base class that handles the try/except/log pattern once.

- **Finding (Low)**: Deep, complex multiple inheritance (MRO). **Evidence**:
  `ObsCommonPDS3` inherits from 9 classes: `ObsGeneralPDS3`, `ObsPdsPDS3`,
  `ObsTypeImage`, `ObsWavelength`, `ObsProfilePDS3`, `ObsRingGeometry`,
  `ObsSurfaceGeometry`, `ObsSurfaceGeometryName`, `ObsSurfaceGeometryTarget`.
  Same for `ObsCommonPDS4`. Final instrument classes inherit from these plus
  mission-common classes (e.g. `ObsCassiniCommonPDS3`), creating diamond inheritance.
  **Suggestion**: Document the MRO explicitly in a class hierarchy diagram. The current
  mixin pattern works but is fragile; consider composition if refactoring.

- **Finding (Low)**: `instruments.py` is effectively dead code. **Evidence**: All entries
  in `PDSTABLE_PREPROCESS` and `PDSTABLE_REPLACEMENTS` are commented out. The module is
  still imported by `import_util.py`. **Suggestion**: Remove or explain purpose; if the
  hooks are needed for future instruments, add a comment.

- **Finding (Low)**: `importdb/postgresql.py` is an empty stub. **Evidence**: 8 lines,
  only `__init__` that calls `super().__init__()` with no implementation. Commented out
  in `importdb/__init__.py`. **Suggestion**: Remove or clearly mark as placeholder.

---

## 2. Best practices alignment

- **Finding (Critical)**: Wildcard imports of secrets and config in entry point.
  **Evidence**: `main_opus_import.py` line 25: `from opus_secrets import *`; line 36:
  `from config_data import *`. Util scripts `get_opus2_mults.py` and
  `obs_table_to_schema.py` use `from secrets import *`. Project rule: imports must be
  explicit. **Suggestion**: Replace with explicit named imports. For the entry point,
  import only needed symbols: `from opus_secrets import DB_BRAND, DB_HOST_NAME, ...`.

- **Finding (High)**: Bare `except:` used in critical paths. **Evidence**:
  - `main_opus_import.py` line 541: `except:` (top-level catch-all)
  - `import_util.py` line 304: `except:` (in `safe_pdstable_read_pds3`)
  - `import_util.py` line 410: `except: raise` (pointless re-raise)
  - `do_param_info.py` line 38: `except: raise` (pointless re-raise)

  Project rule: "NEVER use bare except." **Suggestion**: Replace with
  `except Exception:` and preserve traceback. Remove the pointless `except: raise`
  blocks entirely.

- **Finding (High)**: Broad `except Exception as e` used pervasively for SCLK parsing.
  **Evidence**: At least 18 instances across obs_volume_* files catch `Exception` for
  SCLK parsing. While these do log errors, they catch more than intended. **Suggestion**:
  Catch the specific exception from `opus_support.parse_cassini_sclk` (likely
  `ValueError`), or at minimum keep as `except Exception` but consolidate into a single
  helper method.

- **Finding (Medium)**: `assert` used for control flow and validation in production code.
  **Evidence**: `obs_volume_vgiss_5678xxx.py` line 216: `assert camera in [...]`;
  `obs_volume_voyager_common.py` lines 29, 50: assert for host validation;
  `obs_volume_hubble_common.py` lines 25-26; `importdb/super.py` lines 85, 117, etc.:
  `assert False` as "must override" enforcement; `util/dump_pds_definitions.py` line 22:
  `assert False`. **Suggestion**: Replace with explicit `raise ValueError(...)` or
  `raise NotImplementedError(...)` since asserts are stripped in optimized mode.

- **Finding (Medium)**: `sys.path` manipulation in entry point. **Evidence**:
  `main_opus_import.py` has 3 `sys.path.insert(0, ...)` calls (lines 23, 27, 31) to
  make sibling packages importable. **Suggestion**: Document as intentional script
  bootstrap; long-term, make the package installable via `pip install -e .`.

- **Finding (Medium)**: `.find()` used instead of `in` operator. **Evidence**:
  `obs_volume_hstnx_xxxx.py`, `obs_volume_hstux_xxxx.py` use `.find('POL') == -1`
  instead of `'POL' not in`; `obs_volume_covims_0xxx.py` uses `.find('VIMS') != -1`;
  `do_import.py` uses `.find(':') != -1` and `.find('<TARGET>') == -1`. At least 15
  instances. Project rule: "Prefer ... `in` for membership checks." **Suggestion**:
  Replace `.find(x) != -1` with `x in s` and `.find(x) == -1` with `x not in s`.

- **Finding (Low)**: Mutable default argument in `ImportDBSuper.__init__`.
  **Evidence**: `importdb/super.py` line 8: `mult_form_types=[]`. **Suggestion**:
  Use `mult_form_types=None` and `self._mult_form_types = mult_form_types or []`.

- **Finding (Low)**: Typo in `importdb/super.py` line 113: `warnings.showarning`
  should be `warnings.showwarning`. **Evidence**: This silently fails to restore the
  original warning handler. **Suggestion**: Fix the typo.

---

## 3. Types and static checks

- **Finding (Critical)**: Zero type annotations across all 72 Python files. **Evidence**:
  No function signatures use parameter or return type annotations anywhere in the
  package. Project rule: "ALWAYS annotate all function/method parameters and return
  values." **Suggestion**: Add annotations incrementally starting with the most-used
  modules: `import_util.py`, `importdb/super.py`, `importdb/mysql.py`, `obs_base.py`,
  `do_import.py`.

- **Finding (Critical)**: Near-zero docstrings across the entire package. **Evidence**:
  Of ~72 Python files and ~500+ functions/methods, fewer than 20 have docstrings. Most
  files use only `#` block header comments. Only `obs_base.py:ObsBase.__init__`,
  `do_import.py` (5-6 functions), and `importdb/mysql.py` (a few methods) have any
  docstrings. Project rule: "EVERY class, method, function, and module MUST have a
  descriptive docstring." **Suggestion**: Prioritize docstrings on public API and core
  pipeline functions first (all functions in `import_util.py`, `do_import.py`, `obs_base.py`,
  `importdb/*.py`). Use Google-style with `Parameters:`, `Returns:`, `Raises:`.

- **Finding (High)**: No `__all__` declaration anywhere. **Evidence**: No file in the
  package defines `__all__`. `importdb/__init__.py` exports `get_db`,
  `ImportDBException`, `ImportDBMySQL` implicitly. **Suggestion**: Add `__all__` to
  `importdb/__init__.py` and any other module treated as a library surface.

---

## 4. Testing

- **Finding (Critical)**: Zero automated tests for the import package. **Evidence**:
  No `test_*.py` files under `opus/import` or anywhere in the repo referencing import
  modules. Repo-wide grep for `do_import`, `import_util`, `impglobals`, `obs_base`,
  `config_data` in test files returns no matches. The `import_for_tests.sh` shell
  script performs a manual end-to-end import, not a pytest suite. **Suggestion**: Add
  tests in order of priority:
  1. **Pure helper functions** in `import_util.py`: `safe_column`, `encode_target_name`,
     `decode_target_name`, `table_name_mult`, `slug_name_for_sfc_target`,
     `read_schema_for_table`, `find_max_table_id`, `cached_tai_from_iso`, `safe_join`.
  2. **Config lookups** in `config_targets.py`: `TARGET_NAME_MAPPING` round-trips,
     `STAR_RA_DEC` completeness, `PLANET_GROUP_MAPPING` coverage.
  3. **Obs field methods** with mocked metadata: test a representative obs_volume class
     (e.g. `ObsVolumeCOISS12xxx`) with fixture index rows.
  4. **DB layer** in `importdb/`: mock `MySQLdb` and test `create_table`, `insert_rows`,
     `table_names`, `table_exists`.
  5. **Integration**: small fixture data + test DB for one bundle end-to-end.

---

## 5. Performance and resource use

- **Finding (Medium)**: `upsert_rows` in `importdb/mysql.py` does one-by-one upserts.
  **Evidence**: Line 646-651: `upsert_rows` iterates calling `upsert_row` individually.
  In contrast, `insert_rows` batches 1000 rows per SQL statement. **Suggestion**: Batch
  upserts using MySQL's `INSERT ... ON DUPLICATE KEY UPDATE` with multiple value sets.

- **Finding (Medium)**: `NoDupLogger` in `import_util.py` uses lists for dedup, causing
  O(n) lookup. **Evidence**: Lines 441-478: `_LOGGED_DEBUG`, `_LOGGED_WARN`, etc. are
  lists; each `warn()`/`error()` call does `if key in self._LOGGED_*` which is O(n).
  These are class-level (shared across instances) and never cleared. **Suggestion**:
  Use sets instead of lists for O(1) membership testing. (Note: the key is a tuple of
  `(msg, args, kwargs)` — `kwargs` would need to be converted to a hashable form.)

- **Finding (Low)**: `table_exists` in `importdb/super.py` rebuilds a lowered list every
  call. **Evidence**: Line 122-126: `table_names = [x.lower() for x in
  self.table_names(namespace)]` is called on every existence check, rebuilding the list.
  **Suggestion**: Cache a lowered set version or use the cached `_table_names` directly
  with case-insensitive comparison.

- **Finding (Low)**: Good use of `lru_cache` in `import_util.cached_tai_from_iso` and
  `importdb/mysql.py:table_info`. No major hot-path issues identified without profiling.

---

## 6. Maintainability and extensibility

- **Finding (High)**: Tight coupling via `impglobals` makes testing and reuse difficult.
  **Evidence**: Every `do_*` module, `import_util`, and all `obs_*` classes access
  `impglobals.DATABASE`, `impglobals.LOGGER`, `impglobals.ARGUMENTS` directly. This
  means no function can be tested without setting up the full global state.
  **Suggestion**: Introduce an `ImportContext` or similar, passed from
  `main_opus_import.py`, that carries database/logger/arguments. Refactor incrementally.

- **Finding (Medium)**: Obs class hierarchy is well-designed and extensible. **Evidence**:
  `ObsBase` -> version-specific (`ObsBasePDS3`/`ObsBasePDS4`) -> table-specific
  (`ObsGeneral`, `ObsPds`, `ObsWavelength`, ...) -> mission-common
  (`ObsCassiniCommon`, `ObsVolumeVoyagerCommon`, ...) -> instrument-specific
  (`ObsVolumeCOISS12xxx`, etc.). New instruments follow `docs/adding_an_instrument_or_mission.md`.
  The `field_obs_<table>_<column>` naming convention auto-maps to table columns via
  `import_run_field_function()`. **Suggestion**: Keep and document this pattern. Add
  an architecture diagram.

- **Finding (Medium)**: `import_observation_table()` in `do_import.py` is a 270-line
  function (lines 1178-1448) with deeply nested control flow. **Evidence**: It handles
  field iteration, value validation, type coercion, mult table updates, and error
  checking all in one function. **Suggestion**: Extract sub-functions: `_compute_column_value()`,
  `_validate_column_value()`, `_handle_mult_field()`.

- **Finding (Medium)**: `import_one_index()` in `do_import.py` is a 540-line function
  (lines 635-1175) with the entire import logic for one index file. **Suggestion**:
  Extract phases into named functions: `_read_associated_metadata()`,
  `_process_observation_row()`, `_handle_surface_geometry()`, `_dump_tables_to_db()`.

- **Finding (Low)**: Dead/unreachable code. **Evidence**:
  - `obs_volume_cassini_occ_common.py` lines 31-35: commented-out multi-target fake
  - `obs_volume_covims_0xxx.py` lines 107-122: code after `return` statement
  - `instruments.py`: all entries commented out
  **Suggestion**: Remove or explain purpose.

---

## 7. Security and robustness

- **Finding (High)**: SQL injection risk in util scripts. **Evidence**:
  `util/get_opus2_mults.py` line 36: table name inserted directly into SQL string.
  `util/obs_table_to_schema.py` lines 97, 213-218: f-string SQL queries with
  unsanitized `table_name` and `field_name`. **Suggestion**: Use parameterized queries
  or at minimum validate identifiers against an allowlist.

- **Finding (High)**: `from secrets import *` in util scripts. **Evidence**:
  `util/get_opus2_mults.py` line 12; `util/obs_table_to_schema.py` line 58. These
  import from a local `secrets` module (not stdlib) that contains `DB_USER`,
  `DB_PASSWORD`. **Suggestion**: Replace with explicit imports.

- **Finding (Medium)**: Credentials handled via parameters, not hardcoded. **Evidence**:
  `importdb/__init__.py:get_db()` receives credentials as parameters from the entry
  point. `opus_secrets` (gitignored) is the single source. **Suggestion**: Ensure
  `opus_secrets.py` is in `.gitignore` and DB passwords are never logged. Consider
  environment variables.

- **Finding (Medium)**: SQL string construction in `importdb/mysql.py` uses backtick
  quoting but not parameterization for identifiers. **Evidence**: Table names, column
  names, and schema names are inserted via f-strings (e.g., line 55:
  `f'USE \`{self.db_schema}\`'`; line 155: `TABLE_SCHEMA='{self.db_schema}'`). String
  values in INSERT/UPDATE use `%s` parameterization correctly. **Suggestion**: Validate
  identifiers (table/column names) against a pattern like `^[a-zA-Z0-9_]+$` at the
  boundary.

- **Finding (Low)**: `do_import.py` line 70: `where = f'{q("bundle_id")}="{bundle_id}"'`
  constructs WHERE clause with unescaped `bundle_id`. While bundle IDs come from
  config (not user input), this is fragile. **Suggestion**: Use parameterized queries
  for WHERE clauses.

---

## 8. Dependencies and tooling

- **Finding (Medium)**: Import package depends on several external packages not visible
  in a top-level `pyproject.toml` or `requirements.txt`. **Evidence**: Uses `pdsfile`,
  `pdslogger`, `pdsparser`, `pdstable`, `julian`, `opus_support`, `numpy`, `MySQLdb`
  (mysqlclient). These are imported at module level. **Suggestion**: Ensure all are
  declared in project dependencies; consider making `MySQLdb` optional with a clear
  error (already partially done via `MYSQLDB_AVAILABLE` flag).

- **Finding (Medium)**: Entry point assumes specific repo layout. **Evidence**:
  `main_opus_import.py` computes `PROJECT_ROOT` and `RMS_OPUS_ROOT` relative to its
  own `__file__` location and manipulates `sys.path` (3 inserts). **Suggestion**:
  Document the required layout; long-term, make installable as `pip install -e .`.

- **Finding (Low)**: `README.md` for `opus/import` is a scratchpad TODO list, not
  documentation. **Evidence**: Contains apt-get commands, a TODO list, and "THE BIG
  QUESTIONS" section. No usage instructions, no architecture overview, no Python version
  or venv requirements. **Suggestion**: Rewrite as proper README with: purpose, setup,
  usage (`python main_opus_import.py --help`), architecture overview, and link to
  `docs/` for detailed schema/format docs.

- **Finding (Low)**: Good internal documentation exists for DB schema and OPUS ID format.
  **Evidence**: `docs/database_schema.md` (626 lines, comprehensive schema docs),
  `docs/opus_id_format.md` (thorough naming conventions). **Suggestion**: Keep and
  cross-reference from README.

---

## 9. Technical debt and risk

- **Finding (High)**: 13 TODO/TODOPDS4/XXX comments indicating incomplete PDS4 support.
  **Evidence**:
  - `import_util.py` lines 241, 275: PDS4 index files lack labels, type inference is a hack
  - `main_opus_import.py` lines 421, 423: `Pds4File.use_shelves_only()` and `require_shelves()` commented out
  - `do_import.py` lines 1544, 1578: PDS4 `find_selected_row_key` raises OSError
  - `obs_volume_corss_8xxx.py` line 14: "Verify these are correct"
  - `obs_volume_vg2803.py` line 11: "Verify these are correct"
  - `obs_volume_ebrocc_xxxx.py` line 16: invalid PDS4 context product
  - `obs_bundle_uranus_occs_earthbased.py` lines 11, 28
  - `obs_profile_pds4.py` line 55: unresolved optical depth interpretation
  - `obs_bundle_cassini_uvis_solarocc_beckerjarmak2023.py` line 111
  - `obs_general.py` lines 59, 102: `### XXX Review this`
  **Suggestion**: Triage each into a GitHub issue or resolve. The PDS4 TODOs represent
  a category of technical debt that will grow as more PDS4 bundles are added.

- **Finding (High)**: Potential bugs found during review:
  - **Typo**: `importdb/super.py` line 113: `warnings.showarning` should be
    `warnings.showwarning`. This silently fails to restore the original handler.
  - **Unbound variable risk**: `obs_volume_hstjx_xxxx.py` ~line 94: if the final `else`
    branch fires in the filter wavelength chain, `wr` and `bw` may be undefined before
    `spec_size = bw // wr` is computed.
  - **None comparison crash**: `obs_volume_hstox_xxxx.py` ~line 67: `wr1 > wr2` is
    evaluated without checking for `None` first.
  - **Missing return**: `obs_profile_pds4.py` `field_obs_profile_occ_type`: error path
    falls through to implicit `None` without explicit return.
  - **Dead code**: `obs_volume_covims_0xxx.py` has code after a `return` statement
    in `field_obs_general_ring_obs_id`.
  **Suggestion**: Fix these bugs immediately.

- **Finding (Medium)**: Pervasive magic numbers. **Evidence**: At least 25 files contain
  unexplained numeric constants. Key examples:
  - `10000.` (wavenumber conversion) in `obs_wavelength.py`, `obs_volume_cocirs_01xxx.py`,
    `obs_volume_cocirs_56xxx.py`, `obs_volume_corss_8xxx.py` — should be a named constant
  - `180.`, `90.`, `360.` in ~20 obs_* files — longitude/angle constants
  - `-1.942979`, `-130.589560`, etc. in `obs_ring_geometry.py` — planetary ascending
    node offsets with no citation
  - `/1000.` and `/1000` (unit conversions) in ~10 files
  - `4096`, `1024`, `256`, `65536` (detector levels/sizes) in 8+ files
  - `0.8842`, `5.1225`, etc. in `obs_volume_covims_0xxx.py` — instrument calibration
  **Suggestion**: Define named constants (e.g., `WAVENUMBER_TO_MICRON = 10000.`,
  `DEGREES_PER_CIRCLE = 360.`) at module level or in a shared constants module.

- **Finding (Medium)**: Long-standing README TODO list indicates deferred work.
  **Evidence**: `README.md` lists 12+ items including JSON validation, index optimization,
  foreign key changes, and mult table regeneration. **Suggestion**: Convert actionable
  items to GitHub issues; remove completed/obsolete items.

- **Finding (Medium)**: Deprecated util scripts still in tree. **Evidence**:
  `util/get_opus2_mults.py` and `util/obs_table_to_schema.py` are one-time migration
  tools from OPUS2 to OPUS3 with SQL injection risks and `from secrets import *`.
  **Suggestion**: Move to an `archive/` directory or remove entirely with a git note.

- **Finding (Low)**: Spelling typos. **Evidence**: "compatability" (should be
  "compatibility") in `obs_volume_nhxxlo_xxxx.py` line 89 and `obs_volume_nhxxmv_xxxx.py`
  line 91. "contraints" (should be "constraints") in `do_import.py` lines 42, 72, 118.
  **Suggestion**: Fix typos.

---

## Recommended priorities

1. **Fix bugs found during review** — The `importdb/super.py` typo
   (`warnings.showarning`), the unbound variable risk in `obs_volume_hstjx_xxxx.py`,
   the None comparison crash in `obs_volume_hstox_xxxx.py`, and the dead code in
   `obs_volume_covims_0xxx.py` should be fixed immediately as they represent runtime
   risks.

2. **Add tests for pure helpers and critical paths** — Start with `import_util.py`
   functions (no DB dependency), `config_targets.py` lookups, and one obs_volume class
   with mocked metadata. Target 80% coverage of `import_util.py` first. This enables
   safe refactoring.

3. **Replace bare `except:` and wildcard imports** — In `main_opus_import.py`,
   `import_util.py`, and `do_param_info.py`, replace bare `except:` with
   `except Exception:`. Replace `from opus_secrets import *` and `from config_data import *`
   with explicit imports. This aligns with project rules and improves debuggability.

4. **Add type annotations and docstrings to core modules** — Annotate and document
   `import_util.py`, `importdb/super.py`, `importdb/mysql.py`, `obs_base.py`, and
   `do_import.py` first. This improves IDE support, enables mypy checking, and makes
   the codebase approachable.

5. **Split `do_import.py`** — Break the 1,778-line module into 4-5 submodules by
   responsibility area. This meets the 1000-line rule and makes the core pipeline
   more navigable.

6. **Extract shared SCLK parsing helper** — Consolidate the ~18 duplicated SCLK
   try/except/log patterns into a single method in the appropriate base class. This
   reduces ~100 lines of duplicated code.

7. **Introduce ImportContext to reduce `impglobals` coupling** — Pass database, logger,
   and arguments through a context object. This is the highest-effort item but enables
   testability and removes the single biggest architectural issue.

8. **Define named constants for magic numbers** — Create a `constants.py` module for
   frequently used values (wavenumber conversion, angle constants, detector parameters).

9. **Triage TODOPDS4 items** — Convert the 13 TODO/TODOPDS4 comments into GitHub issues
   with clear descriptions and link them. This ensures PDS4 support gaps are tracked.

10. **Rewrite `opus/import/README.md`** — Replace the scratchpad with proper usage docs,
    architecture overview, and links to the existing (good) `docs/` files.

# Codebase Analysis: opus/application/apps, opus/application/test_api, opus/application/templates

## Summary

This analysis covers the Django application layer of the OPUS (Outer Planets Unified Search) web application — a planetary science data search tool serving NASA PDS (Planetary Data System) data. The codebase is a mature, feature-rich Django project with 9 apps (cart, dictionary, help, metadata, paraminfo, results, search, tools, ui), an extensive integration test suite (`test_api/`), and Django template overrides.

**Overall health**: Functional and well-structured for its era but shows significant technical debt. The code predates modern Python/Django conventions (no type annotations, no `pyproject.toml`, heavy raw SQL, deprecated Django APIs). Top priorities are: (1) migrating from raw SQL string-building to parameterized ORM queries or at least a SQL builder, (2) adding type annotations and modern Python practices, and (3) improving test coverage beyond null-request edge cases.

---

## 1. Structure and Layout

- **Finding**: The application is organized into 9 Django apps under `apps/`, which is a reasonable separation of concerns (cart, dictionary, help, metadata, paraminfo, results, search, tools, ui). Each app has its own `views.py`, `urls.py`, `models.py`, and test file.
  **Evidence**: `opus/application/apps/` directory structure.
  **Suggestion**: Good modular layout; maintain this separation.

- **Finding**: Several files are extremely large and exceed the project's 1000-line limit. `search/views.py` is ~2034 lines, `results/views.py` is ~1894 lines, `cart/views.py` is ~1561 lines, `ui/views.py` is ~1827 lines, and `search/models.py` exceeds 100,000 characters (could not be fully loaded).
  **Evidence**: `search/views.py` (2034 lines), `results/views.py` (1894 lines), `cart/views.py` (1561 lines), `ui/views.py` (1827 lines), `search/models.py` (703,286 chars).
  **Suggestion**: Split these into submodules. For example, `search/views.py` could be split into `search/api.py`, `search/query_builder.py`, `search/url_parser.py`, and `search/cache.py`. The massive `search/models.py` should be broken into multiple files in a `models/` package.

- **Finding**: `search/test_search.py` is also extremely large (175,885 chars), making it difficult to navigate and maintain.
  **Evidence**: File exceeds 100K character read limit.
  **Suggestion**: Split into multiple test files by feature area (e.g., `test_normalize_input.py`, `test_string_search.py`, `test_triggered_tables.py`).

- **Finding**: Significant dead/commented-out code exists. `dictionary/admin.py` is entirely commented out (54 lines). `dictionary/views.py` has ~65 lines of commented-out code from an old web-based dictionary feature. `dictionary/urls.py` has most URL patterns commented out. `dictionary/tests.py` is effectively empty (only comments).
  **Evidence**: `dictionary/admin.py` (lines 1–54 all comments), `dictionary/views.py` (lines 20–108 commented out), `dictionary/urls.py` (lines 6–27 commented out).
  **Suggestion**: Remove all dead code. If needed for reference, it lives in version control history.

- **Finding**: Empty `__init__.py` files exist for all apps, which is fine for Django apps, but several serve no purpose and could use docstrings describing the app.
  **Evidence**: All app `__init__.py` files are empty.
  **Suggestion**: Add module docstrings to `__init__.py` files describing each app's purpose (per project rules requiring docstrings on every module).

- **Finding**: The `tools/` app is a utility grab-bag rather than a cohesive app. It contains `app_utils.py` (generic HTTP helpers, error message factories), `db_utils.py` (database lookup helpers), `file_utils.py` (PDS file retrieval), and `opus_middleware.py` (whitespace stripping middleware). These have no views or models of their own but are imported by all other apps.
  **Evidence**: `tools/` app directory contents.
  **Suggestion**: Consider renaming to `common` or `utils` for clarity. Could also be broken into separate focused modules.

---

## 2. Best Practices Alignment

- **Finding (Critical)**: No type annotations anywhere in the codebase. All function parameters and return values lack type hints. This violates the project rule requiring annotations on all functions/methods.
  **Evidence**: Every `views.py`, `models.py`, `app_utils.py`, etc. — zero type annotations found.
  **Suggestion**: Add type annotations incrementally, starting with public API functions. This is a prerequisite for enabling mypy.

- **Finding (High)**: Heavy raw SQL string concatenation throughout `cart/views.py`, `metadata/views.py`, `results/views.py`, `search/views.py`, and `tools/file_utils.py`. SQL strings are built using manual `+=` with `connection.ops.quote_name()`. While parameterized values are used for user inputs (preventing SQL injection), the approach is error-prone, hard to read, and difficult to maintain.
  **Evidence**: `cart/views.py` `_get_download_info()` (~200 lines of SQL construction, lines 814–1073), `search/views.py` `construct_query_string()` (lines 1334–1509), `results/views.py` `get_search_results_chunk()` (lines 1253–1713).
  **Suggestion**: Consider using Django's ORM more extensively, or at minimum extract SQL building into dedicated query-builder functions. For complex queries, consider using a SQL builder library or raw SQL in separate `.sql` files.

- **Finding (High)**: Bare `except:` clauses (without specifying exception type) appear in multiple places. This catches all exceptions including `SystemExit` and `KeyboardInterrupt`.
  **Evidence**: `cart/views.py` line 367 (`except:`), `app_utils.py` line 99 (`except:`), `app_utils.py` lines 189, 201 (`except:`), multiple places in `ui/views.py`.
  **Suggestion**: Replace bare `except:` with specific exception types (e.g., `except ValueError:`, `except Exception:`).

- **Finding (Medium)**: The `settings` module is imported as a bare module name (`import settings`) rather than using Django's standard `from django.conf import settings`. This relies on non-standard `PYTHONPATH` configuration.
  **Evidence**: Every `views.py` file uses `import settings`.
  **Suggestion**: Migrate to `from django.conf import settings` for standard Django compatibility.

- **Finding (Medium)**: Several functions shadow Python built-in names. `id` is used as a database column name (though Django forces this), `filter_` appears (correctly suffixed), but `format` is used as a variable name in `cart/views.py` line 134 (`info['format'] = ...`), and `type` is used frequently.
  **Evidence**: `cart/views.py` line 134, various model fields.
  **Suggestion**: Audit for built-in shadowing per project rules. Rename where possible.

- **Finding (Medium)**: The `from __future__ import unicode_literals` import in `dictionary/models.py` is a Python 2 compatibility artifact that should be removed for Python 3.10+.
  **Evidence**: `dictionary/models.py` line 8.
  **Suggestion**: Remove Python 2 compatibility imports.

- **Finding (Medium)**: Functions with many positional parameters exist. `get_search_results_chunk()` has 12+ parameters. `api_create_download()` has mixed positional/keyword parameters.
  **Evidence**: `results/views.py` `get_search_results_chunk()` (lines 1253–1262).
  **Suggestion**: Use keyword-only parameters (after `*`) per project rules limiting positional parameters to 3.

- **Finding (Low)**: Import ordering is inconsistent. Some files mix Django imports with stdlib imports, and third-party imports are not always cleanly separated with blank lines.
  **Evidence**: `help/views.py` has `import base64`, `import mistune`, `import qrcode` interleaved. `search/forms.py` has `import settings` before local imports.
  **Suggestion**: Enforce three-group import ordering with ruff/isort: stdlib, third-party, local.

- **Finding (Low)**: The `throw_random_http404_error()` and `throw_random_http500_error()` debugging functions are called in production code paths. While they default to 0% probability, their presence adds noise to every API handler and makes code harder to read.
  **Evidence**: Every API function checks `throw_random_http404_error()` and `throw_random_http500_error()` inline.
  **Suggestion**: Consider removing these from production code or moving them to a testing/middleware layer that can be toggled.

---

## 3. Types and Static Checks

- **Finding (Critical)**: Zero type annotations across the entire analyzed codebase. No `py.typed` marker. No mypy configuration visible.
  **Evidence**: All source files lack type annotations.
  **Suggestion**: This is a critical gap per project rules. Begin annotating public API functions, model methods, and utility functions.

- **Finding (High)**: No evidence of ruff or mypy configuration in the analyzed directories. The project rules reference `pyproject.toml` for ruff configuration, but it was not found in the analyzed scope.
  **Evidence**: No lint/type-check configuration files in analyzed directories.
  **Suggestion**: Set up ruff and mypy, run them against the codebase, and fix violations incrementally.

- **Finding (High)**: Most functions lack docstrings that meet the Google style standard. Many have short one-line descriptions but omit `Parameters:`, `Returns:`, and `Raises:` sections. Some functions have no docstring at all (e.g., most private functions in `search/views.py`).
  **Evidence**: `_get_download_info()` in `cart/views.py` has a detailed docstring; `_add_to_cart_table()` has a brief one. `_remove_from_cart_table()`, `_edit_cart_range()`, `_edit_cart_addall()` have minimal one-line docstrings. Most helper functions in `tools/app_utils.py` have brief docstrings.
  **Suggestion**: Expand docstrings to include `Parameters:`, `Returns:`, `Raises:` sections per project rules.

---

## 4. Testing

- **Finding (High)**: The unit tests in `apps/` (e.g., `test_cart.py`, `test_help.py`, `test_metadata.py`, `test_results.py`, `test_ui.py`) are extremely narrow — they only test null `META` and null `GET` edge cases (i.e., verifying that `Http404` is raised when no request is provided). They do not test any actual business logic, data processing, or happy paths.
  **Evidence**: `cart/test_cart.py` — all 14 tests check only "no META" and "no GET" scenarios. `help/test_help.py` — all 16 tests are identical null-request checks. `metadata/test_metadata.py` — same pattern. `results/test_results.py` has null-request tests plus `get_triggered_tables` tests.
  **Suggestion**: Add comprehensive unit tests for business logic: cart operations (add, remove, range, reset), download creation, metadata retrieval, search parameter parsing, result chunking, etc. Current tests provide almost no coverage of actual functionality.

- **Finding (Medium)**: The integration tests in `test_api/` are more thorough. They use `ApiTestHelper` to make full HTTP requests and compare responses (JSON, HTML, CSV) against stored reference files in `test_api/responses/` (347 files). However, they rely on a live database with specific test data, making them integration tests rather than isolated unit tests.
  **Evidence**: `test_api/api_test_helper.py`, `test_api/responses/` (286 JSON, 43 HTML, 18 CSV files).
  **Suggestion**: These are valuable but slow. Consider also adding fast, isolated unit tests using mocks.

- **Finding (Medium)**: Test classes use `unittest.TestCase` directly instead of `django.test.TestCase`, which means they don't get Django's transaction isolation. `results/test_results.py` manually deletes from `user_searches` and drops cache tables in `setUp`/`tearDown`.
  **Evidence**: `results/test_results.py` lines 31–53 (`_empty_user_searches` method).
  **Suggestion**: Use `django.test.TransactionTestCase` or `django.test.TestCase` for proper test isolation.

- **Finding (Medium)**: Test class naming violates PEP 8. Classes like `cartTests`, `helpTests`, `resultsTests`, `uiTests`, `fileUtilsTests` use lowercase first letter (should be `CartTests`, `HelpTests`, etc.).
  **Evidence**: All test files in `apps/`.
  **Suggestion**: Rename to TitleCase per Python naming conventions.

- **Finding (Low)**: Tests contain `print()` statements for debugging output, which clutters test output.
  **Evidence**: `results/test_results.py` lines 297–300, `test_file_utils.py` lines 34–38.
  **Suggestion**: Remove print statements or use `logging` / pytest's capsys.

- **Finding (Low)**: `dictionary/tests.py` is empty (only comments), meaning the dictionary app has zero test coverage.
  **Evidence**: `dictionary/tests.py` — only 2 commented-out lines.
  **Suggestion**: Add tests for `get_def_for_tooltip()`.

---

## 5. Performance and Resource Use

- **Finding (High)**: `cart/views.py` `api_create_download()` opens files with `open()` without `with` statements (lines 682, 686), creating a risk of resource leaks if an exception occurs between `open()` and `close()`.
  **Evidence**: `cart/views.py` lines 682 (`manifest_fp = open(...)`) and 686 (`url_fp = open(...)`), closed at lines 781–782.
  **Suggestion**: Use `with` statements for all file operations.

- **Finding (Medium)**: The `_get_download_info()` function in `cart/views.py` executes two separate SQL queries — one for distinct product types and one for aggregated counts. The second query is ~80 lines of hand-built SQL including nested subqueries. This could be slow for large carts.
  **Evidence**: `cart/views.py` lines 814–1073.
  **Suggestion**: Consider combining into a single query or using database views. Profile to determine actual impact.

- **Finding (Medium)**: The `get_search_results_chunk()` function creates and drops temporary MySQL tables on every call (lines 1496–1517, 1642–1651). For high-traffic scenarios, this creates database overhead.
  **Evidence**: `results/views.py` lines 1496–1517.
  **Suggestion**: Consider using subqueries instead of temp tables, or caching results more aggressively.

- **Finding (Medium)**: `_PARAMINFO_CACHE` in `search/views.py` (line 1174) is an unbounded in-memory cache. While the comment says "there aren't that many" entries, there's no eviction policy.
  **Evidence**: `search/views.py` line 1174.
  **Suggestion**: Use `functools.lru_cache` with a `maxsize` or use Django's cache framework.

- **Finding (Low)**: `added = []` list in `api_create_download()` uses `in` for membership checks on every file (line 751), which is O(n). For large downloads with many files, this could be slow.
  **Evidence**: `cart/views.py` line 751.
  **Suggestion**: Use a `set` for O(1) membership testing.

---

## 6. Maintainability and Extensibility

- **Finding (High)**: Tight coupling between apps. `cart/views.py` directly imports from `metadata.views`, `results.views`, `search.views`, `search.models`, `dictionary.models`, and `tools.app_utils`. Similarly, `results/views.py` imports from `metadata.views`, `search.views`, `tools.app_utils`, `tools.db_utils`, and `tools.file_utils`. This creates a web of dependencies making it difficult to modify one app without affecting others.
  **Evidence**: Import statements in `cart/views.py` (lines 36–71), `results/views.py` (lines 46–89), `ui/views.py` (lines 37–68).
  **Suggestion**: Introduce a service layer or clearly defined interfaces between apps. Use Django signals for cross-app notifications where appropriate.

- **Finding (High)**: Error message constants (`HTTP404_NO_REQUEST`, `HTTP404_BAD_OR_MISSING_REQNO`, etc.) are defined as functions in `tools/app_utils.py` and imported individually by every view module. There are ~20 of these. This pattern is verbose and creates long import lists.
  **Evidence**: `cart/views.py` imports 17 error message functions (lines 52–69).
  **Suggestion**: Group error message functions into a class or enum, e.g., `from tools.app_utils import errors` then `errors.no_request(...)`.

- **Finding (Medium)**: The `enter_api_call` / `exit_api_call` pattern is manually applied to every API function. This is boilerplate that could be replaced with a decorator.
  **Evidence**: Every API function in every `views.py` starts with `api_code = enter_api_call(...)` and ends with `exit_api_call(api_code, ret)`.
  **Suggestion**: Create an `@api_call` decorator that handles timing, logging, and error reporting automatically.

- **Finding (Medium)**: The URL normalization function `api_normalize_url()` in `ui/views.py` is ~825 lines long (lines 740–1590). This is a single monolithic function handling search slugs, qtypes, units, cols, widgets, order, view, browse, pagination, and detail — all in one function with deeply nested logic.
  **Evidence**: `ui/views.py` lines 740–1590.
  **Suggestion**: Break into smaller functions: `_normalize_search_slugs()`, `_normalize_cols()`, `_normalize_widgets()`, `_normalize_order()`, `_normalize_view()`, `_normalize_pagination()`, `_normalize_detail()`.

- **Finding (Low)**: Django's deprecated `extra()` method is used in `metadata/views.py` (lines 533–546) for constructing queries with raw WHERE clauses.
  **Evidence**: `metadata/views.py` lines 533, 537, 545.
  **Suggestion**: Migrate to Django's `annotate()`, `filter()`, or raw SQL as `extra()` is deprecated.

---

## 7. Security and Robustness

- **Finding (Medium)**: `subprocess.check_output(['git', ...])` is called in `app_utils.py` `get_git_version()` (lines 186–197). While `shell=False` is used (safe), the function changes the working directory globally via `os.chdir()` which is not thread-safe.
  **Evidence**: `app_utils.py` lines 179–212.
  **Suggestion**: Use the `cwd` parameter of `subprocess.check_output()` instead of `os.chdir()`.

- **Finding (Medium)**: The `secrets_template.py` file in `dictionary/` contains placeholder credential fields (`DB_USER = 'XXX'`, `DB_PASSWORD = 'XXX'`). While this is a template, the naming doesn't make it obvious that this shouldn't be filled in and committed.
  **Evidence**: `dictionary/secrets_template.py`.
  **Suggestion**: Add clear comments and ensure the actual `secrets.py` is in `.gitignore`. Consider using environment variables instead.

- **Finding (Low)**: User-supplied file paths are used in archive creation (`cart/views.py` `api_create_download()`). While the paths come from the database (not directly from user input), there's no explicit validation that the paths don't traverse outside expected directories.
  **Evidence**: `cart/views.py` lines 760–764.
  **Suggestion**: Add explicit path validation before including files in archives.

- **Finding (Low)**: The `StripWhitespaceMiddleware` in `tools/opus_middleware.py` modifies response content using regex on every text response. This could mask HTML rendering issues and adds processing overhead.
  **Evidence**: `tools/opus_middleware.py` lines 17–44.
  **Suggestion**: Consider whether this middleware is still needed with modern frontend tooling.

---

## 8. Dependencies and Tooling

- **Finding (High)**: Dependencies are imported but no `requirements.txt` or `pyproject.toml` was found in the analyzed scope. Third-party dependencies include `django`, `hurry.filesize`, `mistune`, `pdfkit`, `qrcode`, `yaml` (PyYAML), `pdsfile`, `opus_support`, `regex`, `PIL` (Pillow). These should be pinned.
  **Evidence**: Import statements across all source files.
  **Suggestion**: Create or verify a `requirements.txt` / `pyproject.toml` with pinned dependency versions.

- **Finding (Medium)**: The `opus_support` module is imported in many files but is not part of the analyzed directories. It provides critical functions (`parse_form_type`, `format_unit_value`, `convert_to_default_unit`, etc.). Its location and maintenance status is unclear from this analysis.
  **Evidence**: Imports in `metadata/views.py`, `search/views.py`, `results/views.py`, `ui/views.py`, `paraminfo/models.py`.
  **Suggestion**: Ensure `opus_support` is well-documented and tested.

- **Finding (Low)**: The project uses `re_path` with regex patterns for URL routing. Django 4.0+ recommends `path()` with converters for simple routes and reserves `re_path` for complex patterns.
  **Evidence**: All `urls.py` files use `re_path`.
  **Suggestion**: Migrate simple routes to `path()`. Keep `re_path` only for patterns that truly need regex.

---

## 9. Technical Debt and Risk

- **Finding (Critical)**: The `search/models.py` file is enormous (700K+ characters). This is likely an auto-generated models file containing hundreds of Django model classes (one per database table). This is extremely difficult to maintain.
  **Evidence**: `search/models.py` exceeds the 100K character read limit.
  **Suggestion**: Split into a `models/` package with separate files for each logical group of models (e.g., `obs_general.py`, `obs_pds.py`, `mult_tables.py`, etc.).

- **Finding (High)**: The `ParamInfo` model in `paraminfo/models.py` uses `__unicode__` (line 48), a Python 2 method. In Python 3, this should be `__str__`.
  **Evidence**: `paraminfo/models.py` line 48.
  **Suggestion**: Rename to `__str__`.

- **Finding (High)**: Multiple "backwards compatibility" code paths exist throughout the codebase. These include support for `ring_obs_id` (old format observation IDs), old slug names, old URL formats, and the `metadata_v2` API endpoint. The project rules state "NEVER include backwards-compatibility code unless explicitly requested."
  **Evidence**: `results/views.py` lines 486–491, 808–811, 930–937; `results/urls.py` line 34; `ui/views.py` `api_normalize_url()` has extensive old-slug handling.
  **Suggestion**: Assess whether old-format support is still needed. If it can be dropped, remove the compatibility code to simplify the codebase significantly.

- **Finding (Medium)**: TODO/FIXME/XXX comments exist. `ui/views.py` contains `XXX` comments (lines 343, 527, 649, 689, 1647, 1697) and `TODOPDS4` comments (lines 689, 691). `results/views.py` has `# Bakwards compatibility` (typo, line 268).
  **Evidence**: Grep for XXX/TODO/TODOPDS4 in source files.
  **Suggestion**: Convert actionable items to GitHub issues. Fix typos. Remove or resolve stale comments.

- **Finding (Medium)**: Django models use `managed = False` (e.g., `Cart`, `Contexts`, `Definitions`), meaning Django cannot create or modify these tables. This is typical for legacy databases but prevents using Django migrations.
  **Evidence**: `cart/models.py` line 13, `dictionary/models.py` lines 21, 33.
  **Suggestion**: Document the schema management approach. Consider whether migration to managed models is feasible.

- **Finding (Low)**: The `cart/models.py` file starts with a comment "# this is not being used" (line 1), yet the `Cart` model is actively imported and used by `cart/views.py`, `metadata/views.py`, and `ui/views.py`.
  **Evidence**: `cart/models.py` line 1.
  **Suggestion**: Remove the misleading comment or clarify what it means (perhaps only the Django ORM operations aren't used, with raw SQL being preferred).

---

## Template Analysis

- **Finding (Low)**: The Django widget templates in `opus/application/templates/django/forms/widgets/` override Django's default form rendering. The `input.html`, `input_option.html`, and `multiple_input.html` templates are minimal customizations. These should be documented to explain why the overrides are necessary.
  **Evidence**: `templates/django/forms/widgets/` — 3 template files.
  **Suggestion**: Add comments explaining the purpose of each override.

- **Finding (Low)**: The `ui/templatetags/multilines_template_tags.py` modifies Django's internal `base.tag_re` regex at import time to enable multi-line template tags. This is a fragile monkey-patch that could break on Django upgrades.
  **Evidence**: `ui/templatetags/multilines_template_tags.py` lines 1–4.
  **Suggestion**: Document the Django version dependency. Consider alternatives or submit a Django feature request.

---

## Recommended Priorities

1. **Split oversized files**: Break `search/models.py`, `search/views.py`, `results/views.py`, `cart/views.py`, `ui/views.py`, and `search/test_search.py` into smaller, focused modules. This is the single highest-impact change for maintainability.

2. **Add type annotations**: Begin annotating public API functions, model methods, and utility functions. Enable mypy with basic strictness and fix errors incrementally.

3. **Improve test coverage**: The current unit tests only cover null-request edge cases. Add tests for actual business logic: cart operations, search parameter parsing, result retrieval, metadata lookups, URL normalization, etc.

4. **Refactor raw SQL**: Extract SQL string-building into dedicated query-builder classes or functions. Consider migrating simpler queries to Django ORM.

5. **Remove dead code**: Delete all commented-out code in `dictionary/admin.py`, `dictionary/views.py`, `dictionary/urls.py`. Remove the empty `dictionary/tests.py` placeholder or add real tests.

6. **Modernize Python idioms**: Replace bare `except:` with specific types, remove Python 2 artifacts (`__unicode__`, `from __future__ import unicode_literals`), fix `os.chdir()` thread-safety issue, use `with` statements for file operations, use `set` for membership checks.

7. **Reduce boilerplate**: Create an `@api_call` decorator to replace the manual `enter_api_call`/`exit_api_call` pattern. Group error message constants into a class.

8. **Break up `api_normalize_url()`**: At 825 lines, this single function handles too many concerns. Split into 6–7 focused helper functions.

9. **Establish linting and formatting**: Configure ruff and mypy, add them to CI, and enforce on all new code.

10. **Assess backwards compatibility burden**: Determine whether old `ring_obs_id` format, old slugs, and `metadata_v2` endpoints are still needed. Removing them would significantly simplify the codebase.

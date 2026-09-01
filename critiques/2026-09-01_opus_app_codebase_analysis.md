# Codebase analysis: `src/opus_app/` and `src/opus_log_analyzer/`

**Date:** 2026-09-01
**Tree:** `2bfc2a0e57d4ccb1465775e8e32a7f564d1f2bb1` (branch `pr-24-merge-to-main`)
**Scope:** `src/opus_app/` (all apps, `settings.py`, `urls.py`, `wsgi.py`, and templates
where they bear on the Python) and `src/opus_log_analyzer/`, with `tests/`,
`import_tests/` and `integration_tests/` read as context on those two packages.
`src/opus_app/apps/search/models.py` is a generated file: its generator and its
integration are assessed, its 12,093 lines are not.
**Out of scope (other reviewers):** `src/opus_import/`, `src/opus_support/`,
`src/opus_config/`, and the static JS/CSS except at the Python/template boundary.
**Method:** source reading, plus read-only `ruff`, `mypy`, `vulture`, `pytest --cov`
and targeted Python reproductions. Every count below was measured at this tree; where
a number could not be measured it is omitted rather than estimated.

---

## Summary

This is a well-maintained tree with an unusually high standard of *explanation*. The
tooling is comprehensive and green (ruff clean, `ruff format` clean on 254 files, mypy
strict with no module-level suppression, bandit/vulture/pyroma all wired into CI), and
`apps/tools/sql_builder.py` is a genuinely exemplary piece of work. The comment and
docstring discipline is the best I have seen in a codebase of this age: `pyproject.toml`
justifies every floor and every skip and tells you the command that regenerates the
figure, and `integration_tests/conftest.py` closes a database-destruction hazard with a
session-wide collection hook and explains exactly why.

Against that, three things dominate. **First, the view layer is untested by anything
that can run without the PDS holdings**: `pytest` covers 0% of `search/views.py` (806
statements), `ui/views.py` (890), `results/views.py` (754), `cart/views.py` (633),
`metadata/views.py` (345), `help/views.py` (95), `search/forms.py` (57),
`tools/file_utils.py` (145) and `tools/db_utils.py` (37) — 3,762 statements at zero.
**Second, the view layer is where the structural debt lives**: `api_normalize_url` is
1,028 lines with 197 branch nodes in one function, and five modules exceed the 1,000-line
limit `.cursor/rules/python.mdc` §2 states as ALWAYS. **Third, several unauthenticated
inputs reach code that is not defensive about them** — four confirmed paths turn a
malformed query string into an HTTP 500, one public download parameter does the opposite
of what it says, and a module-level cache grows without bound from attacker-chosen keys.

Top three priorities: close the query-string-to-500 paths and the `_PARAMINFO_CACHE`
growth (§7); give the view layer holdings-free tests (§4); split `api_normalize_url` and
`url_to_search_params` (§1).

---

## 1. Structure and layout

- **Finding**: Five modules exceed the 1,000-line ceiling. **Evidence** (measured,
  `wc -l`): `apps/ui/views.py` 2,278; `apps/search/views.py` 2,222;
  `apps/results/views.py` 2,128; `apps/cart/views.py` 1,839; `apps/metadata/views.py`
  1,085. **Severity: medium.** This conflicts with `.cursor/rules/python.mdc` §2
  ("ALWAYS keep modules under 1000 lines. Split larger modules into a package with
  multiple files"). **Suggestion**: Each already has a natural seam — the `# API
  INTERFACES` / `# SUPPORT ROUTINES` banner comments mark it. Prefer splitting each
  `views.py` into a package (`views/__init__.py` re-exporting, `views/_api.py`,
  `views/_query.py`), starting with `ui`.

- **Finding**: Individual functions are far past any reasonable complexity bound.
  **Evidence** (measured by AST walk; branch count = `If`/`For`/`While`/`And`/`Or`/
  `ExceptHandler`/`IfExp`/`comprehension` nodes):

  | Lines | Branches | Location | Function |
  |------:|---------:|----------|----------|
  | 1,028 | 197 | `apps/ui/views.py:922` | `api_normalize_url` |
  | 570 | 99 | `apps/search/views.py:406` | `url_to_search_params` |
  | 506 | 70 | `apps/results/views.py:1385` | `get_search_results_chunk` |
  | 397 | 52 | `apps/ui/views.py:363` | `api_get_widget` |
  | 345 | 26 | `apps/cart/views.py:1287` | `_edit_cart_range` |
  | 299 | 47 | `apps/cart/views.py:548` | `api_create_download` |
  | 292 | 42 | `apps/ui/views.py:1987` | `_get_menu_labels` |

  **Severity: high.** `api_normalize_url` is a single function longer than most modules
  in this repository; it cannot be reviewed as a unit, and it is the only place the
  URL-migration rules exist. **Suggestion**: `api_normalize_url` already divides itself
  with `### SEARCH`, `### ORDER`, `### VIEW`, `### BROWSE`, `### PAGE and STARTOBS`,
  `### DETAIL` banner comments — lift each into a `_normalize_<section>(original_slugs,
  msg_list) -> list[tuple[str, str]]` helper. That is a mechanical, individually
  testable change.

- **Finding**: The referred-slug resolution block is copy-pasted five times, verbatim
  apart from one argument. **Evidence**: `apps/results/views.py:616-632` and
  `:651-668`; `apps/ui/views.py:2146-2160` and `:2187-2199`;
  `apps/metadata/views.py:933-951`. Each is "look up `referred_slug`, assert non-None,
  overwrite `label`/`label_results`, restore `referred_slug`". **Severity: medium.**
  Conflicts with `python.mdc` §2 ("ALWAYS apply DRY… Place reusable logic in a utility
  module"). **Suggestion**: One `resolve_referred_slug(param_info) -> ParamInfo` in
  `apps/tools/`.

- **Finding**: The `download` / `recyclebin` query-parameter parsing is duplicated four
  times, and the four copies disagree about what to catch. **Evidence**:
  `apps/cart/views.py:230-237` (catches `ValueError`), `:374-390` (catches
  `(TypeError, ValueError)`, with a careful comment about why), `:412-419`
  (`ValueError`), `:497-513` (`ValueError`). **Severity: medium.** **Suggestion**:
  `_int_param(request, name, allowed=(0, 1))` raising `Http400Error`, used by all four.

- **Finding**: The same four `str.replace()` calls that trim a table label appear twice
  in one class. **Evidence**: `apps/paraminfo/models.py:133-136` and `:174-177`.
  **Severity: low.** **Suggestion**: A module-level `_TABLE_LABEL_SUFFIXES` tuple and
  one `_pretty_category_name(label)` helper.

- **Finding**: Dead code that no gate catches. **Evidence, each verified by
  repository-wide grep**:
  - `apps/paraminfo/models.py:63` `__unicode__` — a Python-2-era Django method. Nothing
    calls it (Django 5 uses `__str__`); `integration_tests/.coveragerc:28` even excludes
    `def __unicode__` from the 100% gate, so its deadness is already known.
  - `src/opus_log_analyzer/ip_to_host_converter.py:30` `RESULT_TYPE` and `:200`
    `__testing_update_expiration` — referenced nowhere in `src/`, `tests/`,
    `integration_tests/`, `import_tests/`, `docs/` or the Jinja templates. `vulture`
    reports both at 60% confidence; `[tool.vulture] min_confidence = 70` filters them
    out. (I checked the other 60%-confidence hits: `target_url`,
    `relative_start_time`, `get_fancy_name`, `headers` are used from
    `src/opus_log_analyzer/templates/*.html`, and `session_info.__api_data` is reached
    through its `@pattern_registry.register` decorators — those are true negatives.)
  - `src/opus_log_analyzer/cronjob_utils.py:87` `args.batch = True` — a write-only
    attribute; `_create_argument_parser` defines no `batch` dest and nothing reads it.
    Worse, `cronjob_utils.py:26-27` documents the write as if it had an effect, which
    conflicts with CLAUDE.md's rule that a docstring describes the code as it is.
  - `apps/ui/views.py:138` `str(settings.PREVIEW_GUIDES).strip('"')` — the `.strip('"')`
    is a no-op (measured: input and output are identical for the shipped value).
  - `apps/metadata/views.py:931` `fields.order_by('category_name', 'slug')` — a Django
    QuerySet is immutable, so the returned ordering is discarded and the loop below
    iterates the unordered queryset.

  **Severity: medium** in aggregate. **Suggestion**: Delete the five; consider
  `min_confidence = 60` for vulture with the true negatives moved into
  `vulture_whitelist.py`, which is what that file is for.

- **Finding**: Commented-out code left in place. **Evidence**:
  `apps/tools/opus_middleware.py:61-62`; `apps/ui/views.py:1674-1676`, `:1689-1691`,
  `:1775-1776`, `:1798-1799`, `:1849-1851`; `apps/tools/file_utils.py:335-336`;
  `apps/help/views.py:389`; `apps/search/views.py:972-973`. **Severity: low.**

- **Finding**: A module-level global is neither ALL_CAPS nor underscore-prefixed.
  **Evidence**: `src/opus_log_analyzer/log_entry.py:18` `parts = [...]` (its neighbour
  `LOG_PATTERN` on line 30 is correct). `python.mdc` §1 requires
  `ALL_CAPS_WITH_UNDERSCORES` for module-level constants and a leading `_` for
  module-private globals. Ruff's `N` rules do not check module-level assignment.
  **Severity: low.**

---

## 2. Best practices alignment

*(All references are to `.cursor/rules/python.mdc` unless stated.)*

- **Finding**: A raw query-string value is tested for truth, so `urlonly=0` produces a
  URL-only archive — the opposite of what it asks for. **Evidence**:
  `apps/cart/views.py:569` `url_file_only = request.GET.get('urlonly', 0)` (the default
  is the *int* 0, but a supplied value is always the *string* `'0'`, which is truthy),
  consumed at `:589`, `:629` and `:652`. `docs/api_guide_calls.rst:454-455` documents
  the parameter as `urlonly=<N>`, so `urlonly=0` is the natural spelling for a public
  API user asking for data. `[__]api/download/<opus_id>.<fmt>` is a public route
  (`apps/cart/urls.py`). **Severity: high** — a documented public parameter silently
  returns an archive with no data products. This is exactly the case §1 names ("Do NOT
  rely on truthiness when the intent could be ambiguous"). **Note**: the behavior is
  pinned by `integration_tests/test_api/test_cart_api.py:4065-4067`, which sends
  `urlonly=0` and asserts the archive contains only `data.csv`, `manifest.csv`,
  `urls.txt`. Fixing the code means fixing that test. **Suggestion**: Parse it the way
  `download` and `recyclebin` are parsed a few lines away.

- **Finding**: Three unauthenticated query strings reach unguarded code and produce
  HTTP 500 instead of 400. **Evidence, each verified**:
  1. `apps/search/views.py:2175` `descending = order[0] == '-'` raises `IndexError` on
     an empty order component. Reproduced: `parse_order_slug(',')` and
     `parse_order_slug('time1,,opusid')` both raise `IndexError: string index out of
     range`. Reachable from `api/data.json`, `api/images.json`, `__api/dataimages.json`
     and the cart routes via `url_to_search_params` (`:508`) and
     `get_search_results_chunk` (`apps/results/views.py:1716`). Note that
     `api_normalize_url` handles the same input correctly (`apps/ui/views.py:1695-1696`
     skips an empty component with `if order == '': continue`) — the two parsers
     disagree about the same input.
  2. `apps/search/views.py:1382` `if source == 'search' and (slug[-1] == '1' or …)`
     raises `IndexError` for an empty slug. `QueryDict('=x')` yields `{'': ['x']}`
     (measured), and `url_to_search_params` passes that key straight to
     `get_param_info_by_slug(slug, 'search')` at `:573`. So `?=x` on any search
     endpoint is a 500.
  3. `apps/cart/views.py:729` `int(request.GET.get('hierarchical', 0))` is unguarded, so
     `?hierarchical=x` (or `?hierarchical=`) on `__cart/download.json` is a 500 — while
     `download` and `recyclebin` in the same handler are carefully guarded.

  In all three the `api_view` decorator's `except Exception` (`apps/tools/app_utils.py:499`)
  converts them to a 500 *and* writes a full traceback via `log.exception`.
  **Severity: high** — malformed input from an unauthenticated caller should be a 400,
  and each occurrence writes an ERROR record (see §7 on log rotation).
  **Suggestion**: Guard each at its parse site and raise `Http400Error`; the message
  builders already exist (`http400_bad_limit`, `http400_unknown_slug`, …).

- **Finding**: `except Exception` used where a narrow exception is meant.
  **Evidence**: `apps/ui/views.py:543` and `:547` wrap a plain dictionary lookup
  (`len(selections[param1])`) — §1 says "Prefer explicit membership or presence checks
  over catching exceptions for control flow"; `apps/tools/app_utils.py:201` wraps
  `int(raw_reqno)`, where `(TypeError, ValueError)` is meant;
  `src/opus_log_analyzer/manifest.py:55` swallows every exception from
  `ManifestEntry.from_csv_line`, including programming errors. Three further sites
  (`app_utils.py:300`, `search/views.py:379`, `cart/views.py:804`) are broad but carry
  a stated rationale and a `# nosec`, and I do not count those against the rule.
  **Severity: medium.** Conflicts with §2 ("ALWAYS catch exceptions at the smallest
  granularity possible").

- **Finding**: 14 text-mode `open()` calls omit `encoding=`. **Evidence** (measured,
  binary-mode and `shelve.open` excluded): `apps/help/views.py:185`;
  `apps/cart/views.py:713`, `:719`, `:1829`; `apps/ui/views.py:185`, `:199`;
  `log_analyzer/error_analyzer.py:193`, `:459`; `log_analyzer/opus/html_generator.py:164`;
  `log_analyzer/opus/slug.py:470`; `log_analyzer/manifest.py:95`;
  `log_analyzer/log_entry.py:68`, `:88`; `log_analyzer/log_parser.py:182`.
  **Severity: medium.** Two of these matter concretely. `log_entry.py:68` reads Apache
  access logs, whose User-Agent and Referer fields are attacker-controlled bytes — a
  single malformed sequence raises `UnicodeDecodeError` and aborts the whole nightly
  cron report. `cart/views.py:713`/`:719`/`:1829` write the manifest, URL list and
  `data.csv` that ship inside every user download, using metadata labels from
  `param_info`. `faq.yaml` is currently pure ASCII (measured: 0 non-ASCII bytes in
  21,836), so `help/views.py:185` is latent rather than live. **Suggestion**:
  `encoding='utf-8'` everywhere; add `errors='replace'` on the two log readers, whose
  input is by definition untrusted.

- **Finding**: `csv.writer` is given a file opened without `newline=''`. **Evidence**:
  `apps/cart/views.py:1829-1834`. Python's `csv` documentation states the file object
  "should be opened with `newline=''`"; without it, `csv.writer`'s `\r\n` terminator is
  translated again. `src/opus_log_analyzer/manifest.py:95` does get this right on the
  read side, which makes the omission on the write side an inconsistency rather than an
  unknown. **Severity: low** on POSIX, higher if a Windows deployment is ever wanted
  (the classifiers list `Operating System :: Microsoft :: Windows`).

- **Finding**: A module docstring is a change log. **Evidence**:
  `apps/tools/opus_middleware.py:1-14` — `---- CHANGES ---- / v1.1 - 31st May 2011 /
  Cal Leeming [Simplicity Media Ltd] / Modified regex to…` plus a `---- TODO ----`
  section. **Severity: low**, but it is a direct violation of §4 ("NEVER write a comment
  whose ONLY content is a restatement of the code, a user request, or modification
  history") and of the rule CLAUDE.md singles out as easy to violate. It is also, as far
  as I found, the only surviving instance in the whole scope — the rest of the tree is
  scrupulous about this. **Suggestion**: Replace with a description of what the
  middleware does now; keep the attribution line if it is a licensing requirement.

- **Finding**: `raise Exception(...)` with no custom exception hierarchy.
  **Evidence**: `src/opus_log_analyzer/log_analyzer.py:259`, `:264`;
  `cronjob_utils.py:72`, `:74`, `:120`; and
  `ip_to_host_converter.py:88` (`raise Exception()`, with no message at all, in an
  `@abc.abstractmethod` body where `NotImplementedError` is meant — and where
  `NotImplementedError` would also be picked up by
  `[tool.coverage.report] exclude_lines`). **Severity: medium.** No
  `OpusLogAnalyzerError` base class exists, so a caller cannot distinguish this
  package's failures from anything else. **Suggestion**: Add a base exception class per
  the skill's dimension-2 guidance; switch `ip_to_host_converter.py:88` to
  `NotImplementedError`.

- **Finding**: `import urllib` followed by `urllib.parse.quote_plus`. **Evidence**:
  `apps/results/templatetags/encode_value.py:8` and `:29`. Reproduced in a fresh
  interpreter: `import urllib; urllib.parse` raises `AttributeError: module 'urllib'
  has no attribute 'parse'`. It works today only because Django has already imported
  `urllib.parse` into `sys.modules`. **Severity: medium** (a latent failure that
  depends on import order elsewhere). **Suggestion**: `from urllib.parse import
  quote_plus`.

- **Finding**: Inline imports of stdlib modules. **Evidence**:
  `src/opus_log_analyzer/log_analyzer.py:294` (`import hashlib`) and `:297`
  (`import pickle`). §2 permits inline imports "only to avoid heavy optional
  dependencies (e.g., GUI libraries)"; neither of these is heavy or optional.
  **Severity: low.**

- **Finding**: A 13-parameter function returning a 7-tuple. **Evidence**:
  `apps/results/views.py:1385-1399` — `get_search_results_chunk(request, use_cart,
  ignore_recycle_bin, cols, prepend_cols, append_cols, limit, opus_id, start_obs,
  return_opusids, return_ringobsids, return_cart_states, api_code)`, all
  positional-or-keyword with no `*`, returning
  `(page_no, start_obs, limit, results, all_order, aux_dict, error)`. §2 states that
  "If the leading logical group is larger than about five parameters, make all
  parameters (after `self`) keyword-only" and that the RORO pattern applies "when a
  function takes or returns more than a few related values". The 7-tuple even has a
  named `TypeAlias` (`SearchResultsChunk`, `:116-124`) — the shape is already
  acknowledged. The cost is visible at every call site as `assert page is not None` /
  `assert aux is not None` (`:211`, `:384`, `:880-881`, `:1030`, `:1927`).
  **Severity: medium.** **Suggestion**: A frozen dataclass with the six fields plus
  `error`, or a `Result`/`Error` pair; the asserts then disappear.

---

## 3. Types and static checks

- **Strength**: mypy runs `strict = true` across `src`, `integration_tests`,
  `import_tests`, `tests`, `docs` and `manage.py` with **no** `ignore_errors` entry and
  no module-level blanket ignore; `warn_unused_ignores` is on, so every suppression has
  to keep earning its place. The `[tool.mypy] exclude` list and the single
  `ignore_missing_imports` override each carry a per-entry justification. Ruff is
  configured with the full recommended category set (`E,F,W,I,UP,B,SIM,C4,A,N,PT,RUF`)
  and `[tool.ruff.lint.per-file-ignores]` is empty with an explanation of why an entry
  there is not the way to land failing code. `ruff check` and `ruff format --check`
  both pass over the configured paths at this tree (measured; the only four `ruff check`
  findings repository-wide are in `vulture_whitelist.py`, which is deliberately outside
  `OPUS_RUFF_PATHS`).

- **Finding**: 75 `# type: ignore` comments in scope, and roughly a third of them come
  from one avoidable pattern: attributes are monkey-patched onto Django model instances
  to carry values into templates. **Evidence** (`apps/ui/views.py`): `:314-316` and
  `:2178` set `p.disp_unit`, `p.default_unit`, `p.units` on a `ParamInfo`; `:320` sets
  `p.disp_unit`; `:2105-2109` set `d.collapsed` and `d.show` on a `TableNames`. This is
  also why `apps/search/views.py:1229-1230` has to `copy.copy(pi)` on every
  `get_param_info_by_slug` return ("multiple callers mutate the structure after its
  returned"). **Severity: medium.** **Suggestion**: A small `@dataclass MenuField`
  view-model built from a `ParamInfo`; the ignores, the copies and the aliasing hazard
  all go away together.

- **Finding**: Five sites deliberately ship a known crash under a `# type: ignore`
  rather than fixing it. **Evidence**: `apps/tools/app_utils.py:219-225` (issue #1468 —
  a configuration file writing `log_api_calls = true` reaches `.lower()` on a `bool` and
  raises); `apps/tools/db_utils.py:150-155` (`','.join` over a list containing `None`);
  `apps/tools/dictionary.py:82-86` (`None.startswith`);
  `apps/paraminfo/models.py:138-145` and `:267-272` (`None + str`).
  **Severity: medium.** The honesty here is genuinely admirable — each carries a
  paragraph explaining what fails and why the fix is a design decision rather than a
  cast — but five documented crash paths are still five crash paths, and four of the
  five are reachable from ordinary nullable columns in `param_info`.
  **Suggestion**: Track them as issues (only one, #1468, has a number) and decide the
  display semantics; the comments already contain the analysis.

- **Finding**: `getattr` is used for dynamic dispatch on a configuration-supplied
  string. **Evidence**: `apps/tools/app_utils.py:225`
  `getattr(log, settings.OPUS_LOG_API_CALLS.lower())(s)`. A configuration value that is
  not a logging-method name resolves to some other logger attribute and fails with a
  confusing `TypeError`. **Severity: low** (operator-controlled input).
  **Suggestion**: A `{'debug': log.debug, 'info': log.info, …}` map with a clear error
  for an unknown level; that also fixes #1468 in the same line.

---

## 4. Testing

- **Finding**: The holdings-free suite covers none of the view layer. **Evidence**
  (measured: `OPUS_CONFIG=tests/fixtures/opus_ci.toml pytest --cov=opus_app
  --cov=opus_log_analyzer`, 1,496 tests, 12 s):

  | Module | Statements | Coverage |
  |---|---:|---:|
  | `apps/ui/views.py` | 890 | 0% |
  | `apps/search/views.py` | 806 | 0% |
  | `apps/results/views.py` | 754 | 0% |
  | `apps/cart/views.py` | 633 | 0% |
  | `apps/metadata/views.py` | 345 | 0% |
  | `apps/tools/file_utils.py` | 145 | 0% |
  | `apps/help/views.py` | 95 | 0% |
  | `apps/search/forms.py` | 57 | 0% |
  | `apps/tools/db_utils.py` | 37 | 0% |
  | `apps/paraminfo/models.py` | 106 | 37% |

  3,762 statements at zero. `tests/opus_app/` holds six files (1,627 lines) importing
  only `opus_app.settings` and `opus_app.apps.tools.{app_utils, file_size,
  opus_middleware, sql_builder}` — verified by grep. Reinforcing this,
  `pyproject.toml:262` sets `[tool.coverage.run] source = ["opus_support",
  "opus_config", "opus_import", "opus_log_analyzer"]`, which omits `opus_app`
  altogether, so the GitHub-hosted **Unit Tests** job measures no `opus_app` coverage at
  all. The only gate on this code is `integration_tests/`, which needs the terabyte
  holdings and a completed import and therefore runs on the Node's own hardware
  (`.github/workflows/run-integration.yml`, `runs-on: ${{ matrix.os }}` self-hosted, on
  `pull_request`/`push` to `main` and a nightly cron). **Severity: high.** A change to a
  view module gets ruff, mypy, bandit and vulture, and nothing that executes it, unless
  the contributor has the holdings. **Suggestion**: Add a `tests/opus_app/` tier using
  `RequestFactory` plus fakes for the three `ParamInfo`/`TableNames`/`Definitions`
  lookups — that alone would cover `url_to_search_params`, `parse_order_slug`,
  `get_param_info_by_slug`, `labels_for_slugs` and the whole `api_normalize_url` slug
  machinery, which is where the input-validation bugs in §2 live. All four of those bugs
  are reachable from a pure query string with no database row involved.

- **Finding**: `src/opus_log_analyzer/` (4,158 lines) has effectively no tests.
  **Evidence**: `tests/opus_log_analyzer/test_log_analyzer.py` is 25 lines with one test
  function (it asserts the default `--configuration` module supplies a `Configuration`
  class); `tests/opus_log_analyzer/test_package_data.py` is 55 lines about wheel
  contents. Neither `import_tests/` nor `integration_tests/` references
  `opus_log_analyzer` (verified by grep). Measured per-module coverage from the unit
  suite: `opus/query_handler.py` 13%, `cronjob_utils.py` 14%, `opus/slug.py` 21%,
  `error_analyzer.py` 23%, `opus/html_generator.py` 25%, `log_parser.py` 26%,
  `opus/session_info.py` 31%, `log_entry.py` 34%, `ip_to_host_converter.py` 37%,
  `manifest.py` 43%, `log_analyzer.py` 44%. **Severity: high.** The package is in the
  `[tool.coverage.run] source` list, so its untested statements sit in the denominator
  of `fail_under = 75` — a floor measured by the Import Tests job, which never imports
  it. The floor is honest about the aggregate but protects nothing here specifically.
  This is also where the dead code and the `pytz` bug in §8 survived.
  **Suggestion**: `log_entry.__parse_line`, `manifest.ManifestEntry.from_csv_line`,
  `cronjob_utils.__parse_date_argument` and `opus/slug.py` are all pure functions over
  strings; a few dozen parametrized cases would take this from 13-44% to something
  meaningful with no fixtures at all.

- **Finding**: A golden-response test pins a defect as expected behavior.
  **Evidence**: `integration_tests/test_api/test_cart_api.py:4054-4067` sends
  `?fmt=tar&urlonly=0` and asserts the archive is exactly
  `['data.csv', 'manifest.csv', 'urls.txt']` — the URL-only shape (see §2).
  **Severity: medium**, as a property of the approach rather than of this one test: a
  suite that asserts what the server currently returns will lock in whatever it
  currently returns wrong. **Suggestion**: Where a golden covers a *documented*
  parameter, cross-check the golden against `docs/api_guide_calls.rst` rather than
  against the server.

- **Finding**: The Django template-lexer monkeypatch has no regression test.
  **Evidence**: `apps/ui/templatetags/multilines_template_tags.py` rebinds
  `django.template.base.tag_re` at import; its docstring records three manual checks
  "Verified against Django 5.2.17 (2026-08-23)". A repository-wide grep for
  `multilines` / `tag_re` outside that file finds only `docs/dev_guide_webapp_ui.rst:177`
  — no test. **Severity: medium.** The failure mode is silent: on a Django release that
  changes `tag_re`, every multi-line `{{ … }}` in the templates renders as literal text
  rather than raising. **Suggestion**: Turn the docstring's third check into a test —
  render `'A{{\n  x\n}}B'` through the configured engine and assert `AXB`. It is three
  lines and it converts a prose claim into a gate.

- **Strength**: The suite that does exist is fast, precise and green: 1,496 tests in
  12 seconds. `apps/tools/sql_builder.py` is at 99% (239 statements, 1 partial branch),
  `opus_middleware.py` and `file_size.py` at 100%, `app_utils.py` at 87%,
  `settings.py` at 94%. `pyproject.toml` sets `--strict-markers --strict-config`,
  registers all three markers with descriptions, and sets `filterwarnings = ["error"]`
  with an *empty* suppression list plus a paragraph explaining that the emptiness is
  itself the claim. That is exactly what `.cursor/rules/python_testing.mdc` §4 asks for.

- **Strength (important)**: `DATABASES['default']['TEST']['NAME']` is the live schema
  (`settings.py:374-376`), which would let any `django.test.TestCase` destroy a
  production database. `integration_tests/conftest.py:1-52` closes this with a
  collection hook that refuses `@pytest.mark.django_db`, the `db` /
  `transactional_db` / `live_server` fixtures, a direct `django_db_setup` request, and
  any `SimpleTestCase` subclass — session-wide, not just for that tree, because
  pytest-django decides whether to call `setup_databases` by looking at every collected
  item. The reasoning is written out in full. **But** the guard lives in
  `integration_tests/conftest.py`, which that same docstring notes "is loaded only when
  a command line reaches into this directory, so a bare `pytest` leaves `tests/` free to
  use any of the above." A `@pytest.mark.django_db` test added under `tests/` and run by
  a developer with a production `OPUS_CONFIG` would still reach `setup_databases`.
  **Severity: high** for the residual gap. **Suggestion**: Move the hook to the root
  `tests/conftest.py`, or better, to a session-scoped `conftest.py` at the repository
  root so it covers every invocation.

---

## 5. Performance and resource use

- **Finding**: `api/fields.json` issues roughly three database queries per metadata
  field. **Evidence**: `apps/metadata/views.py:906-1029` loops over every `ParamInfo`
  row and calls `TableNames.objects.get(table_name=f.category_name)` at `:973`,
  `f.body_qualified_label_results()` at `:1017` (another
  `TableNames.objects.get`, `apps/paraminfo/models.py:173`) and
  `f.body_qualified_label()` at `:1018` (a third, `:132`). The endpoint is public,
  `@never_cache` (`:745`), and describes every field when no `slug` is given.
  **Severity: high.** **Suggestion**: One `TableNames.objects.in_bulk` /
  `{t.table_name: t for t in TableNames.objects.all()}` at the top of the loop, or a
  process-level cache like the one `apps/tools/db_utils.py:88` already keeps for mults.

- **Finding**: The search menu re-queries the database per rendered field, from the
  template. **Evidence**: `apps/ui/templates/ui/menu.html:47`, `:96` call
  `{{ p.body_qualified_label }}`; `:60`, `:65`, `:109`, `:118` call
  `{{ p.get_tooltip_results }}` / `{{ p.get_tooltip }}`; `:70` and `:123` call
  `{{ p.get_link_tooltip }}`. Each is a model
  method that issues a `TableNames.objects.get` (`paraminfo/models.py:110`, `:132`,
  `:173`) or a `Definitions.objects.get` (`apps/tools/dictionary.py:77`).
  `apps/ui/templates/ui/add_field.html:40`, `:76` do the same. **Severity: high.**
  **Suggestion**: Resolve labels and tooltips in `_get_menu_labels` against a
  pre-fetched map and pass plain strings to the template; a template should not be able
  to issue a query.

- **Finding**: A per-mult-field query is issued inside a loop even though the values
  were already fetched. **Evidence**: `apps/results/views.py:644` reads
  `result_rows = results.values(*all_param_names)` — one query for the whole row — and
  then `:675` re-executes `results.values(param_info.name)[0][param_info.name]` for
  each MULT field, inside a loop that is itself inside a loop over every category
  table. **Severity: medium.** **Suggestion**: `result_vals[param_info.name]`, which is
  already in hand on line 649.

- **Finding**: A widget's tooltips are one query each. **Evidence**:
  `apps/ui/views.py:659` and `:685` call `get_def_for_tooltip(mult.value, 'MULT_' + …)`
  inside loops over every mult value of the field. For a large mult (targets,
  instruments) that is one `Definitions.objects.get` per checkbox. The same function
  runs `model.objects.filter(...)` five separate times over the one small mult table
  (`:636`, `:648`, `:650`, `:667`, `:675`, `:679`). **Severity: medium.**

- **Finding**: `api_bundles` issues one query per distinct bundle. **Evidence**:
  `apps/help/views.py:131-139` — `MultObsGeneralInstrumentId.objects.values('label')
  .filter(id=d['instrument_id'])` inside a loop over every distinct
  `(instrument_id, bundle_id)` pair; `instrument_name[0]` at `:139` also raises
  `IndexError` if the mult row is missing. **Severity: medium.**

- **Finding**: A linear membership test over a list that can hold every file in a cart
  download. **Evidence**: `apps/cart/views.py:723` `added = []` and `:790`
  `if logical_path not in added:` — quadratic in the number of files. The cart admits
  up to `MAX_SELECTIONS_FOR_DATA_DOWNLOAD = 10000` observations (`settings.py:490`),
  each with several products. `added` is only ever membership-tested and appended.
  **Severity: medium** and a one-word fix. **Suggestion**: `added = set()` /
  `added.add(...)`. `apps/tools/file_utils.py:253` (`if res not in
  results[opus_id][version_name][product_type]`) has the same shape over a smaller list.

- **Finding**: Every access-log file is read wholly into memory as a list of strings.
  **Evidence**: `src/opus_log_analyzer/log_entry.py:69`
  `for log_line in file.readlines():` and `error_analyzer.py:194` likewise. Apache
  access logs are routinely gigabytes, and the parsed entries are accumulated anyway,
  so this doubles peak memory for no benefit. **Severity: medium.**
  **Suggestion**: `for log_line in file:`.

- **Finding**: Importing the settings module opens a network connection and writes a
  key into the cache. **Evidence**: `settings.py:35-40` — `pymemcache.client.base.Client(
  ('127.0.0.1', 11211))` followed by `.set('__test_key__', 'test_val')`, with no
  `connect_timeout`/`timeout`, catching only `ConnectionRefusedError`. A memcached that
  is firewalled rather than refusing blocks the import (and therefore worker startup)
  indefinitely; any other error (`socket.timeout`,
  `MemcacheUnexpectedCloseError`) propagates and fails startup outright. The client is
  never closed. **Severity: medium.** **Suggestion**: Pass a short
  `connect_timeout`, catch `OSError`, and close the probe client.

- **Finding**: A user-supplied regular expression is run against the observation tables
  with no execution-time bound. **Evidence**: `qtype=regex` is a documented public
  q-type (`settings.py:472`); `apps/search/views.py:1691-1693` validates it with a round
  trip to the server (`_valid_regex`, `:1609-1614`) and then builds
  `binary_op(param_column, 'RLIKE', value(value))`. The main search `Select` at
  `apps/search/views.py:1568` is constructed with no `max_execution_time`, unlike the
  string-choices queries at `:300` and `:334`, which do set one.
  **Severity: medium** (catastrophic-backtracking denial of service).
  **Suggestion**: Give the search `Select` a `max_execution_time`; `sql_builder` already
  supports it.

- **Finding**: A negative cache lookup does not prevent the fallback queries it was
  meant to save. **Evidence**: `apps/search/views.py:1298-1299` sets `pi` from
  `_PARAMINFO_CACHE`, which may be `None`; `:1314 if pi:` is then false, and control
  falls through to the `widget` (`:1349`), `qtype` (`:1365`) and `search` (`:1382`)
  fallbacks, each of which issues up to two more `ParamInfo.objects.get` calls, and to
  the `log.error` at `:1402`. A cached miss therefore still costs queries and a log
  line. **Severity: low.**

- **Finding**: `labels_for_slugs` is called twice for the same column list.
  **Evidence**: `apps/results/views.py:246-247` — `labels_for_slugs(cols_to_slug_list(
  cols))` and `labels_for_slugs(cols_to_slug_list(cols), units=False)`, doubling the
  per-slug `TableNames` queries described above. **Severity: low.**

- **Finding**: Module-level mutable state with no locking and no documented
  thread-safety contract. **Evidence**: `apps/search/views.py:1231`
  `_PARAMINFO_CACHE`; `apps/tools/db_utils.py:88` `_PRETTY_MULT_CACHE`;
  `apps/tools/app_utils.py:206-207` `_API_CALL_NUMBER` / `_API_START_TIMES`. The last
  pair is the one where it shows: `_API_CALL_NUMBER += 1` is a read-modify-write, so
  under a threaded WSGI server two concurrent requests can be issued the same api_code,
  and the first `exit_api_call` pops the other's start time, mis-timing the call.
  **Severity: low** (the consequence is a wrong log line, and the size hazard of
  `_PARAMINFO_CACHE` is covered in §7). **Suggestion**: `itertools.count()` for the
  counter, and a sentence in each module docstring stating the thread-safety
  assumption.

---

## 6. Maintainability and extensibility

- **Finding**: A Python `dict` repr is emitted as a JavaScript object literal.
  **Evidence**: `apps/ui/views.py:138` `context['preview_guides'] =
  str(settings.PREVIEW_GUIDES).strip('"')` and
  `apps/ui/templates/ui/header.html:90` `const PREVIEW_GUIDES = {{ preview_guides|safe }}`.
  This works only because the shipped value happens to be a flat `dict[str, str]` whose
  repr is accidentally valid JavaScript (measured). A `None` value emits the token
  `None`, and `True`/`False` emit `True`/`False` — each a `ReferenceError` that kills
  the whole inline `<script>` and stops the OPUS front end initializing. An apostrophe
  in a key changes the quoting style silently. **Severity: medium** and it is squarely
  the Python/template boundary. **Suggestion**: `json.dumps(settings.PREVIEW_GUIDES)`,
  or Django's `json_script` template filter, which is what it exists for. The
  `.strip('"')` is a no-op and should go with it.

- **Finding**: A private Django global is monkey-patched as an import side effect.
  **Evidence**: `apps/ui/templatetags/multilines_template_tags.py:34` rebinds
  `django.template.base.tag_re` with `re.DOTALL` added, relying on the
  DjangoTemplates engine importing every module under an installed app's `templatetags`
  package. **Severity: medium.** The documentation here is outstanding — the module
  states that it must never be `{% load %}`ed, why the import happens anyway, the
  Django version it was verified against, and the three checks that were run — but the
  patch changes template lexing for every template in the process, including
  `django.contrib.admin`'s, and no test guards the assumption (see §4).
  **Suggestion**: Keep it, add the regression test, and add a startup assertion that
  `re.DOTALL in base.tag_re.flags` so a Django upgrade fails loudly rather than
  silently.

- **Finding**: A testing affordance is wired into production request handling.
  **Evidence**: `apps/tools/app_utils.py:173-181` — `get_session_id` returns
  `request.GET.get('__sessionid')` in preference to the real session, unconditionally.
  `integration_tests/test_api/test_cart_api.py:2080-2134` depends on it to drive two
  carts in one process, so the parameter cannot simply be removed without rewriting
  those tests. **Severity: high** (see §7 for the security consequence).
  `docs/dev_guide_webapp_tools.rst:93-95` documents the hazard plainly ("**nothing
  restricts it to a test request**, so any caller can name the session a handler will
  read and write"), which is the right instinct, but documenting a hole does not close
  it. **Suggestion**: Gate it on `settings.DEBUG` or on a dedicated setting the
  integration configuration turns on; the test suite already reads its own
  configuration file.

- **Finding**: User-facing HTML is assembled by string concatenation in Python, with
  escaping applied by hand at each site. **Evidence**: `apps/ui/views.py:1108`,
  `:1140-1144`, `:1154-1160`, `:1260-1265`, `:1860-1877`, `:1925-1942` build the
  `__normalizeurl.json` `msg` payload with `+` and call `escape()` per interpolation;
  `apps/ui/views.py:437-460` builds the mult-group container markup the same way;
  `:700-703` inserts a `selected` attribute by `str.replace` on already-rendered form
  HTML. **Severity: medium.** The current sites are correct as far as I traced them
  (the unescaped interpolations are database-sourced labels and OPUS IDs), but
  correctness rests on every future author remembering. **Suggestion**: Move message
  construction into a small template, or use `django.utils.html.format_html`, which
  escapes its arguments by construction.

- **Finding**: `SearchForm.__init__` reads loop variables after the loop.
  **Evidence**: `apps/search/forms.py:176-182` uses `form_type`, `slug_no_num` and
  `slug` after the `for slug in form_vals` loop at `:63`. An empty `form_vals` raises
  `NameError`; a mapping holding both a STRING and a RANGE slug silently discards the
  string field, depending on iteration order. The docstring at `:47-49` records the
  behavior, so it is deliberate — but it is deliberate fragility.
  `MultiFloatField` (`:26-33`) is an empty `forms.Field` subclass that "adds nothing".
  **Severity: low.**

- **Finding**: A loop variable is rebound from inside its own body.
  **Evidence**: `apps/cart/views.py:761` `for product_type in files_version:` and
  `:766` `product_type = file_data['full_name']`; likewise `:757`
  `for version_name in files[f_opus_id]:` and `:768`
  `version_name = file_data['version_name']`. It happens to be correct because both
  are re-read at the top of each iteration, but it makes the loop very hard to read.
  **Severity: low.**

- **Strength**: The API surface is unusually well organized for a project of this age.
  Every routed handler is wrapped in one decorator (`apps/tools/app_utils.py:430`),
  every error message has a named builder whose `http400_`/`http404_`/`http500_` prefix
  records the status it belongs to (`:618-764`), and each handler's docstring gives its
  URL, its arguments, whether it is PUBLIC or PRIVATE, and a worked example of every
  return format. Reading one handler tells you how to read the next.

---

## 7. Security and robustness

*(References to `.cursor/rules/security.mdc`.)*

- **Finding**: A module-level cache grows without bound from attacker-chosen keys.
  **Evidence**: `apps/search/views.py:1231` `_PARAMINFO_CACHE: dict[Any, Any] = {}`;
  `:1400` `_PARAMINFO_CACHE[key] = None` interns a *negative* result keyed on
  `(slug, source)` where `slug` is a raw query-string key. Nothing evicts. The
  amplifying path is `api_normalize_url`: `apps/ui/views.py:1067` loops over every key
  in the query string and `:1107-1110` appends a message and `continue`s past an
  unknown slug rather than aborting — so one request to
  `/__normalizeurl.json?a1=x&a2=x&…` with distinct unknown keys interns one permanent
  entry per key, up to Django's `DATA_UPLOAD_MAX_NUMBER_FIELDS` (default 1000). The
  route is unauthenticated (`apps/ui/urls.py:24`, mounted at both `^` and `^opus/` by
  `opus_app/urls.py:33-35`). Each unknown slug also writes an ERROR line
  (`apps/search/views.py:1402`). **Severity: high** — a slow memory-exhaustion vector
  against a long-lived worker process, with log amplification attached.
  **Suggestion**: Bound the cache (`functools.lru_cache` on an inner function, or an
  explicit size cap), and stop caching misses keyed on unvalidated input.

- **Finding**: Any caller can read and write any session's cart.
  **Evidence**: `apps/tools/app_utils.py:173-181` `get_session_id` prefers
  `?__sessionid=<S>` over the real session with no validation and no environment gate;
  every cart handler keys on its return value (`apps/cart/views.py:127`, `:223`,
  `:359`, `:490`, `:571`). So `__cart/status.json?__sessionid=X`,
  `__cart/add.json?__sessionid=X`, `__cart/reset.json?__sessionid=X` and
  `__cart/download.json?__sessionid=X` all act on session `X`.
  **Severity: high.** Django session keys are 32 characters of `[a-z0-9]`, so blind
  guessing is infeasible — but the parameter is designed to be put in a URL, and URLs
  leak through Referer headers, browser history and this project's own access logs.
  Separately, because `__sessionid` accepts arbitrary strings, an unauthenticated
  caller can create cart rows under any number of invented session ids, which is an
  unbounded write into the shared `cart` table. A related consequence: the value is
  interpolated into a temporary table name at `apps/cart/views.py:1368`, so a
  `__sessionid` containing anything outside `[A-Za-z0-9_]` raises `SQLIdentifierError`
  from `sql_builder.quote_identifier` and becomes a 500 (the injection itself is
  correctly blocked — see the strength below). **Suggestion**: Honor `__sessionid` only
  when a dedicated setting enables it, and turn that setting on in the integration
  configuration.

- **Finding**: The application log holds at most ~150 KB. **Evidence**:
  `settings.py:288-295` — the `logfile` handler is a `RotatingFileHandler` with
  `maxBytes: 50000` and `backupCount: 2`. Every app logger writes to it at level
  `DEBUG` (`:317-353`). **Severity: medium.** Any burst of errors — including the ones
  the input-validation gaps in §2 make trivially triggerable — rotates the whole history
  away within seconds. This matters more here than usual because `opus_error_analyzer`
  exists specifically to correlate these logs with requests. **Suggestion**: Raise
  `maxBytes` to a realistic size (tens of megabytes) and `backupCount` accordingly, or
  hand rotation to `logrotate` with a `WatchedFileHandler`.

- **Finding**: The Django admin is served on a site with no admin models.
  **Evidence**: `apps/ui/urls.py:19` `re_path(r'^admin/', admin.site.urls)`, mounted
  under both URL prefixes; `INSTALLED_APPS` includes `django.contrib.admin`,
  `auth` and `sessions` (`settings.py:229-234`). `opus_app/urls.py:17-19` itself notes
  that `admin.autodiscover()` is "inert either way, because no app defines an admin
  module". **Severity: medium.** A public `/admin/login/` backed by the `auth_user`
  table `migrate` created, with no rate limiting, is attack surface for nothing in
  return. **Suggestion**: Drop the route and `django.contrib.admin` from
  `INSTALLED_APPS`, or gate the route on `DEBUG`.

- **Finding**: File handles and temporary files leak on the download error path.
  **Evidence**: `apps/cart/views.py:713` and `:719` open the manifest and URL files
  with no context manager and no `try`/`finally`; they are closed at `:824-825` and the
  temporary files removed at `:836-837`. Anything raising in between leaks both handles
  and the open archive and leaves three files on disk. `path.index(settings.
  PDS3_HOLDINGS_DIR)` at `:743` and `:775` raises `ValueError` whenever a configured
  holdings root does not appear in a stored path, and is not guarded. Separately,
  `:649` calls `_create_csv_file(...)` and **discards its return value**, which is the
  500 response `_create_csv_file` produces when the rows cannot be read
  (`:1820-1822`); execution then continues to `:828`/`:832`, where
  `archive_file.write(csv_file_name, …)` raises `FileNotFoundError` because the file
  was never written — converting a clean 500 into a crash with leaked handles.
  **Severity: medium.** **Suggestion**: `contextlib.ExitStack` around the whole assembly
  block; check `_create_csv_file`'s return.

- **Finding**: A user-supplied string of unbounded length is fed to a QR encoder.
  **Evidence**: `apps/help/views.py:287-288` read `?searchurl=` and `?stateurl=`;
  `:301` `qr.make(fit=True)` raises `qrcode.exceptions.DataOverflowError` past QR
  version 40's capacity (~2,953 bytes). OPUS bookmark URLs carrying many columns and
  widgets are long, so this is reachable by legitimate use, not only by attack, and it
  is a 500. **Severity: medium.** **Suggestion**: Catch `DataOverflowError` and render
  the page without that QR code.

- **Strength (significant)**: `apps/tools/sql_builder.py` is the best-designed module
  in the scope and closes the injection risk properly. Identifiers go through
  `quote_identifier` (`:100-115`), which *validates* against `\A[A-Za-z0-9_]+\Z`
  before quoting — and the docstring explains why validation and not quoting is what
  closes the hole ("Django's `quote_name` wraps a name in backticks but does not escape
  a backtick *inside* it"). Values are always `%s` parameters; the two literal-rendered
  numbers (`LIMIT`/`OFFSET` at `:489-507` and `MAX_EXECUTION_TIME` at `:430-434`) are
  `isinstance(..., int)`-checked with the reasoning written out; operators are
  restricted to a frozenset (`:79`, enforced at `:228`); join kinds to two values
  (`:358`); `columns_equal` refuses to take parameters at all (`:240-241`), which is
  what makes a join condition structurally safe. Parameters are emitted in placeholder
  order by construction. The three `# nosec B608` markers each name what is
  interpolated and why. This is how raw SQL should be done.

- **Strength**: The escaping boundary is thought through where it matters.
  `wrap_http500_string` (`apps/tools/app_utils.py:723-742`) escapes, and its docstring
  explains why it is the *only* place that escapes — the 400/404 messages go through
  templates and would be double-escaped otherwise. `hashlib.md5(...,
  usedforsecurity=False)` is used correctly at `apps/search/views.py:253`, `:1111`,
  `:1130`, `:1149`, `:1155`. Log calls use `%r` on request-supplied scalars with a
  written rationale about CRLF log forging (`apps/cart/views.py:382-388`) — that is a
  level of care I rarely see.

---

## 8. Dependencies and tooling

- **Finding**: The declared `rms-pdsfile` floor does not satisfy the project's own type
  gate. **Evidence**: `pyproject.toml:29` declares `rms-pdsfile>=0.0.18`, and
  `[[tool.mypy.overrides]]` (`:229-231`) deliberately has no `pdsfile.*` entry ("Every
  package the repository imports either has an entry here or is checked"). But every CI
  job installs the package from a git branch instead —
  `.github/workflows/run-tests.yml:102`, `:196`, `:296`, `:377` and
  `run-integration.yml:141` all run
  `pip install "rms-pdsfile @ git+https://github.com/SETI/rms-pdsfile@rewrite"`.
  Measured against PyPI's 0.0.18 (which ships no `py.typed`), `mypy src
  integration_tests import_tests tests docs manage.py` reports **20 `import-untyped`
  errors in 14 files**, two of them in scope
  (`src/opus_app/apps/tools/file_utils.py:21`). **Severity: high.** A contributor who
  follows `pip install -e ".[dev]"` cannot reproduce the green mypy gate, and the wheel
  published to PyPI declares a dependency that does not satisfy the project's own
  checks. **Suggestion**: Either floor `rms-pdsfile` at the first release that ships
  `py.typed`, or add a documented `ignore_missing_imports` entry for `pdsfile.*` until
  it does — and say in `CONTRIBUTING.md` that the git install is required meanwhile.

- **Finding**: `pytz` is used in place of stdlib `zoneinfo`, and used the way pytz's own
  documentation forbids. **Evidence**: `src/opus_log_analyzer/cronjob_utils.py:18`
  `DEFAULT_TIMEZONE = pytz.timezone('US/Pacific')`, then `:106-108` and `:114-119`
  construct `datetime.datetime(tzinfo=DEFAULT_TIMEZONE, …)`. Measured:
  `datetime(tzinfo=TZ, year=2026, month=7, day=15)` carries a UTC offset of **−07:53
  (LMT)** rather than −07:00 (PDT) — a 53-minute error, because the constructor takes
  the zone's first historical offset instead of the one in force on that date. The
  correct pytz call is `TZ.localize(...)`; the correct modern call is
  `ZoneInfo('US/Pacific')`, which has none of this behavior and needs no dependency
  (the project requires Python ≥3.12). Today the affected values are only used for
  `strftime` on file patterns and for `.day`/`.month`/`.year`, so the impact is latent
  rather than live — but `run_date` is also *returned* and mixed with the correctly
  aware `today` from `:93`. `types-pytz` is carried in the dev extras for this one
  module. **Severity: medium.** **Suggestion**: Replace `pytz` with
  `zoneinfo.ZoneInfo` and drop both dependencies.

- **Finding**: `requires-python` is open-ended past what is tested or classified.
  **Evidence**: `pyproject.toml:10` `requires-python = ">=3.12"`; the classifiers list
  only 3.12 and 3.13 (`:50-51`); the Unit Tests matrix is `["3.12", "3.13"]`
  (`run-tests.yml:157`). Python 3.14 satisfies the constraint and is neither tested nor
  claimed. **Severity: low.** **Suggestion**: `>=3.12,<3.14` until 3.14 is added to the
  matrix.

- **Strength**: The tooling story is thorough and coherent. `scripts/run-all-checks.sh`
  runs ruff check, ruff format, mypy, pytest, pyroma, bandit, vulture, Sphinx and
  PyMarkdown, and the CI lint job runs the same set over the same path list
  (`OPUS_RUFF_PATHS` / `MYPY_PATHS` are the same string). `[tool.bandit] skips` holds a
  single entry (`B101`) with a paragraph explaining why a per-line `# nosec` is not the
  answer for it and giving the command that regenerates what it is holding back;
  everything else is a per-line `# nosec <ID> - <reason>`. `[tool.setuptools.package-data]`
  is preceded by a package-data audit that gives the command to re-derive the wheel
  inventory and explains the two categories of file that are in it deliberately. This
  "state the command that regenerates the claim rather than writing the number down" is
  a discipline worth keeping.

---

## 9. Technical debt and risk

- **Finding**: Three of the log analyzer's four documented modes cannot run.
  **Evidence**: `src/opus_log_analyzer/log_analyzer.py:245` `elif args.glob:` — no
  `--glob` argument and no `glob` dest is defined anywhere in
  `_create_argument_parser` (`:45-222`), so `--summary`, `--realtime`/`-i`/`-r` and
  `--xxfake-realtime` all raise `AttributeError` before doing any work. `--summary` and
  `--realtime` are advertised in `--help` (`:91`, `:108`). The module docstring
  (`:8-9`) and `main`'s `Raises:` (`:231-234`) both state this plainly.
  **Severity: medium.** Honest documentation of a broken feature is much better than
  silence, but the feature is still broken and still advertised.
  **Suggestion**: Either restore the missing argument or delete the three modes and
  their `--help` entries; `RunType`, `run_summary` and `run_realtime` go with them.

- **Finding**: A concentration of unlinked `XXX` markers in one module.
  **Evidence**: `apps/ui/views.py:372` ("addlink=true|false XXX???"), `:415`, `:454`,
  `:502` ("XXX Really should throw an error of some kind"), `:660`, `:830`, `:2049`
  ("XXX Needs api_code to report errors"), `:2114` ("XXX This really shouldn't be
  here!!"), plus `:871`/`:874` `TODOPDS4`. **Severity: low.** All eight are in the one
  module that is also the largest and the least covered. **Suggestion**: Triage into
  issues or delete; `python.mdc` §4 allows an issue number as a reference once the
  comment already says what the behavior is.

- **Finding**: An `atexit` handler can raise. **Evidence**:
  `src/opus_log_analyzer/ip_to_host_converter.py:194` `min(expiration for (_, expiration)
  in self._database.values())` with no `default=`, inside `__close`, registered at
  `:147`. On a first run with `--xxdns-cache` against an empty shelf this raises
  `ValueError` at interpreter exit. The docstring at `:190-192` records it.
  **Severity: low** (a hidden flag). **Suggestion**: `default=None` and skip the field
  when there is nothing to report.

- **Finding**: Two callers rely on an unenforced trailing-slash convention for
  configured directories. **Evidence**: `apps/cart/views.py:644-647` builds four paths
  by `settings.TAR_FILE_PATH + …` / `settings.MANIFEST_FILE_PATH + …`;
  `src/opus_config/config.py:110` documents that these "ha[ve] to end with a path
  separator", but nothing validates it, so a configuration missing the slash writes
  archives into a sibling directory under a mangled name. A related inconsistency:
  `apps/tools/file_utils.py:228`, `:230` and `:232` join with `.rstrip('/') + '/'` while
  `:349` joins the *same* setting with `.strip('/')` and no separator — the two agree
  only because the shipped value has no leading slash. **Severity: low.**
  **Suggestion**: `pathlib.Path` at the call sites, which makes the convention
  unnecessary.

---

## 10. Packaging and distribution

Little to report, which is itself the finding: this dimension is in good shape.

- **Strength**: `pyproject.toml` carries a complete `[project]` table — description,
  readme, `requires-python`, license, authors/maintainers, keywords, the full classifier
  set and a five-entry `[project.urls]`. Version is single-sourced through
  `setuptools_scm` with `write_to = "src/opus_config/_version.py"` (git-ignored, and
  excluded from ruff and mypy for that reason, each with a stated justification).
  `py.typed` is present in both `src/opus_app/` and `src/opus_log_analyzer/` and shipped
  via `[tool.setuptools.package-data] "*" = ["py.typed"]`. `pyroma` runs in CI
  (`run-tests.yml`, Package job). `[tool.setuptools.packages.find] namespaces = false`
  is set with an explanation of what it prevents.

- **Finding**: The wheel ships developer `README.md` files from inside the Django app.
  **Evidence**: `src/opus_app/apps/README.md` and eight per-app `README.md` files;
  `pyproject.toml`'s package-data audit acknowledges this ("kept because the
  alternatives are worse, not because they earn their place") and states the measurement
  that showed `exclude-package-data` cannot reach them. **Severity: low**, and already
  reasoned about; I record it only because the audit invites re-checking.

---

## What is notably strong

Worth naming specifically, because it is unusual:

1. **`apps/tools/sql_builder.py`** — identifier validation before quoting, values always
   parameterized, a closed operator set, `columns_equal` that structurally cannot take
   a parameter, and a module docstring that explains the two literal-rendered exceptions
   and why the driver's behavior is the wrong reason to rely on. 99% covered by a
   448-line unit test.
2. **`api_view`** (`apps/tools/app_utils.py:430-507`) — one decorator owns
   entry/exit logging, fault injection, `Http400Error` → 400, and everything else → 500,
   *and* deliberately re-raises the four exceptions Django's own handler answers
   specifically, with the reasoning for each written down including why
   `MultiPartParserError` is absent.
3. **`integration_tests/conftest.py`** — a session-wide refusal of every route to
   `setup_databases`, closing a hazard that would otherwise destroy a production schema,
   with the full argument written out.
4. **Configuration that explains itself.** `pyproject.toml` justifies every dependency
   floor (the `rms-julian>=3.0.2` note, the `ruff>=0.9` formatter-style note, the
   `pytest>=9.0.3` CVE note), states what an empty list *claims*
   (`filterwarnings`, `per-file-ignores`), and repeatedly gives the command that
   regenerates a figure rather than writing the figure down.
5. **Honest recording of latent faults.** Five sites ship a `# type: ignore` with a
   paragraph saying exactly what will crash and why the fix is a design decision. I
   would rather have this than a cast that hides it — and it made this review much
   faster.
6. **Docstrings that would let you write a black-box test.** Every API handler gives its
   URL, arguments, PUBLIC/PRIVATE status and a sample of each return format;
   `multilines_template_tags.py` names the Django version it was verified against and
   the three checks that were run.

---

## Recommended priorities

1. **Close the unauthenticated-input holes.** In one pass: guard `parse_order_slug`
   against an empty component (`apps/search/views.py:2175`), guard the empty slug in
   `get_param_info_by_slug` (`:1382`), guard `hierarchical` (`apps/cart/views.py:729`),
   parse `urlonly` instead of testing it for truth (`:569`, and update
   `test_cart_api.py:4065-4067`), and bound `_PARAMINFO_CACHE` so an unknown slug cannot
   be interned forever (`apps/search/views.py:1231`, `:1400`). Then raise the log
   handler's `maxBytes` (`settings.py:292`). Each is a few lines; together they remove
   four 500s, one wrong public-API answer and one memory-exhaustion vector.
2. **Give the view layer holdings-free tests.** 3,762 statements are at 0% under
   `pytest`, and `opus_app` is not even in `[tool.coverage.run] source`. Start with the
   pure query-string paths — `url_to_search_params`, `parse_order_slug`,
   `get_param_info_by_slug`, `labels_for_slugs` — which need only a `RequestFactory` and
   fakes for three model lookups, and which are exactly where priority 1's bugs live.
   Add `opus_app` to the coverage source list once there is something to measure.
3. **Gate `__sessionid`, or remove it.** It is the one finding where a documented
   decision is actively unsafe in production, and the fix is a settings check plus one
   line in the integration configuration.
4. **Split `api_normalize_url` and `url_to_search_params`.** 1,028 lines / 197 branches
   and 570 / 99 respectively. The section banners already mark the seams; do it as
   pure extraction, with the golden suite as the safety net, before anything else in
   those two functions changes.
5. **Fix the dependency and timezone mismatches.** Make `rms-pdsfile`'s declared floor
   the one that satisfies mypy, and replace `pytz` with `zoneinfo` (dropping the
   `types-pytz` stub with it) — both are small, both remove a class of surprise, and the
   second fixes a measured 53-minute offset error.
6. **Sweep the small stuff.** The 14 `encoding=`-less `open()` calls, `newline=''` on
   the CSV writer, `import urllib.parse`, `added` as a set, the five dead names, the
   `PREVIEW_GUIDES` `json.dumps`, and the `opus_middleware.py` change-log docstring.
   None is individually urgent; together they are an afternoon and they close every
   remaining rule violation I found.

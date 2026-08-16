# Codebase analysis – reference

Use this when you need concrete examples for a dimension or wording guidance.

## Example findings (by dimension)

**Structure**
- **Finding**: Single module `utils.py` is 1,200 lines and mixes I/O, parsing, and formatting. **Evidence**: `src/utils.py`. **Suggestion**: Split into `io.py`, `parsing.py`, `formatting.py` under `utils/` and re-export from `utils/__init__.py`.

**Best practices**
- **Finding**: Several functions use `except Exception` and pass, hiding failures. **Evidence**: `src/loader.py` lines 45, 89. **Suggestion**: Catch specific exceptions, log with `logging.exception`, and re-raise or return a sentinel where appropriate.

**Best practices – library hygiene**
- **Finding**: Library code uses `print()` for diagnostic output instead of logging. **Evidence**: `src/parser.py` lines 12, 78, 134. **Suggestion**: Replace with `logger.debug()`/`logger.info()` using a module-level `logger = logging.getLogger(__name__)`.
- **Finding**: Top-level `__init__.py` configures the root logger with `logging.basicConfig()`. **Evidence**: `src/REPONAME/__init__.py` line 5. **Suggestion**: Remove; add `logging.getLogger(__name__).addHandler(logging.NullHandler())` instead. Libraries must not configure logging for their callers.
- **Finding**: `sys.exit(1)` called in library function on validation failure. **Evidence**: `src/validator.py` line 42. **Suggestion**: Raise a `ValueError` (or a custom exception) and let the caller decide how to handle it.

**Best practices – error messages**
- **Finding**: Exceptions raised with no context: `raise ValueError("invalid input")`. **Evidence**: `src/converter.py` lines 30, 55. **Suggestion**: Include the actual value and constraint: `raise ValueError(f"scale must be positive, got {scale}")`.
- **Finding**: No custom exception hierarchy; all errors are bare `ValueError`/`TypeError`. **Evidence**: Grep for `raise ValueError` across `src/`. **Suggestion**: Define a `ModulenameError` base class and specific subclasses so callers can catch library errors without catching unrelated `ValueError`s.

**Best practices – encoding and I/O**
- **Finding**: `open()` calls omit `encoding`; relies on platform default. **Evidence**: `src/reader.py` lines 18, 42. **Suggestion**: Add `encoding='utf-8'` (or the appropriate encoding) to all `open()` calls in library code.
- **Finding**: Public API accepts only `str` paths; callers using `pathlib.Path` must convert. **Evidence**: `src/loader.py` `load(path: str)`. **Suggestion**: Accept `str | Path` and convert internally with `Path(path)`.

**Types**
- **Finding**: Public API in `api.py` has no return type annotations; mypy is not run in CI. **Evidence**: `pyproject.toml` has no `[tool.mypy]`; `api.py` functions lack `->`. **Suggestion**: Add mypy to CI, enable strict mode, and annotate public functions first.

**Testing**
- **Finding**: Coverage is ~45%; module `core/solver.py` has no direct tests. **Evidence**: `coverage report`; no `tests/test_solver.py`. **Suggestion**: Add unit tests for solver entry points and key branches; aim for ≥90% on core.

**Performance**
- **Finding**: Config is re-read from disk inside a loop in `process_batch`. **Evidence**: `src/batch.py` `process_batch` calls `load_config()` per item. **Suggestion**: Load config once outside the loop and pass it in or use a module-level cache.

**Performance – concurrency and thread safety**
- **Finding**: Module-level mutable cache `_cache = {}` is written from multiple functions with no locking. **Evidence**: `src/registry.py` line 8 and functions `register()`, `lookup()`. **Suggestion**: Protect with `threading.Lock`, or document that the module is not thread-safe.
- **Finding**: Lazy singleton initialization uses a plain `if _instance is None` check. **Evidence**: `src/client.py` `get_client()`. **Suggestion**: Use `threading.Lock` or a module-level instance initialized at import time.

**Maintainability**
- **Finding**: Feature flags and environment checks are scattered across 12 files. **Evidence**: Grep for `os.getenv("FEATURE_")`. **Suggestion**: Centralize in a `config` or `features` module and inject into call sites.

**Maintainability – documentation quality**
- **Finding**: README usage example calls `MODULENAME.process(data)` but the function was renamed to `MODULENAME.transform(data)` in v2.0. **Evidence**: `README.md` line 34 vs `src/REPONAME/__init__.py`. **Suggestion**: Update README examples to match the current API; consider a CI check that runs README code blocks.
- **Finding**: Three public modules (`analysis`, `export`, `utils`) have no corresponding Sphinx `automodule` directive. **Evidence**: Compare `src/REPONAME/__init__.py` `__all__` against `docs/module.rst`. **Suggestion**: Add `.. automodule::` entries for each public module.

**Security**
- **Finding**: Subprocess is invoked with `shell=True` and user-controlled input. **Evidence**: `src/runner.py` line 67. **Suggestion**: Use list form of arguments and avoid `shell=True`; validate/sanitize input.

**Dependencies**
- **Finding**: Runtime deps are in `requirements.txt` and `pyproject.toml` with different versions. **Evidence**: `numpy` in requirements.txt pinned, in pyproject.toml minimum. **Suggestion**: Use `pyproject.toml` as single source of truth; remove duplicate requirements.txt or generate from it.

**Dependencies – CI/CD consistency**
- **Finding**: `pyproject.toml` declares `requires-python = ">=3.10"` but CI matrix only tests 3.12. **Evidence**: `.github/workflows/run-tests.yml` `matrix.python-version: ["3.12"]`. **Suggestion**: Add 3.10, 3.11, 3.13 to the CI matrix to match the supported range.
- **Finding**: CI does not run Sphinx build or PyMarkdown; only ruff and pytest. **Evidence**: `.github/workflows/run-tests.yml`. **Suggestion**: Add Sphinx and PyMarkdown steps to match the local `run-all-checks.sh` so documentation issues are caught before merge.

**Dependencies – configuration consistency**
- **Finding**: Ruff is configured with `line-length = 88` but mypy uses no line-length setting and the project rule says 100. **Evidence**: `pyproject.toml` `[tool.ruff]` vs `.cursor/rules/python.mdc`. **Suggestion**: Align `line-length` across ruff, formatter, and project rules to a single value.
- **Finding**: Stale `[tool.black]` section remains in `pyproject.toml` after migration to Ruff. **Evidence**: `pyproject.toml` line 45. **Suggestion**: Remove the `[tool.black]` section; Ruff format replaces Black.

**Technical debt**
- **Finding**: 40+ TODO comments with no issue links or owners. **Evidence**: `grep -r TODO src`. **Suggestion**: Link TODOs to issues, or triage and remove obsolete ones; add a policy in CONTRIBUTING.

**Packaging and distribution**
- **Finding**: `pyproject.toml` is missing `project.urls` (no Homepage, Repository, or Documentation links). **Evidence**: `pyproject.toml` `[project]` section. **Suggestion**: Add `[project.urls]` with links to GitHub, ReadTheDocs, and changelog so they appear on PyPI.
- **Finding**: `__version__` is hard-coded in both `__init__.py` and `pyproject.toml`; they disagree after the last release. **Evidence**: `src/REPONAME/__init__.py` line 3 says `1.2.0`, `pyproject.toml` says `1.3.0`. **Suggestion**: Use a single source of truth (e.g. `importlib.metadata.version("MODULENAME")` in `__init__.py` reading from the installed package metadata).
- **Finding**: `py.typed` marker file is missing; downstream users get no type-checking benefit. **Evidence**: `src/REPONAME/` has no `py.typed` file. **Suggestion**: Add an empty `src/REPONAME/py.typed` and ensure it is included in the package via `[tool.setuptools.package-data]`.
- **Finding**: `tests/` directory and test fixtures are included in the sdist/wheel. **Evidence**: `pip show -f REPONAME` lists `tests/`. **Suggestion**: Exclude `tests` from the package via `[tool.setuptools.packages.find]` `exclude = ["tests*"]` or equivalent.

## Severity phrasing

- Critical: "must be addressed before…", "exposes…", "prevents…"
- High: "significantly increases…", "will make it difficult to…"
- Medium: "recommended to…", "would improve…"
- Low: "consider…", "optional:…"

## When project rules exist

- "Per project rule in `.cursor/rules/python.mdc`, …"
- "This conflicts with the project's convention that …"
- "Align with project rule: … (see python.mdc)."

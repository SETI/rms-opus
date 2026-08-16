---
name: critique-test-suite
description: Analyze the test suite for consistency, completeness, redundancy, parallel safety, and assertion quality. Produces a comprehensive report (no test modifications). Use when the user asks to critique tests, review the test suite, or generate a report for fixing tests.
---

# Critique Test Suite

Analyze all tests in the project and produce a **report only**—do not modify any test files. The report is intended to be used as a prompt for an AI agent (or developer) to fix the tests later.

## Scope

- **Tests:** All files under `tests/` (pytest).
- **Fixtures:** Include `conftest.py` and any shared fixtures in the analysis.
- **Package:** Assume a standard Python package layout (e.g. `src/` with the package under test; tests in `tests/`).

## Project rules

If the repo contains a `.cursor/rules/` directory, treat those rule files as the authoritative standard and cite them by filename in findings:

- `python_testing.mdc` — the **primary** standard for this critique (pytest usage, fixtures, parametrization, coverage target, markers, TDD, hygiene). Map the checklist items below to it wherever they overlap.
- `python.mdc` — general coding standards that apply to test code as well (naming, type annotations, docstrings, DRY, line length).
- `logging.mdc` / `logging_nav.mdc` — the logging conventions the logging-assertion checks (section 21) should validate against.
- `filecache.mdc` — the transparent local/remote file-access conventions; relevant where tests touch file paths or temp directories.

Not every project ships every rule. **If a referenced rule file does not exist, ignore the corresponding part of the critique** instead of inventing a standard. In particular, the `filecache` and `logging` (and `logging_nav`) rules are project-specific and are frequently absent; when they are missing, skip the file-access and logging-assertion checks that rely on them and do not report their absence as a finding.

## Checklist for Analysis

Apply these criteria when reviewing each test file and each test case.

### 1. Return values and assertions

- **Explicit values:** Assert exact expected values where known (e.g. `assert result == expected`, not just `assert result` or `assert result is not None`).
- **Dynamic values:** When the value is dynamic (IDs, timestamps), assert **type** and **format** (e.g. regex, enum membership) rather than only existence.
- **Collections:** Prefer asserting **exact length** (e.g. `assert len(items) == 2`) when the expected count is known; avoid only `assert len(items) >= 1` unless the count truly varies.
- **Shape:** For dicts or structured return values, assert expected keys or shape where the contract is defined (e.g. no extra keys, required keys present).

### 2. Success and failure conditions

- **Success paths:** Every behavior under test should have at least one test that asserts the happy-path result (return value or side effect).
- **Failure paths:** For each operation, consider: invalid arguments (TypeError, ValueError), missing data (KeyError, custom exceptions), domain-specific errors. Note missing failure cases in the report.
- **Edge cases:** Empty collections, None/optional values, boundary values (min/max length, zero, negative where invalid).

### 3. Consistency

- **Naming:** Test names should follow a consistent style (e.g. `test_<action>_<condition>_<expected>` or `test_<function>_returns_<value>_when_<condition>`).
- **Structure:** Similar units (e.g. same module or class) should have similar test structure (success, validation error, edge case).
- **Fixtures:** Same concepts (e.g. "sample data", "minimal config") should be reused via fixtures; avoid duplicating setup logic.
- **Assertion style:** Prefer one logical assertion per concept; group related assertions consistently across files.

### 4. Completeness

- **Coverage map:** For each module or public API area, list which behaviors are tested and which are missing.
- **Parameters:** Arguments that affect behavior should have at least one test (valid and, where relevant, invalid).
- **Documentation:** If the project has a spec or docstrings that define behavior, note gaps between documented behavior and tests.

### 5. Redundancy

- **Duplicate coverage:** Identify tests that assert the same behavior in the same way; suggest merging or removing duplicates.
- **Overlap:** Note tests that are subsets of others (e.g. one test checks return type only, another checks return type and value for the same case).
- **Fixtures:** Flag repeated inline setup that could be a shared fixture.

### 6. Parallel execution

- **Isolation:** Tests must not depend on global state, shared mutable objects, or execution order. Note any use of module/class-level mutable state or singletons.
- **Resources:** Note any shared files, caches, or external services that could cause flakiness under `pytest -n auto`.
- **Database:** If the project uses a DB in tests, per-worker schema or transactional rollback should be used; note tests that commit data that could leak to other workers.

### 7. Mocking and dependency isolation

- **External services:** HTTP calls, file I/O to shared paths, or third-party APIs should be mocked in unit tests; note tests that make real external calls.
- **Time-sensitive logic:** Tests involving `datetime.now()`, `time.time()`, or expiration should freeze time (e.g. `freezegun`, `time_machine`) for determinism.
- **Pure logic:** Unit tests for pure business logic should not require a database or network; note functions that could be unit-tested but only have integration tests.
- **Environment variables:** Tests should not depend on real `.env` or env values; note tests that would fail with different env configs.
- **Patch target location:** `mock.patch` must target where the name is *looked up*, not where it is *defined* (e.g. `mock.patch("module_under_test.requests.get")`, not `mock.patch("requests.get")`). Note patches that target the wrong module.
- **`monkeypatch` vs `mock.patch` usage:** Prefer a consistent default per test file, but allow either tool where it is the clearer fit (e.g., env/process state with `monkeypatch`, call assertions/spies with `mock.patch`). Flag only inconsistent usage that reduces clarity.
- **Patch scope:** Decorator-level `mock.patch` applies for the whole test; context-manager form limits scope. Note patches broader than needed or too narrow (missing setup/teardown).
- **Mock return values:** Mocks that return `MagicMock()` by default can hide type bugs (a function expected to return `str` returns a `MagicMock` and downstream code doesn't fail because it's truthy). Note mocks in critical paths without explicit `return_value` or `side_effect`.

### 8. Security and input validation

- **Input validation:** Functions that accept user or external input should have tests for invalid input (wrong type, out-of-range, malicious patterns). Note missing validation tests.
- **Sensitive data:** Verify that tests do not log or assert on real secrets; test data should not contain real credentials. Note any exposure risk.
- **Path traversal / injection:** If the code handles paths or structured input, note missing tests for path traversal or injection where relevant.

### 9. Parameterization and data-driven tests

- **`@pytest.mark.parametrize`:** Similar test cases (e.g. multiple invalid inputs) should be parameterized instead of copy-pasted; note repeated test bodies that differ only in input.
- **Boundary values:** For numeric or length-sensitive fields, test min, max, and off-by-one values; note missing boundary tests.
- **Factories:** Test data should be created via factories or fixtures where it reduces duplication or collision risk; note tests with hard-coded values that could be shared.

### 10. Async (if the project uses async)

- **Async fixtures:** Fixtures returning async resources should use `@pytest_asyncio.fixture`; note misuse or sync fixtures in async test files.
- **Timeouts:** Long-running async operations should have explicit timeouts in tests; note tests that could hang.
- **Isolation:** For code that modifies shared state, note whether concurrent access is tested if relevant.

### 11. Output and contract

- **Return shape:** Where the public API defines a return type or shape (e.g. dataclass, TypedDict), tests should assert that shape or key fields; note tests that only spot-check.
- **Exceptions:** Verify that documented or expected exceptions are raised with correct types; note tests that only check "no exception" without testing failure paths.
- **Exception message contents:** When testing exceptions that have defined messages (e.g. validation errors), tests must assert on the **contents** of the exception message, not only that the exception was raised. Use `pytest.raises(SomeError) as exc_info` and assert on `str(exc_info.value)`. Note tests that only check exception type.

### 12. Error handling and messages

- **Error specificity:** Different error conditions should be distinguishable (e.g. by exception type or message); note tests that only check "an exception was raised" without verifying which one.
- **Exception propagation:** For unit tests of code that raises, verify that exceptions are raised with correct types and messages; note missing exception tests.
- **Message assertion:** When exceptions have defined messages, assert on message content (e.g. `pytest.raises(...) as exc_info`, then `assert "expected substring" in str(exc_info.value)`).

### 13. State and workflow

- **State transitions:** For code with status or lifecycle (e.g. state machine, pipeline stage), test valid and invalid transitions; note missing transition tests.
- **Idempotency:** Operations that should be idempotent should be tested for repeated calls; note missing idempotency tests.
- **Side effects:** Actions that trigger side effects (e.g. callbacks, file writes) should verify those occur; note untested side effects.

### 14. Test data and fixtures

- **Realistic data:** Test data should be realistic enough to catch edge cases (e.g. Unicode, long strings); note tests using only trivial data.
- **Cleanup:** Tests that create external resources (files, temp dirs) must clean up; note tests that leak state.
- **Fixture scope:** Fixtures should use the narrowest appropriate scope (`function` > `class` > `module` > `session`); note overly broad scopes that could cause isolation issues.
- **Conftest hierarchy:** Fixtures should live in the `conftest.py` closest to where they're used — a root `conftest.py` with dozens of unrelated fixtures is a smell. Note fixtures that belong in a subdirectory conftest or in the test file itself.
- **Autouse fixtures:** `@pytest.fixture(autouse=True)` hides dependencies — a test silently depends on setup it doesn't request. Note autouse fixtures and whether they're justified (e.g. DB cleanup is reasonable; injecting test data for every test is not).
- **Fixture visibility:** Note fixtures defined in a deep conftest but used only in one test file (move to the file) and fixtures duplicated across files that should be in conftest.
- **Fixture depth:** Deep fixture-depends-on-fixture chains (3+ levels) are hard to trace and debug; note such chains.

### 15. Flakiness indicators

- **Time-based assertions:** Tests asserting on wall-clock time are flaky; note and suggest freezing time.
- **Order dependence:** Tests that pass only when run in a specific order indicate shared state; note such patterns.
- **External dependencies:** Tests depending on network, file system state, or external services are flaky in CI; note and suggest mocking.
- **Random data:** Tests using `random` or `uuid4` for assertions without seeding are non-deterministic; note and suggest seeding or fixed values.

### 16. Regression and documentation

- **Bug reference:** Tests written to reproduce bugs should reference the issue in docstring or comment; note regression tests that lack context.
- **Spec alignment:** Tests should map to documented behavior (docstrings, specs); note tests for undocumented behavior or missing tests for documented behavior.
- **Deprecation warnings:** If deprecated APIs exist, tests should verify warnings are emitted using `pytest.warns(DeprecationWarning)` (or `FutureWarning`). Note deprecated APIs that lack warning-emission tests.
- **`filterwarnings` configuration:** Check whether `filterwarnings = ["error"]` (or equivalent) is set in pytest config to surface unexpected warnings as test failures. Without it, new warnings go unnoticed. Note if missing.
- **Warning noise:** Note unexpected warnings emitted during the test run that are silently swallowed. A clean run should produce no unhandled warnings.

### 17. Other good practices

- **Independence:** Each test should be runnable in isolation; document any hidden dependencies (e.g. "must run after X").
- **Clarity:** Test names and docstrings should describe intent; report tests whose purpose is unclear.
- **Speed:** Note slow tests (e.g. many I/O calls, sleeps) that could be sped up with mocks or smaller scope.
- **Assertion messages:** Use clear messages where it helps (e.g. `assert x == y, f"Expected {x} to equal {y}"`); note assertions that would be hard to debug on failure.
- **Single responsibility:** Each test should verify one behavior; note tests that assert unrelated things or have multiple "acts".
- **Arrange-Act-Assert:** Tests should follow AAA pattern; note tests with interleaved setup and assertions.
- **Keep test logic minimal:** Avoid complex control flow in tests. Simple loops and branching are acceptable when they improve clarity (e.g., table-driven checks); flag only logic that obscures intent or masks failures.

### 18. Code coverage

- **Target:** At least 90% line coverage for the package under test (or the project's stated target).
- **Scope:** Coverage should cover almost all non-exception lines; exception branches may be excluded from the percentage but should still be tested where they represent distinct behavior.
- **Measurement:** Coverage must be checked by running the **entire test suite** (e.g. `pytest tests/ --cov=src --cov-report=term-missing`), not a subset. Note if 90% is met and whether measurement is full-suite.
- **Report:** List modules or packages below the target or with significant uncovered non-exception lines.

### 19. Pytest markers and registration

- **Marker registration:** All custom marks must be registered in `pyproject.toml` under `[tool.pytest.ini_options] markers = [...]`. Unregistered marks are silently ignored unless `--strict-markers` is enabled — a typo like `@pytest.mark.solw` means the mark has no effect. Note unregistered marks.
- **`--strict-markers`:** Check whether it is enabled in pytest config. If not, note that marker typos will go undetected.
- **`xfail` audit:** `@pytest.mark.xfail` should document a known issue with a linked ticket and use `strict=True` where the failure is expected to persist. Note `xfail` tests that now pass (missing `strict=True`) or that lack an issue reference — they may be masking real bugs.
- **`skip`/`skipif` audit:** Check whether skip conditions are still valid. Old `skipif` for Python 3.8 when the project requires `>=3.10` is dead code. Note stale skips.
- **Categorization marks:** Note whether `@pytest.mark.slow` or `@pytest.mark.integration` marks exist so developers can run fast subsets (`pytest -m "not slow"`). If all tests run at the same speed this is not needed, but if some tests are noticeably slower, suggest marking them.

### 20. Test boundary (public API vs internals)

- **Importing private names:** Tests that `from src.package._internal import _helper` are tightly coupled to implementation details and break on refactors. Note tests importing `_`-prefixed modules, classes, or functions.
- **Testing through the public API:** Prefer testing via the public surface (`__all__`, documented functions). Tests that only exercise internals give false confidence — the public API could be broken while internal tests pass. Note modules where only internals are tested.
- **Over-mocking:** Tests that mock so many internals that they're testing the mock setup, not the code. Note tests where more than half the function's collaborators are mocked, especially if the function under test is small.

### 21. Logging assertions

- **`caplog` usage:** Functions that log errors, warnings, or important info should have tests verifying log output via `caplog`. Note functions with `logger.error()` or `logger.warning()` calls that have no corresponding `caplog` assertion in tests.
- **Log level verification:** When testing logged output, verify the message is at the expected level (e.g. an error condition logs at `ERROR`, not `INFO`). Note tests that check message text but not level.
- **Absence of logging:** Some code paths should explicitly *not* produce warnings or errors during normal operation. Note where this is important but untested.

### 22. Pytest configuration

- **`pyproject.toml` `[tool.pytest.ini_options]`:** Check that `testpaths` is set (without it, pytest collects from the entire repo — slow and may find stray test files). Check `python_files`, `python_classes`, `python_functions` if non-standard naming is used.
- **Plugin inventory:** Note installed pytest plugins that are unused (slow startup) and useful plugins that are missing (e.g. `pytest-xdist` for parallelism, `pytest-randomly` for order-independence testing).
- **`addopts`:** Are default options sensible? Suggest `--strict-markers`, `--strict-config`, `-q`, and `-W error::DeprecationWarning` if not present.
- **Config conflicts:** Note if both `pytest.ini` and `[tool.pytest.ini_options]` in `pyproject.toml` exist — only one is read and the other is silently ignored.

### 23. Snapshot and golden-file testing

- **Complex output:** Functions that return large dicts, dataclass trees, serialized formats (JSON, YAML), or rendered text are hard to assert inline. Note where snapshot testing (e.g. `syrupy`) would be more maintainable than dozens of field-level assertions.
- **Golden file management:** If snapshot or golden files exist, check: are they committed to the repo? Is there a CI step to detect stale snapshots? Note missing update procedures.
- **Over-use:** Snapshot tests can become "approve and forget." Note if snapshots are used extensively but there is no evidence of intentional review on change.

## Output: Report Format

Produce a single markdown report with the following structure. Do **not** edit any test files; only write the report.

```markdown
# Test Suite Critique Report

**Generated:** [date]
**Scope:** tests/ (and conftest.py)

## Executive summary
- Overall assessment (strengths, main gaps).
- **Coverage:** At least 90% and almost all non-exception lines; measured by running the **entire test suite**. Note if met and whether measurement is full-suite.
- **Exception messages:** When testing exceptions with defined messages, tests must assert on message contents (e.g. `pytest.raises(...) as exc_info`, `str(exc_info.value)`), not only that the exception was raised.
- High-priority fixes vs. nice-to-have.

## 1. Return values and assertions
[Existence-only asserts; exact length vs >=; shape checks.]

## 2. Success and failure conditions
[Per module/area: what's tested, what's missing (validation, exceptions, edge cases).]

## 3. Consistency
[Naming, structure, fixture usage, assertion style.]

## 4. Completeness
[Coverage map; spec/docstring gaps.]

## 5. Redundancy
[Duplicate or overlapping tests with file:test references.]

## 6. Parallel execution
[Global state, order dependence, shared resources.]

## 7. Mocking and dependency isolation
[Real external calls, time-sensitive tests, env dependencies, patch targets, mock return values.]

## 8. Security and input validation
[Missing validation tests, sensitive data, injection/traversal.]

## 9. Parameterization
[Tests that could be parameterized; missing boundary tests.]

## 10. Async (if applicable)
[Async fixture issues, timeouts, isolation.]

## 11. Output and contract
[Return shape, exception types, message assertions.]

## 12. Error handling
[Error specificity; exception message content assertions.]

## 13. State and workflow
[Transitions, idempotency, side effects.]

## 14. Test data and fixtures
[Realistic data, cleanup, fixture scope, conftest hierarchy, autouse, fixture depth.]

## 15. Flakiness indicators
[Time, order, external deps, randomness.]

## 16. Regression and documentation
[Bug references, spec alignment, deprecation warnings, filterwarnings config.]

## 17. Other
[Clarity, speed, assertion messages, AAA, logic in tests.]

## 18. Code coverage
[Target 90%; full-suite measurement; modules below target.]

## 19. Pytest markers
[Unregistered marks, strict-markers, xfail audit, stale skips, categorization.]

## 20. Test boundary
[Private imports, public API coverage, over-mocking.]

## 21. Logging assertions
[caplog usage, log level checks, absence-of-logging tests.]

## 22. Pytest configuration
[testpaths, plugins, addopts, config conflicts.]

## 23. Snapshot and golden-file testing
[Complex output candidates, golden file management, over-use.]

## Prompt for an AI agent to fix tests

[Self-contained prompt for an AI to apply the fixes. Include:
- Report sections as context.
- **Coverage:** Run coverage using the entire test suite; ensure at least 90% and cover almost all non-exception lines.
- **Exception messages:** When testing exceptions with defined messages, assert on message contents (e.g. `pytest.raises(...) as exc_info`, `str(exc_info.value)`).
- Instruction to fix tests according to the report without changing production code.
- Instruction to preserve existing passing behavior and only add/change assertions and test structure.]
```

## Execution steps

1. **Gather:** List all test files under `tests/` and any `conftest.py`. Read pytest config (pyproject.toml or pytest.ini if present) for markers and addopts. For plugins, check declared entry points in dependencies, the PYTEST_PLUGINS environment variable, and any pytest_plugins references in conftest.py files.
2. **Read:** For each file, read test names, docstrings, assertion patterns (focus on `assert`, return checks, fixtures, marks, `mock.patch`, `monkeypatch`, `caplog`, `pytest.warns`).
3. **Classify:** For each criterion (1–23), note specific file names, test names, and line references or short quotes.
4. **Write:** Produce the full report in the format above, including the "Prompt for an AI agent" section at the end.
5. **Do not:** Change, add, or remove any line in any test or conftest file.

## When to use this skill

- User asks to "critique the test suite", "review the tests", "analyze tests", or "generate a report to fix tests".
- User wants a "prompt for an AI to fix the tests" based on the current test suite.

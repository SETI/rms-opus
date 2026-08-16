---
name: run-all-checks
description: Run all linting, type checking, tests, Markdown lint, and documentation build for the project. Check for errors and warnings, then fix any problems found. Use when the user asks to run checks, verify the build, run CI locally, or fix lint/type/test errors.
---

# Run All Checks

Execute all project checks (lint, typecheck, test, Markdown lint, docs) and fix any errors found. This skill aligns with the `scripts/run-all-checks.sh` script and a standard Python package layout (e.g. `src/`, `tests/`, `docs/`).

## The script controls which checks are enabled

`scripts/run-all-checks.sh` is the **single source of truth** for which checks a given repo runs. The set of checks MUST be consistent across this skill (the AI), the CI/CD pipeline, and the script — and the script is authoritative.

- Run the checks the script actually runs, and **only** those. If a check listed in this skill (e.g. a docs build, Markdown lint, or coverage gate) is not enabled in the script for this repo, it does NOT need to be run as part of the skill — skip it rather than running it anyway.
- Treat the commands and tools in this skill as the typical default set. When the script and this skill disagree, follow the script.
- If you believe a check should be added or removed, change it in `scripts/run-all-checks.sh` first (and keep CI/CD in step with it), rather than running an out-of-band check from the skill.

## Quick Start

1. Run all checks (optionally in parallel via the script).
2. Review output for errors and warnings.
3. Fix any issues found.
4. Re-run checks to verify fixes.

## Check Commands

Run from **project root** with the project **virtual environment activated** (e.g. `source venv/bin/activate` or create a new venv and then `pip install -e ".[dev]"`).

### Code (ruff, mypy, pytest)

```bash
# Lint (ruff)
python -m ruff check src tests examples
python -m ruff format --check src tests examples

# Type check (mypy)
python -m mypy src tests examples

# Tests (pytest; use -n auto for parallel when tests are independent)
python -m pytest tests -q
```

Omit `examples` if the project has no `examples/` directory. The run-all-checks script runs these in sequence; use the script’s `-c` option to run only code checks.

### Markdown (PyMarkdown)

```bash
python -m pymarkdown scan docs/ .cursor/ README.md CONTRIBUTING.md
```

Use the script’s `-m` option to run only Markdown lint.

### Documentation (Sphinx)

```bash
cd docs && make clean && make html SPHINXOPTS="-W"
```

Warnings are treated as errors (`-W`). The script’s `-d` option runs docs build plus Markdown lint.

## Using the Script

From project root:

```bash
./scripts/run-all-checks.sh
```

Options:

- **Default**: Run code checks and docs (Sphinx + PyMarkdown) in parallel.
- `-c, --code`: Only ruff, mypy, pytest.
- `-d, --docs`: Only Sphinx build and PyMarkdown scan.
- `-m, --markdown`: Only PyMarkdown scan.
- `-s, --sequential`: Run code and docs sequentially (easier to read output).
- `-p, --parallel`: Run code and docs in parallel (the default).
- `-h, --help`: Show usage.

Set `VENV` or `VENV_PATH` to point to the virtual environment if it is not at `./venv`.

## Execution Workflow

```
Check Progress:
- [ ] Ruff check (src, tests, examples)
- [ ] Ruff format --check
- [ ] Mypy (src, tests, examples)
- [ ] Pytest (tests)
- [ ] PyMarkdown scan (docs/, .cursor/, README, CONTRIBUTING)
- [ ] Sphinx build (docs/) with SPHINXOPTS="-W"
- [ ] All errors fixed
- [ ] Re-verify all checks pass
```

### Step 1: Run Checks

Use the script (recommended) or run the commands above manually. Fix any non-zero exit codes.

### Step 2: Analyze Results

- **Errors**: Must be fixed (non-zero exit).
- **Warnings**: Sphinx is run with `-W`, so docs warnings fail the check; fix them so the build passes.

Common error types:

| Check   | Error pattern              | Typical fix                    |
|---------|----------------------------|--------------------------------|
| ruff    | `F401` unused import       | Remove import                  |
| ruff    | `ARG001` unused argument   | Prefix with `_` or add noqa    |
| mypy    | `error: Name "X" not defined` | Add import or fix typo      |
| pytest  | `FAILED` / `ERROR`        | Fix test or code under test   |
| pymarkdown | Rule ID + message       | Fix Markdown style/structure   |
| sphinx  | `WARNING: duplicate object` | Add `:no-index:` or fix refs |

### Step 3: Fix Issues

For each error: read the message, open the file and line, apply the fix. Re-run the failing check to confirm.

### Step 4: Re-verify

Run the full script again; all checks should pass (exit code 0).

## Common Fixes Reference

### Ruff unused argument (ARG001)

For fixtures that are dependencies but not directly used:

```python
def my_fixture(other_fixture: None) -> None:  # noqa: ARG001
    ...
```

### Sphinx duplicate object warning

Add `:no-index:` to the automodule directive where appropriate:

```rst
.. automodule:: mypackage.module
   :members:
   :no-index:
```

### Coverage threshold

If coverage is below the project target (90%; see `python_testing.mdc`): add tests or, temporarily, adjust `[tool.coverage.report]` / threshold in config. Prefer adding tests.

### Type annotation issues

For forward reference or union syntax issues:

```python
from __future__ import annotations  # at top of file
```

## Success Criteria

All checks pass when:

- `ruff check` → All checks passed
- `ruff format --check` → Would reformat 0 files (or run `ruff format` and re-check)
- `mypy` → Success: no issues found
- `pytest` → All tests pass; coverage meets target if configured
- `pymarkdown scan` → No violations
- `make html SPHINXOPTS="-W"` (in docs/) → Build completes with exit 0

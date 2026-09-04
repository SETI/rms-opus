# Vulture whitelist.
#
# Vulture reports names it cannot see used through static analysis. This file
# lists the irreducible false positives (framework-hook signatures,
# dynamically-referenced symbols) so `vulture` stays clean; referencing a name here
# marks it as used. Every entry carries its own justification; genuine dead code is
# deleted, not whitelisted.
#
# This module is never imported or executed; it is only parsed by vulture, and
# it is intentionally outside the ruff scope.

# `lineno` is a required positional parameter of the warnings.showwarning
# callback protocol (message, category, filename, lineno, file, line). Our
# handlers in src/opus_import/importdb/super.py and src/opus_import/cli.py
# use only `message`, so `lineno` is unused but cannot be dropped without
# breaking the callback signature.
#
# At the configured scan paths this entry suppresses nothing on its own: the
# whole-tree scan is clean without it, because tests/opus_import reads
# `node.lineno` off AST nodes and that marks the name as used everywhere. That is
# incidental coupling to an unrelated tree rather than a reason to drop the entry
# -- `vulture src` alone still reports both handlers. Re-check with `vulture src`,
# not with the configured paths, before removing it.
lineno  # unused variable (warnings.showwarning callback)

# `subprocess_coverage` is a pytest fixture requested by name and used for its effect
# rather than its value: it installs the .pth file that lets coverage measure the
# pipeline's subprocesses, and removes it again when the session ends. Three run
# fixtures in import_tests/conftest.py depend on it so that it is installed before any
# subprocess starts, which is the whole point, and pytest resolves the dependency by
# parameter name -- so the parameter cannot be renamed or dropped.
subprocess_coverage  # unused variable (pytest fixture requested for its effect)

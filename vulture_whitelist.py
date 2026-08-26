# Vulture whitelist (plan PR-02).
#
# Vulture reports names it cannot see used through static analysis. This file
# lists the irreducible false positives (framework-hook signatures,
# dynamically-referenced symbols) so `vulture` stays clean; referencing a name
# here marks it as used. PR-17 shrinks this list to individually-justified
# entries. Genuine dead code is deleted, not whitelisted.
#
# This module is never imported or executed; it is only parsed by vulture, and
# it is intentionally outside the ruff scope.

# `lineno` is a required positional parameter of the warnings.showwarning
# callback protocol (message, category, filename, lineno, file, line). Our
# handlers in src/opus_import/importdb/super.py and src/opus_import/cli.py
# use only `message`, so `lineno` is unused but cannot be dropped without
# breaking the callback signature.
#
# Measured at PR-17a: at the configured scope this entry currently suppresses
# nothing -- `vulture src integration_tests tests manage.py` is clean without
# it, because tests/opus_import reads `node.lineno` off AST nodes and that marks
# the name as used everywhere. It is kept rather than retired because that is
# incidental coupling to an unrelated tree: `vulture src` alone still reports
# both handlers, so a later PR that narrows the scan paths or rewrites those
# tests would need it back. Re-check with `vulture src` before removing it.
lineno  # unused variable (warnings.showwarning callback)

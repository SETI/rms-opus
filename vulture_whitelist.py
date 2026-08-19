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
lineno  # unused variable (warnings.showwarning callback)

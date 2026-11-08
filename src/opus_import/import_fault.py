"""Make the import fail on purpose at a named point, for the tests that prove it recovers.

A test sets ``OPUS_IMPORT_FAULT=<site>:<argument>`` in the environment of the
``opus_import`` process it starts. The import reads the variable only at the sites that
call `import_fault_argument`, and each site decides what its argument selects and what
failing there means. Nothing outside a test sets the variable.
"""

from __future__ import annotations

import os

#: The environment variable naming the fault, as ``<site>:<argument>``.
IMPORT_FAULT_ENV_VAR = 'OPUS_IMPORT_FAULT'


class InjectedImportFaultError(RuntimeError):
    """The failure a site raises when `IMPORT_FAULT_ENV_VAR` names it."""


def import_fault_argument(site: str) -> str | None:
    """Return the argument `IMPORT_FAULT_ENV_VAR` gives this site, if it names it.

    Parameters:
        site: The site asking, as the variable spells it before the colon.

    Returns:
        The text after the colon when the variable names ``site``; None otherwise,
        including when the variable is unset.
    """
    named_site, separator, argument = os.environ.get(IMPORT_FAULT_ENV_VAR, '').partition(':')
    if separator == '' or named_site != site:
        return None
    return argument

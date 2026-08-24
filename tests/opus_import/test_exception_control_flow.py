"""Pin the control-flow properties that let `ImportDBError` derive from `Exception`.

`ImportDBError` used to derive from `BaseException`, so no ``except Exception:``
handler in the pipeline could catch it and every database failure reached the top-level
handler in `opus_import.cli`. Narrowing it to `Exception` is only safe while no
``except Exception:`` handler sits between a database operation and that top-level
handler.

The handler that makes this load-bearing is in
`opus_import.steps.do_import_obs.import_run_field_function`: it wraps the call to an
``obs`` field function and, on any exception, logs "field function failed" and lets the
import *continue*. If a field function could ever reach the database, a database failure
would be logged as a bad field and the import would finish, silently writing an
incomplete database instead of aborting.

Today no field function can: nothing under `opus_import.obs` touches the database at
all. That is what the sweep below asserts. **If it fails, do not relax it** -- revisit
`import_run_field_function`, which must re-raise `ImportDBError` (or catch something
narrower) before any obs class is allowed to talk to the database.
"""

import ast
from pathlib import Path

import pytest

import opus_import.obs
from opus_import.importdb import ImportDBError

#: Every operation on `ImportDBSuper` that can raise `ImportDBError`, plus the
#: attribute the pipeline reaches the database through.
_DB_NAMES = frozenset({
    'DATABASE',
    '_execute', '_execute_and_fetchall',
    'analyze_table', 'convert_namespace_to_raw', 'convert_raw_to_namespace',
    'copy_rows_between_namespaces', 'create_table', 'delete_rows', 'drop_table',
    'find_column_max', 'general_select', 'insert_row', 'insert_rows', 'read_rows',
    'table_exists', 'table_info', 'table_names', 'update_row', 'upsert_row',
    'upsert_rows',
})

#: Modules an obs class must not import, because each is a route to the database.
_DB_MODULES = ('opus_import.importdb', 'opus_import.steps')

#: The same modules as they appear in a relative import, where the package prefix is
#: absent (`from . import importdb`, `from ..steps import do_import_mult`).
_DB_TAILS = frozenset({'importdb', 'steps'})

_OBS_DIR = Path(opus_import.obs.__file__).parent
_OBS_MODULES = sorted(_OBS_DIR.glob('*.py'))


def test_the_sweep_below_actually_has_modules_to_sweep() -> None:
    """Guard against the glob silently matching nothing and the sweep passing vacuously."""
    assert len(_OBS_MODULES) > 40


def test_import_db_error_is_an_ordinary_exception() -> None:
    """A plain ``except Exception:`` catches it, rather than it being a `BaseException`."""
    assert issubclass(ImportDBError, Exception)

    with pytest.raises(Exception) as excinfo:
        raise ImportDBError('the database went away')
    assert type(excinfo.value) is ImportDBError
    assert str(excinfo.value) == 'the database went away'


@pytest.mark.parametrize('path', _OBS_MODULES, ids=lambda p: p.name)
def test_an_obs_module_never_reaches_the_database(path: Path) -> None:
    """No module under `opus_import.obs` names a database module or operation.

    See this module's docstring for why a failure here is a control-flow problem and not
    a naming coincidence to be waived.
    """
    tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))

    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr in _DB_NAMES:
            offenders.append(f'line {node.lineno}: .{node.attr}')
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith(_DB_MODULES):
                    offenders.append(f'line {node.lineno}: import {alias.name}')
        elif isinstance(node, ast.ImportFrom):
            # A relative import has module=None (`from . import importdb`) or an
            # unqualified module (`from ..importdb import X`), so match the tail
            # names too rather than only the fully qualified form.
            module = node.module or ''
            imported = [alias.name for alias in node.names]
            if (module.startswith(_DB_MODULES)
                    or module.split('.')[0] in _DB_TAILS
                    or (node.level and any(name in _DB_TAILS for name in imported))):
                offenders.append(
                    f'line {node.lineno}: from {"." * node.level}{module} '
                    f'import {", ".join(imported)}')

    assert offenders == [], (
        f'{path.name} reaches the database, which makes the `except Exception:` in '
        f'import_run_field_function able to swallow an ImportDBError: {offenders}')

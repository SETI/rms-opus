"""Questions the harness asks a side's own code, run by that side's interpreter.

A side is one of the two versions of OPUS an A/B compares -- the before side, the commit
a change starts from, or the after side, the commit with the change -- as a checkout of
that commit and a virtual environment with the checkout installed (`benchmarks.sides`).

The harness always runs from the PR's checkout, but what a side imports, which settings
it starts with, and which bundles an import descriptor stands for are properties of
that side's code. So the harness runs this file as a script with the side's interpreter
in isolated mode (``python -I benchmarks/side_probe.py ...``), which keeps this
directory off ``sys.path``: everything imported below comes from the side's own
installation. For the same reason it imports nothing from `benchmarks` and only names
that exist on every commit from the harness's first on.

Subcommands, each printing one JSON value on standard output:

``expand GROUPS``
    ``GROUPS`` is a JSON list of bundle descriptors, one string per import invocation.
    Prints, for each, the bundles that invocation imports: its descriptors expanded the
    way the import expands them, less every bundle the import deliberately skips (its
    bundle-registry entry has no instrument class). Reads ``OPUS_CONFIG`` for the
    holdings.

``settings``
    Prints the cache backend and location, ``CACHE_MIDDLEWARE_SECONDS``, and the
    transaction isolation level of a database connection, as the side's settings
    produce them under ``OPUS_CONFIG``.
"""

import argparse
import json
import os
import sys


def _expand(groups_json: str) -> list[list[str]]:
    """Expand each group of descriptors into the bundles its invocation imports.

    Parameters:
        groups_json: A JSON list of strings, each one invocation's comma-separated
            descriptors.

    Returns:
        One list of bundle ids per group, in import order.
    """
    import pdslogger
    from pdsfile import Pds3File, Pds4File

    from opus_config import get_config
    from opus_import import import_util
    from opus_import.context import ImportContext
    from opus_import.steps import do_import_tables

    config = get_config()
    # The same shelf rules opus_import.cli applies, so a descriptor resolves here
    # exactly as it does in the import.
    Pds3File.use_shelves_only()
    Pds4File.use_shelves_only()
    Pds3File.require_shelves(True)
    Pds3File.preload(config.paths.pds3_holdings)
    Pds4File.preload(config.paths.pds4_holdings)

    logger = pdslogger.PdsLogger('benchmarks.side_probe')
    expanded = []
    for group in json.loads(groups_json):
        args = argparse.Namespace(
            bundles=[group], exclude_bundles=None, log_suppress_traceback=False
        )
        ctx = ImportContext(args=args, logger=logger)
        imported = []
        for bundle_id in import_util.yield_import_bundle_ids(ctx):
            vol_info = do_import_tables.lookup_vol_info(bundle_id)
            if vol_info is not None and vol_info['instrument_class'] is not None:
                imported.append(bundle_id)
        expanded.append(imported)
    return expanded


def _settings() -> dict[str, object]:
    """Report the cache and database settings the side's web application starts with.

    Returns:
        The cache backend class path, its location (None for a backend without one),
        ``CACHE_MIDDLEWARE_SECONDS``, and the isolation level a connection reports.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'opus_app.settings')
    import django
    from django.conf import settings
    from django.db import connection

    django.setup()
    cache = settings.CACHES['default']
    with connection.cursor() as cursor:
        cursor.execute('SELECT @@SESSION.transaction_isolation')
        isolation = cursor.fetchone()[0]
    return {
        'cache_backend': cache['BACKEND'],
        'cache_location': cache.get('LOCATION'),
        'cache_middleware_seconds': settings.CACHE_MIDDLEWARE_SECONDS,
        'isolation_level': isolation,
    }


def main() -> None:
    """Answer the one question named on the command line."""
    parser = argparse.ArgumentParser(prog='side_probe')
    commands = parser.add_subparsers(dest='command', required=True)
    expand = commands.add_parser('expand')
    expand.add_argument('groups')
    commands.add_parser('settings')
    args = parser.parse_args()
    answer: object = _expand(args.groups) if args.command == 'expand' else _settings()
    sys.stdout.write(json.dumps(answer) + '\n')


if __name__ == '__main__':
    main()

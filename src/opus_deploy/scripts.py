"""Write the server deploy chain into a directory it can be run from.

``opus_deploy_scripts`` copies every file of the chain -- the deploy scripts, the database
dump helpers, the log-analyzer cron templates and ``deploy.env.template`` -- out of the
installed distribution::

    opus_deploy_scripts --directory /opt/opus/deploy

**Copy them out rather than running them where they are installed.** A deploy runs
``pip install --upgrade rms-opus``, and these scripts are part of ``rms-opus``: a script
running from inside the environment being upgraded would be rewritten under bash, which
reads a script as it goes. A copy outside every OPUS installation is not affected by what
the deploy does to any of them.

The copy is also where ``secrets/deploy.env`` goes. The chain finds that file beside
itself -- ``<the directory this wrote>/secrets/deploy.env`` -- so the credentials live
with the copy rather than inside an installation that a deploy replaces.
"""

from __future__ import annotations

import argparse
import importlib.metadata
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from importlib.abc import Traversable

#: The packaged directory this copies, and the name it is written under.
TREE_NAME = 'server'

#: The file recording which release a copy came out of, written beside the chain. The
#: deploy scripts read it and object when it names a release other than the one being
#: deployed: the chain changes between releases, so deploying one release with another
#: release's scripts is how a step a release added goes missing.
VERSION_FILE = 'CHAIN_VERSION'

#: Mode for the shell scripts, and for everything else. A wheel does not carry the
#: executable bit -- ``pip`` writes package data readable and no more -- so it is applied
#: here rather than preserved, by the only rule available: the file's name.
SCRIPT_MODE = 0o755
DATA_MODE = 0o644
SCRIPT_SUFFIX = '.sh'


def _replace(target: Path, data: bytes, mode: int) -> None:
    """Put bytes at a path, by renaming a temporary file over whatever is there.

    Writing to the path directly would truncate the file and fill it again, and one of
    the files this writes is a script that is running while it runs:
    ``update_deploy_scripts.sh`` refreshes the chain it is part of. Bash reads a script
    as it executes it and remembers where it had got to, so a file rewritten underneath
    it carries on at that offset -- into whatever the new file has there. Measured: with
    an in-place rewrite to a longer file, bash resumes inside the new text and dies on a
    fragment of it.

    A rename leaves the running script's own file intact. It is unlinked from the
    directory, but the process holding it open goes on reading it to its end, and the
    new file is what the next run sees. The mode is set on the temporary file rather
    than afterwards, so the file at the path is never briefly non-executable.

    Parameters:
        target: Where the file goes.
        data: Its contents.
        mode: The permissions it ends up with.
    """
    temporary = target.with_name(f'.{target.name}.new')
    temporary.write_bytes(data)
    temporary.chmod(mode)
    temporary.replace(target)


def _packaged_tree() -> Traversable:
    """Return the packaged deploy chain.

    Returns:
        The ``server`` directory inside this package, read through
        :mod:`importlib.resources` so that it is found in an installed distribution
        rather than relative to a source tree.
    """
    return resources.files('opus_deploy').joinpath(TREE_NAME)


def _copy_tree(source: Traversable, destination: Path, *, force: bool) -> list[Path]:
    """Copy one packaged directory into a real one, recursively.

    Parameters:
        source: The packaged directory to copy.
        destination: Where it goes. It and its parents are created.
        force: Whether to overwrite files that are already there.

    Returns:
        Every file written, in the order it was written.

    Raises:
        FileExistsError: If a file is already there and `force` is False. Nothing is
            written after the first one, because a chain half-replaced is worse than one
            not replaced at all.
    """
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for entry in sorted(source.iterdir(), key=lambda item: item.name):
        target = destination / entry.name
        if entry.is_dir():
            written += _copy_tree(entry, target, force=force)
            continue
        if target.exists() and not force:
            raise FileExistsError(f'{target} already exists; pass --force to replace it')
        _replace(
            target,
            entry.read_bytes(),
            SCRIPT_MODE if target.name.endswith(SCRIPT_SUFFIX) else DATA_MODE,
        )
        written.append(target)
    return written


def write_scripts(directory: Path, *, force: bool = False) -> list[Path]:
    """Write the whole deploy chain under a directory, and stamp it with its release.

    Parameters:
        directory: Where the chain goes. It is created if it does not exist.
        force: Whether to replace files that are already there.

    Returns:
        Every file written, the version stamp last. The stamp is written whenever the
        copy succeeds, rather than refused like the rest: it describes the copy this
        call just made, so an old one beside new scripts would be worse than none.

    Raises:
        FileExistsError: If a file is already there and `force` is False.
    """
    written = _copy_tree(_packaged_tree(), directory, force=force)
    stamp = directory / VERSION_FILE
    _replace(stamp, f'{importlib.metadata.version("rms-opus")}\n'.encode(), DATA_MODE)
    return [*written, stamp]


def main() -> None:
    """Write the deploy chain, and say what to do with it.

    Raises:
        SystemExit: With status 1 if the chain cannot be written, having said why.
    """
    parser = argparse.ArgumentParser(
        prog='opus_deploy_scripts',
        description='Write the OPUS server deploy chain into a directory it can be run from',
        epilog='Run the copy from outside every OPUS installation: a deploy upgrades the '
        'distribution these scripts are part of.',
    )
    parser.add_argument(
        '--directory',
        type=Path,
        default=Path('opus_deploy_scripts'),
        help='where to write the chain (default: ./opus_deploy_scripts)',
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='replace files that are already there instead of refusing',
    )
    arguments = parser.parse_args()

    try:
        written = write_scripts(arguments.directory, force=arguments.force)
    except (FileExistsError, NotADirectoryError, OSError) as err:
        parser.exit(1, f'{parser.prog}: {err}\n')

    print(f'Wrote {len(written)} files under {arguments.directory}')
    print(f'Deploy chain from rms-opus {importlib.metadata.version("rms-opus")}')
    print()
    print(f'Start with {arguments.directory}/README.txt: it is the steps, in order.')
    print(f'The first of them is copying {arguments.directory}/deploy.env.template to')
    print(f'{arguments.directory}/secrets/deploy.env, mode 600, and filling it in.')


if __name__ == '__main__':  # pragma: no cover
    main()

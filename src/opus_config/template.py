"""Write a copy of the configuration template where the operator is standing.

Every OPUS installation is described by one TOML file, and there is nothing to copy that
file from: an installation is a ``pip install`` with no checkout on the machine. The
template ships inside this package for that reason, and ``opus_config_template`` writes a
copy of it into the current directory::

    opus_config_template
    install -m 600 opus.toml.template opus.toml   # then fill in every <PLACEHOLDER>
    export OPUS_CONFIG=$PWD/opus.toml

The template is the documentation of the schema as well as the starting point for a file:
it carries a comment for every key, including the ones whose value is not obvious.
`opus_config.config` is what reads the finished file and reports what is wrong with it.
"""

from __future__ import annotations

import argparse
from importlib import resources
from pathlib import Path

#: The template's name inside this package, and the name a copy is written under.
TEMPLATE_NAME = 'opus.toml.template'


def template_text() -> str:
    """Return the template that ships in this package.

    Returns:
        The file's contents, read through :mod:`importlib.resources` so that it is found
        inside an installed distribution rather than relative to a source tree.
    """
    return resources.files('opus_config').joinpath(TEMPLATE_NAME).read_text(encoding='utf-8')


def write_template(directory: Path, *, force: bool = False) -> Path:
    """Write a copy of the template into a directory.

    Parameters:
        directory: Where the copy goes. It has to exist.
        force: Whether to overwrite a copy that is already there. False refuses, because
            the file a copy would replace may be one somebody has already edited.

    Returns:
        The path written.

    Raises:
        FileExistsError: If the destination exists and `force` is False.
        NotADirectoryError: If `directory` is not a directory.
    """
    if not directory.is_dir():
        raise NotADirectoryError(f'{directory} is not a directory')
    destination = directory / TEMPLATE_NAME
    if destination.exists() and not force:
        raise FileExistsError(f'{destination} already exists; pass --force to replace it')
    destination.write_text(template_text(), encoding='utf-8')
    return destination


def main() -> None:
    """Write the template, and say where it went.

    Raises:
        SystemExit: With status 1 if the copy cannot be written, having said why. The
            message names the file rather than raising a traceback at an operator who is
            configuring a server rather than debugging Python.
    """
    parser = argparse.ArgumentParser(
        prog='opus_config_template',
        description='Write a copy of the OPUS configuration template into a directory',
    )
    parser.add_argument(
        '--directory',
        type=Path,
        default=Path(),
        help='where to write the copy (default: the current directory)',
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='replace an existing copy instead of refusing',
    )
    arguments = parser.parse_args()

    try:
        destination = write_template(arguments.directory, force=arguments.force)
    except (FileExistsError, NotADirectoryError, OSError) as err:
        parser.exit(1, f'{parser.prog}: {err}\n')
    print(f'Wrote {destination}')
    print(f'Copy it with `install -m 600 {TEMPLATE_NAME} opus.toml`, fill in every')
    print('<PLACEHOLDER>, and point OPUS_CONFIG at the copy.')


if __name__ == '__main__':  # pragma: no cover
    main()

"""The code being measured: one side of an A/B, and how its CLI spells each step.

A comparison measures two versions of OPUS on the same machine, holdings and scenarios:
the **before** side, the commit a change starts from, and the **after** side, the commit
with the change. Each side is a checkout of its commit together with a virtual
environment that has that checkout installed, named on every bench command by
``--python`` (the environment's interpreter) and ``--repo-root`` (the checkout). One
command measures one side; `benchmarks.compare` then sets the two result files against
each other. A floor session measures one side, the before side, several times over.

The harness itself always runs from the PR's checkout, but everything it measures --
the import, the web application, the settings they start with -- runs as the side's
own programs, in the side's checkout, with the side's interpreter (`Side.run`). That
lets it measure any commit from its own first on, including ones whose command line
differs from the PR's, so the import's options are read from each side's ``opus_import
--help`` once per command, and each step is spelled by a fixed rule
(`Spelling.from_help`). A side lists an option when its help shows that exact option
string as a whole token, so ``--validate`` is not found inside ``--validate-perm``.
"""

from __future__ import annotations

import json
import os
import re
import subprocess  # nosec B404 - the harness runs the side's own programs
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from benchmarks.results import BENCHMARKS_DIR

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

#: The probe a side's interpreter runs to answer questions about that side's code.
SIDE_PROBE = BENCHMARKS_DIR / 'side_probe.py'

#: What a side's interpreter runs to print its ``SCHEMA_VERSION``, or ``None`` for a side
#: whose code predates the module.
SCHEMA_VERSION_PROBE = (
    'try:\n'
    '    from opus_import.schema_version import SCHEMA_VERSION\n'
    'except ModuleNotFoundError:\n'
    '    SCHEMA_VERSION = None\n'
    'print(SCHEMA_VERSION)\n'
)

#: An option string as a whole token: two dashes, then letters, digits and dashes, with
#: neither a word character nor a dash on either side.
_OPTION_TOKEN = re.compile(r'(?<![\w-])--[A-Za-z0-9][A-Za-z0-9-]*(?![\w-])')


class SideError(Exception):
    """Raised when a side's interpreter cannot answer what the harness asks it."""


def require_no_pythonpath(environment: Mapping[str, str] | None = None) -> None:
    """Refuse to measure while ``PYTHONPATH`` is set.

    Every process the harness runs inherits its environment, so a ``PYTHONPATH`` naming
    some checkout would have both sides import that checkout's code while recording
    their own commits; and the side probe, run in isolated mode, would not see it,
    so the probe and the measured processes would disagree.

    Parameters:
        environment: The environment to check; this process's own when None.

    Raises:
        SideError: If ``PYTHONPATH`` is set and not empty.
    """
    value = (os.environ if environment is None else environment).get('PYTHONPATH', '')
    if value != '':
        raise SideError(f'unset PYTHONPATH ({value!r}): each side must import its own checkout')


@dataclass(frozen=True)
class Side:
    """The code one side of an A/B runs.

    Attributes:
        python: The interpreter of the side's virtual environment, which has the side's
            checkout installed.
        repo_root: The side's checkout, the working directory of everything it runs.
    """

    python: Path
    repo_root: Path

    def run(
        self, arguments: Sequence[str], *, env: Mapping[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        """Run a command with the side's interpreter, in its checkout.

        Parameters:
            arguments: What follows the interpreter on the command line.
            env: The environment, or None for this process's own.

        Returns:
            The finished process, with its output captured as text.
        """
        return subprocess.run(  # nosec B603 - a fixed program and the harness's arguments
            [str(self.python), *arguments],
            cwd=self.repo_root,
            env=None if env is None else dict(env),
            capture_output=True,
            text=True,
            check=False,
        )

    def probe(self, arguments: Sequence[str], *, env: Mapping[str, str]) -> Any:
        """Ask the side's own code a question through `SIDE_PROBE`.

        Parameters:
            arguments: The probe's subcommand and its arguments.
            env: The environment, which names the side's configuration.

        Returns:
            The JSON value the probe printed on its last line of output.

        Raises:
            SideError: If the probe failed, naming its standard error.
        """
        finished = self.run(['-I', str(SIDE_PROBE), *arguments], env=env)
        lines = finished.stdout.strip().splitlines()
        if finished.returncode != 0 or len(lines) == 0:
            raise SideError(
                f'{self.python} {SIDE_PROBE.name} {" ".join(arguments)} exited '
                f'{finished.returncode}:\n{finished.stderr[-4000:]}'
            )
        return json.loads(lines[-1])

    def git(self, *arguments: str) -> str:
        """Run a read-only git command in the side's checkout.

        Parameters:
            arguments: The git subcommand and its arguments.

        Returns:
            Its standard output, stripped.

        Raises:
            SideError: If git fails.
        """
        finished = subprocess.run(  # nosec B603 B607 - git, read-only, the harness's arguments
            ['git', *arguments],
            cwd=self.repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if finished.returncode != 0:
            raise SideError(f'git {" ".join(arguments)} failed: {finished.stderr.strip()}')
        return finished.stdout.strip()

    def environment(self) -> dict[str, Any]:
        """Return the side's entries for a result's environment.

        Returns:
            The commit, whether the checkout has uncommitted changes, the interpreter's
            version, and the side's `schema_version`. An untracked file under ``src/``
            counts as a change, since the editable install imports it; one elsewhere
            does not, so the harness's own uncommitted results leave the checkout clean.
        """
        version = self.run(['-c', 'import platform; print(platform.python_version())'])
        changed = self.git('status', '--porcelain', '--untracked-files=no')
        untracked_source = self.git('status', '--porcelain', '--untracked-files=all', '--', 'src')
        return {
            'git_sha': self.git('rev-parse', 'HEAD'),
            'git_dirty': changed != '' or untracked_source != '',
            'python_version': version.stdout.strip(),
            'schema_version': self.schema_version(),
        }

    def schema_version(self) -> int | None:
        """Return the schema version the side's code imports and serves.

        Returns:
            The side's ``opus_import.schema_version.SCHEMA_VERSION``, or None for a side
            whose code has no such module.

        Raises:
            SideError: If the side's interpreter fails for any other reason.
        """
        finished = self.run(['-I', '-c', SCHEMA_VERSION_PROBE])
        if finished.returncode != 0:
            raise SideError(
                f'{self.python} could not report its schema version:\n{finished.stderr[-4000:]}'
            )
        printed = finished.stdout.strip()
        return None if printed == 'None' else int(printed)

    def import_help(self) -> str:
        """Return the side's ``opus_import --help`` text.

        Returns:
            The help, which needs no configuration file.

        Raises:
            SideError: If the side's import cannot print its help.
        """
        finished = self.run(['-m', 'opus_import', '--help'])
        if finished.returncode != 0:
            raise SideError(f'{self.python} -m opus_import --help failed:\n{finished.stderr}')
        return finished.stdout

    def has_coordinator(self) -> bool:
        """Return whether the side's ``opus_import_all`` starts and divides importers.

        Returns:
            True when ``python -m opus_import.import_all --help`` succeeds and lists both
            ``--importers`` and ``--sets``, which a run under the coordinator gives it;
            False for a side without the module or without either option.
        """
        finished = self.run(['-m', 'opus_import.import_all', '--help'])
        if finished.returncode != 0:
            return False
        return {'--importers', '--sets'} <= listed_options(finished.stdout)


def listed_options(help_text: str) -> frozenset[str]:
    """Return every option string a help text shows as a whole token.

    Parameters:
        help_text: The output of ``--help``.

    Returns:
        The option strings, with their leading dashes.
    """
    return frozenset(_OPTION_TOKEN.findall(help_text))


@dataclass(frozen=True)
class Spelling:
    """How one side's import CLI spells each step of the measured sequence.

    Attributes:
        erase: The erase that starts a fresh import.
        bundle_import: The option that imports bundles into the permanent tables.
        finalize: The step that finishes the database after the imports.
        reset_search_tables: The step that empties the search tables between web runs.
        validate: The validation step.
        write_schema_version: The version step, or empty where the side has none.
        timing_json: The option that writes step timings, or None where the side has
            none.
        skipped_steps: The steps the side does not have at all, by name.
        register_bundles: The option that registers bundles without importing them, or
            None where the side has none.
        join: The option that runs one importer drawing bundles from the registry, or
            None where the side has none; a side without it imports in one process.
    """

    erase: tuple[str, ...]
    bundle_import: str
    finalize: str
    reset_search_tables: str
    validate: str
    write_schema_version: tuple[str, ...]
    timing_json: str | None
    skipped_steps: tuple[str, ...]
    register_bundles: str | None = None
    join: str | None = None

    @classmethod
    def from_help(cls, help_text: str) -> Spelling:
        """Choose each step's spelling from what a side's help lists.

        Parameters:
            help_text: The side's ``opus_import --help``.

        Returns:
            The spelling, by these rules: the bundle import is ``--do-all-import`` when
            listed, else ``--import``; the search-table reset is
            ``--reset-search-tables`` when listed, else ``--drop-cache-tables``; the
            finalization is ``--finalize`` when listed, else ``--cleanup-aux-tables``;
            the validation is ``--validate`` when listed, else ``--validate-perm``; the
            erase is ``--scorched-earth --yes`` when ``--yes`` is listed, else
            ``--drop-permanent-tables --scorched-earth``; the version step is
            ``--write-schema-version`` when listed, else skipped; timings are asked
            for with ``--timing-json`` when listed, else skipped; and the registration
            and the queue importer are ``--register-bundles`` and ``--join`` when
            listed, else None.
        """
        listed = listed_options(help_text)

        def pick(preferred: str, fallback: str) -> str:
            """Return `preferred` if the side lists it, else `fallback`."""
            return preferred if preferred in listed else fallback

        skipped = []
        version: tuple[str, ...] = ('--write-schema-version',)
        if '--write-schema-version' not in listed:
            version = ()
            skipped.append('write_schema_version')
        timing: str | None = '--timing-json'
        if timing not in listed:
            timing = None
            skipped.append('timing_json')
        erase = (
            ('--scorched-earth', '--yes')
            if '--yes' in listed
            else ('--drop-permanent-tables', '--scorched-earth')
        )
        return cls(
            erase=erase,
            bundle_import=pick('--do-all-import', '--import'),
            finalize=pick('--finalize', '--cleanup-aux-tables'),
            reset_search_tables=pick('--reset-search-tables', '--drop-cache-tables'),
            validate=pick('--validate', '--validate-perm'),
            write_schema_version=version,
            timing_json=timing,
            skipped_steps=tuple(skipped),
            register_bundles='--register-bundles' if '--register-bundles' in listed else None,
            join='--join' if '--join' in listed else None,
        )

    def role(self, arguments: Sequence[str]) -> str:
        """Name an invocation by the step it performs, whatever this side calls it.

        Two sides that spell a step differently give it the same name, so their
        metrics line up in a comparison.

        Parameters:
            arguments: The invocation's command line after the interpreter.

        Returns:
            ``bundle_import:<group>`` (the group being the last argument), ``erase``,
            ``register_bundles``, ``join``, ``finalize``, ``import_dictionary``,
            ``migrate``, ``validate``, ``write_schema_version``, ``reset_search_tables``,
            or, for anything else, its options joined by spaces.
        """
        if self.bundle_import in arguments:
            return f'bundle_import:{arguments[-1]}'
        if 'migrate' in arguments:
            return 'migrate'
        if self.register_bundles is not None and self.register_bundles in arguments:
            return 'register_bundles'
        if self.join is not None and self.join in arguments:
            return 'join'
        roles = (
            (set(self.erase), 'erase'),
            ({self.finalize}, 'finalize'),
            ({'--import-dictionary'}, 'import_dictionary'),
            ({self.validate}, 'validate'),
            (set(self.write_schema_version), 'write_schema_version'),
            ({self.reset_search_tables}, 'reset_search_tables'),
        )
        for options, name in roles:
            if len(options) > 0 and options.issubset(arguments):
                return name
        skipped = {self.timing_json} if self.timing_json is not None else set()
        return ' '.join(
            argument
            for argument in arguments
            if argument.startswith('--') and argument not in skipped
        )

    def timing_args(self, path: Path) -> tuple[str, ...]:
        """Return the options asking an invocation to write its timings to a file.

        Parameters:
            path: The file.

        Returns:
            The option and the path, or nothing where the side cannot write timings.
        """
        return () if self.timing_json is None else (self.timing_json, str(path))

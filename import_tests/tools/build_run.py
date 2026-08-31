"""Build the temporary holdings tree and run the import pipeline against it.

This is the only code that turns the checked-in fixture into something the pipeline can
read, and the only code that runs the pipeline: the pytest session fixture and the golden
generator both call it, so neither can drift from the other about what a run is.

The tree it builds holds no data files at all. The import never opens one -- every size,
checksum and image dimension it stores comes from a shelf -- so the manifests are pickled
into the shelf trees and nothing else is materialized except the metadata the import
parses and the volume-set descriptions preload reads off the filesystem.

The pipeline runs as a real subprocess, exactly as production runs it. That also keeps
pdsfile's class-level global state and the unit suite's ``filterwarnings = ["error"]`` out
of the run.
"""

from __future__ import annotations

import os
import pickle
import re
import shutil
import site
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

import coverage

from import_tests.tools import fixture_layout, golden_io, holdings_survey, shelf_manifests
from import_tests.tools.golden_io import DatabaseCredentials

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

#: The environment variable the pipeline reads its configuration file from.
CONFIG_ENV_VAR = 'OPUS_CONFIG'

#: What the pipeline's subprocesses run with their hash seed pinned to.
#:
#: The import's row *contents* do not depend on it, but the order in which some rows are
#: written does: `opus_import.steps.do_param_info` asks the backend for the tables to
#: describe and gets a set, and a set of strings iterates in an order Python randomizes
#: per process. The ids handed out follow insertion order, so two runs of the same import
#: give ``param_info`` the same rows under different ids. Pinning the seed is what makes
#: a recorded run and a checked run agree; it is a property of this harness, not of the
#: pipeline, and the underlying order is worth fixing at its source.
HASH_SEED_ENV_VAR = 'PYTHONHASHSEED'
HASH_SEED = '0'

#: What coverage.py reads to start measuring inside a subprocess, and the file that has
#: to be on the interpreter's path for it to act on it.
COVERAGE_ENV_VAR = 'COVERAGE_PROCESS_START'
COVERAGE_PTH_NAME = 'opus_import_tests_subprocess_coverage.pth'
COVERAGE_PTH_CONTENT = 'import coverage; coverage.process_startup()\n'

#: The pipeline's own steps, in the order the integration import script runs them. The
#: goldens encode the row ids these produce, and the ids are handed out in the order
#: rows are inserted, so this order is part of the fixture rather than a convenience.
DROP_ARGS = ('--drop-permanent-tables', '--scorched-earth')
IMPORT_ARGS = ('--do-all-import',)
AUX_ARGS = ('--cleanup-aux-tables',)
DICTIONARY_ARGS = ('--import-dictionary',)
VALIDATE_ARGS = ('--validate-perm',)

#: The log file names the pipeline's warning and error handlers write under the run's
#: log directory. The run's real gate is what these hold, not the exit status.
ERRORS_LOG = 'ERRORS.log'
WARNINGS_LOG = 'WARNINGS.log'

#: What `reimport_bundle` writes beside the first run's, under the run's own directory.
#: The log directory is its own because pdslogger appends: sharing one would put the
#: re-import's records in front of the assertions that read the first run's.
REIMPORT_LOG_DIRNAME = 'logs_reimport'
REIMPORT_CONFIG_NAME = 'opus_reimport.toml'


@dataclass(frozen=True)
class RunPaths:
    """Where one run's tree, configuration and logs live.

    Attributes:
        root: The run's own directory, which holds everything below.
        pds3_holdings: The built PDS3 holdings root.
        pds4_holdings: The built PDS4 holdings root.
        config_file: The generated ``opus.toml``.
        log_dir: Where the pipeline writes its logs. Each run gets its own, because
            pdslogger appends and a shared directory would mix two runs' errors.
    """

    root: Path
    pds3_holdings: Path
    pds4_holdings: Path
    config_file: Path
    log_dir: Path

    @classmethod
    def under(cls, root: Path) -> RunPaths:
        """Return the standard layout under a run directory.

        Parameters:
            root: The run's directory.

        Returns:
            The paths, none of which are created here.
        """
        return cls(
            root=root,
            pds3_holdings=root / fixture_layout.PDS3_ROOT_NAME,
            pds4_holdings=root / fixture_layout.PDS4_ROOT_NAME,
            config_file=root / 'opus.toml',
            log_dir=root / 'logs',
        )

    @property
    def errors_log(self) -> Path:
        """The file every logged error ends up in."""
        return self.log_dir / ERRORS_LOG

    @property
    def warnings_log(self) -> Path:
        """The file every logged warning ends up in."""
        return self.log_dir / WARNINGS_LOG


@dataclass(frozen=True)
class StepResult:
    """What one invocation of the pipeline did.

    Attributes:
        arguments: The command line, after the interpreter.
        returncode: The process's exit status. Zero does not mean the step succeeded --
            several steps report failure through the log and still exit zero -- but a
            non-zero status does mean it stopped, which the logs alone would not say.
        stdout: What it wrote to standard output.
        stderr: What it wrote to standard error, which is where a crash's traceback
            lands.
    """

    arguments: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


@dataclass
class ImportRun:
    """One completed run of the pipeline against a built tree.

    Attributes:
        paths: Where the run's tree, configuration and logs are.
        schema: The database schema the run imported into.
        bundles: The bundles imported, in the order they were imported.
        django_tables: The tables ``manage.py migrate`` created, which are the tables
            the goldens deliberately do not cover.
        steps: Every invocation the run made, in order.
    """

    paths: RunPaths
    schema: str
    bundles: list[str] = field(default_factory=list)
    django_tables: frozenset[str] = frozenset()
    steps: list[StepResult] = field(default_factory=list)


def fixture_bundles() -> list[str]:
    """Return the fixture's bundles in the order the pipeline imports them.

    Which bundles the fixture holds is read from the expected-products directory, which
    has exactly one file per recorded bundle. Deriving it from the directory layout
    instead would miss a PDS4 bundle whose metadata sits directly under its bundle set --
    there is no directory named for it to find.

    The order is the bundle registry's own, because the goldens encode the row ids the
    import hands out and those follow insertion order.

    Returns:
        One bundle id per registered type the fixture covers.
    """
    available = {path.stem for path in fixture_layout.EXPECTED_PRODUCTS_DIR.glob('*.tsv')}
    ordered = []
    for entry in holdings_survey.registry_entries():
        ordered.extend(
            sorted(bundle for bundle in available if re.fullmatch(entry.pattern, bundle))
        )
    return ordered


def _copy_tree(source: Path, destination: Path) -> None:
    """Copy a directory tree if it exists.

    Parameters:
        source: The tree to copy.
        destination: Where it goes; its parents are created.
    """
    if not source.is_dir():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, dirs_exist_ok=True)


def _write_shelves(manifest_dir: Path, holdings_root: Path) -> None:
    """Pickle every manifest in a directory into the shelf path its name encodes.

    Parameters:
        manifest_dir: The fixture's manifests for one regime.
        holdings_root: The built holdings root to write the pickles under.
    """
    if not manifest_dir.is_dir():
        return
    for manifest_path in sorted(manifest_dir.glob(f'*{shelf_manifests.MANIFEST_EXT}')):
        name = shelf_manifests.ManifestName.parse(manifest_path.name)
        entries = shelf_manifests.read_manifest(manifest_path)
        shelf_path = holdings_root / name.shelf_relpath
        shelf_path.parent.mkdir(parents=True, exist_ok=True)
        with shelf_path.open('wb') as handle:
            pickle.dump(entries, handle)


def build_holdings_tree(paths: RunPaths, *, overlay: Path | None = None) -> None:
    """Assemble the two holdings roots the pipeline reads.

    The roots have to be named exactly ``holdings`` and ``pds4-holdings``: pdsfile finds
    a category directory by string-replacing the holdings directory's own name, so the
    names are not free choices.

    Parameters:
        paths: Where to build.
        overlay: A directory whose ``holdings``/``pds4-holdings`` subtrees are copied
            over the built ones once they are complete, which is how a negative case
            perturbs the fixture without editing it.
    """
    paths.root.mkdir(parents=True, exist_ok=True)
    paths.log_dir.mkdir(parents=True, exist_ok=True)

    _copy_tree(fixture_layout.PDS3_METADATA, paths.pds3_holdings / 'metadata')
    _copy_tree(fixture_layout.PDS3_VOLINFO, paths.pds3_holdings / '_volinfo')
    _copy_tree(
        fixture_layout.PDS3_VOLUME_INDEX, paths.pds3_holdings / fixture_layout.PDS3_VOLUMES_DIRNAME
    )
    _copy_tree(fixture_layout.PDS4_METADATA, paths.pds4_holdings / 'metadata')

    _write_shelves(fixture_layout.PDS3_MANIFESTS, paths.pds3_holdings)
    _write_shelves(fixture_layout.PDS4_MANIFESTS, paths.pds4_holdings)

    if overlay is not None:
        _copy_tree(overlay / fixture_layout.PDS3_ROOT_NAME, paths.pds3_holdings)
        _copy_tree(overlay / fixture_layout.PDS4_ROOT_NAME, paths.pds4_holdings)


def _toml_string(value: str) -> str:
    """Return a value with the two characters a TOML basic string cannot hold escaped.

    Parameters:
        value: The value to interpolate -- a path, a schema name, or a password, none of
            which this suite controls the contents of.

    Returns:
        The value with backslashes and double quotes escaped, so that a Windows path or a
        password holding either produces a configuration the loader can read.
    """
    return value.replace('\\', '\\\\').replace('"', '\\"')


def write_opus_config(paths: RunPaths, schema: str, credentials: DatabaseCredentials) -> None:
    """Write the configuration file the run reads, with every key the loader requires.

    It goes to ``paths.config_file``, which is what every caller passes to the pipeline.

    Parameters:
        paths: Where the run's tree and logs are.
        schema: The database schema to import into.
        credentials: How to reach the database server.
    """
    for directory in (paths.log_dir, paths.root / 'tar', paths.root / 'manifest'):
        directory.mkdir(parents=True, exist_ok=True)
    text = _CONFIG_TEMPLATE.format(
        host=_toml_string(credentials.host),
        user=_toml_string(credentials.user),
        password=_toml_string(credentials.password),
        schema=_toml_string(schema),
        pds3_holdings=_toml_string(paths.pds3_holdings.as_posix()),
        pds4_holdings=_toml_string(paths.pds4_holdings.as_posix()),
        run_root=_toml_string(paths.root.as_posix()),
        log_dir=_toml_string(paths.log_dir.as_posix()),
    )
    paths.config_file.write_text(text, encoding='utf-8')


#: Every key `opus_config` requires, not only the ones this suite reads: the loader
#: validates the whole file, so a run's configuration is a complete one.
_CONFIG_TEMPLATE = """\
[database]
brand = "MySQL"
host = "{host}"
database = ""
schema = "{schema}"
user = "{user}"
password = "{password}"

[paths]
pds3_holdings = "{pds3_holdings}"
pds4_holdings = "{pds4_holdings}"
opus_log_file = "{log_dir}/opus_log.txt"
import_log_dir = "{log_dir}"
tar_dir = "{run_root}/tar/"
manifest_dir = "{run_root}/manifest/"
last_blog_update_file = "{run_root}/last_blog_update.txt"
notification_file = "{run_root}/notification.html"
opus_static_root = "{run_root}/static"

[django]
secret_key = "mini-holdings-throwaway-key"
debug = false
allowed_hosts = ["127.0.0.1", "localhost", "testserver"]
cache_server_prefix = "mini_holdings"
public_url = "https://opus.invalid/"
product_http_path = "https://opus.invalid/"
viewmaster_url = "https://viewmaster.invalid/"
tar_file_url = "https://opus.invalid/tar/"
log_file_level = "INFO"
log_console_level = "INFO"
log_django_level = "WARNING"
log_api_calls = false
fake_error404_probability = 0.0
fake_error500_probability = 0.0

[import]
table_temp_prefix = "imp_"
log_file = "{log_dir}/opus_import.log"
debug_log_file = "{log_dir}/opus_import_debug.log"
"""


def install_subprocess_coverage() -> Path | None:
    """Make coverage measure the pipeline's subprocesses as well as this process.

    Coverage crosses a process boundary through an environment variable plus a ``.pth``
    file that calls ``coverage.process_startup()`` before anything else runs. The
    variable alone does nothing.

    Nothing is installed unless this process is itself being measured, and the caller is
    expected to remove what is returned: a ``.pth`` left in a site directory makes every
    later interpreter in that environment import coverage at startup.

    Where the file goes is asked of `site`, not guessed from a directory name: a Debian
    or Ubuntu system interpreter calls its directory ``dist-packages``, and a rule that
    only recognized ``site-packages`` would abort a measured run there. The *user* site
    directory is deliberately not a candidate -- it outlives the interpreter this session
    is running, and a file left in someone's home directory is not this suite's to leave.

    Returns:
        The ``.pth`` file, or None when the run is not being measured.

    Raises:
        RuntimeError: If the run is being measured and no site directory would take the
            file. Failing quietly instead would leave every pipeline subprocess
            unmeasured, and the only symptom would be the coverage floor failing at a
            fraction of its usual figure with nothing saying why.
    """
    if coverage.Coverage.current() is None:
        return None
    attempted = []
    for directory in site.getsitepackages():
        candidate = Path(directory)
        if not candidate.is_dir():
            continue
        attempted.append(str(candidate))
        pth_path = candidate / COVERAGE_PTH_NAME
        try:
            pth_path.write_text(COVERAGE_PTH_CONTENT, encoding='utf-8')
        except OSError:
            continue
        return pth_path
    raise RuntimeError(
        "Coverage is measuring this session, but none of this interpreter's site "
        f'directories would take {COVERAGE_PTH_NAME}, so the pipeline subprocesses would '
        f'go unmeasured. Tried: {attempted or "none"}. The per-user site directory is '
        'deliberately not among them, because a file left there outlives this session; '
        'run the suite in a virtual environment.'
    )


def run_environment(config_file: Path) -> dict[str, str]:
    """Return the environment one pipeline subprocess runs under.

    Parameters:
        config_file: The generated configuration file.

    Returns:
        A copy of this process's environment with ``OPUS_CONFIG`` pointed at the run's
        own configuration, the hash seed pinned so that two runs write their rows in the
        same order, and -- only when this process is itself being measured -- coverage
        told where its settings are. Setting the coverage variable unconditionally would
        make every subprocess of an unmeasured run write a data file into the working
        directory for nobody to combine.
    """
    environment = dict(os.environ)
    environment[CONFIG_ENV_VAR] = str(config_file)
    environment[HASH_SEED_ENV_VAR] = HASH_SEED
    if coverage.Coverage.current() is not None:
        environment[COVERAGE_ENV_VAR] = str(fixture_layout.REPO_ROOT / 'pyproject.toml')
    return environment


def run_pipeline_step(config_file: Path, arguments: Sequence[str]) -> StepResult:
    """Run one ``opus_import`` invocation against a built tree.

    Parameters:
        config_file: The run's configuration file.
        arguments: The command-line arguments after ``python -m opus_import``.

    Returns:
        What the invocation did. The status is not the gate -- several steps report
        failure through the log and still exit zero -- but it is recorded, because a
        step that stopped before it logged anything leaves the log silent.
    """
    finished = subprocess.run(
        [sys.executable, '-m', 'opus_import', *arguments],
        cwd=fixture_layout.REPO_ROOT,
        env=run_environment(config_file),
        capture_output=True,
        text=True,
        check=False,
    )
    return StepResult(
        arguments=tuple(arguments),
        returncode=finished.returncode,
        stdout=finished.stdout,
        stderr=finished.stderr,
    )


def run_migrate(config_file: Path) -> StepResult:
    """Create Django's own contrib tables in the run's schema.

    Parameters:
        config_file: The run's configuration file.

    Returns:
        What the invocation did.
    """
    arguments = ['manage.py', 'migrate']
    finished = subprocess.run(
        [sys.executable, *arguments],
        cwd=fixture_layout.REPO_ROOT,
        env=run_environment(config_file),
        capture_output=True,
        text=True,
        check=False,
    )
    return StepResult(
        arguments=tuple(arguments),
        returncode=finished.returncode,
        stdout=finished.stdout,
        stderr=finished.stderr,
    )


def perform_run(
    root: Path,
    schema: str,
    credentials: DatabaseCredentials,
    *,
    overlay: Path | None = None,
    bundle_groups: Sequence[Sequence[str]] | None = None,
    extra_import_args: Iterable[str] = (),
) -> ImportRun:
    """Build a tree and run the whole pipeline sequence against it.

    The sequence is the one the integration import script runs: drop everything, import
    each bundle on its own, clean up the auxiliary tables, import the dictionary,
    migrate Django's tables, validate. Importing one bundle per invocation is what
    produces the on-top-of-previous-import warnings the whitelist expects, and it fixes
    the order row ids are handed out in, which the goldens encode.

    Parameters:
        root: The run's directory.
        schema: The schema to import into.
        credentials: How to reach the database server.
        overlay: A tree copied over the built one, for a negative case.
        bundle_groups: The bundles each ``--do-all-import`` invocation imports, or None
            for one invocation per fixture bundle. Naming two bundles in one invocation
            is what puts them in the same import tables, which is where a duplicate OPUS
            id between them can be seen at all.
        extra_import_args: Arguments added to each ``--do-all-import`` invocation.

    Returns:
        The completed run.
    """
    paths = RunPaths.under(root)
    build_holdings_tree(paths, overlay=overlay)
    write_opus_config(paths, schema, credentials)

    groups = [[bundle] for bundle in fixture_bundles()] if bundle_groups is None else bundle_groups
    run = ImportRun(
        paths=paths, schema=schema, bundles=[bundle for group in groups for bundle in group]
    )

    run.steps.append(run_pipeline_step(paths.config_file, DROP_ARGS))
    for group in groups:
        run.steps.append(
            run_pipeline_step(
                paths.config_file, [*IMPORT_ARGS, *extra_import_args, ','.join(group)]
            )
        )
    run.steps.append(run_pipeline_step(paths.config_file, AUX_ARGS))
    run.steps.append(run_pipeline_step(paths.config_file, DICTIONARY_ARGS))
    run.django_tables = _migrate_and_diff(paths, schema, credentials, run)
    run.steps.append(run_pipeline_step(paths.config_file, VALIDATE_ARGS))
    return run


def _migrate_and_diff(
    paths: RunPaths, schema: str, credentials: DatabaseCredentials, run: ImportRun
) -> frozenset[str]:
    """Run the Django migration and report exactly which tables it created.

    Which tables the goldens skip is a measurement rather than a list: a table the
    import newly writes then shows up as a missing golden instead of escaping
    comparison.

    Parameters:
        paths: The run's paths.
        schema: The schema being imported into.
        credentials: How to reach the database server.
        run: The run being performed, which the migration is recorded on.

    Returns:
        The table names ``manage.py migrate`` added.
    """
    before = golden_io.list_tables(credentials, schema)
    run.steps.append(run_migrate(paths.config_file))
    after = golden_io.list_tables(credentials, schema)
    return frozenset(after) - frozenset(before)


def reimport_paths(run: ImportRun) -> RunPaths:
    """Return where a re-import of one run's bundles writes.

    The built tree is the finished run's, because re-importing means importing the same
    files again. The log directory is the re-import's own, because pdslogger appends and
    the first run's logs are what the log assertions read; the configuration file is its
    own because that is what points the invocation at that log directory.

    Parameters:
        run: The completed run to re-import into.

    Returns:
        The paths, so that the caller running the re-import and the caller reading its
        log agree about where it went without either of them spelling out the layout.
    """
    return RunPaths(
        root=run.paths.root,
        pds3_holdings=run.paths.pds3_holdings,
        pds4_holdings=run.paths.pds4_holdings,
        config_file=run.paths.root / REIMPORT_CONFIG_NAME,
        log_dir=run.paths.root / REIMPORT_LOG_DIRNAME,
    )


def reimport_bundle(run: ImportRun, bundle: str, credentials: DatabaseCredentials) -> StepResult:
    """Import one bundle a second time into the schema that already holds it.

    This is the only thing in the suite that executes the update half of every upsert --
    the documented re-import operational mode -- so it is run against the finished
    database rather than a fresh one. It writes its logs into a directory of its own,
    because pdslogger appends and the first run's logs are what the log assertions read.

    Parameters:
        run: The completed run whose schema and built tree to reuse.
        bundle: The bundle to import again.
        credentials: How to reach the database server.

    Returns:
        What the invocation did. Its status is worth reading: a re-import that never ran
        leaves the database as the first import left it, which is what all three of the
        re-import assertions also accept, so nothing downstream can tell it from a
        re-import that worked.
    """
    paths = reimport_paths(run)
    write_opus_config(paths, run.schema, credentials)
    return run_pipeline_step(paths.config_file, [*IMPORT_ARGS, bundle])


def drop_schema(credentials: DatabaseCredentials, schema: str) -> None:
    """Drop a schema a run created, whether the run passed or failed.

    A failed run's evidence is its logs and its golden differences, never a schema left
    parked on the server.

    Parameters:
        credentials: How to reach the database server.
        schema: The schema to drop.
    """
    golden_io.execute(credentials, None, f'DROP DATABASE IF EXISTS `{schema}`')

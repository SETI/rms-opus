"""The import scenario files, the holdings each scale reads, and the error-log rule.

Each scale's ``scenarios/import_<scale>.toml`` names its import runs per floor session,
and, at the holdings scales, the holdings roots and the bundle groups each invocation
imports. ``[largest]`` names the scale's largest bundle, whose ``--import`` time is the
``import.largest.import_s`` guard; where a scale names none, the harness uses the bundle
the run itself put the most ``obs_general`` rows in.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING

from benchmarks.bench_server import expand_path
from benchmarks.monitor import RunFailedError
from benchmarks.results import SCENARIOS_DIR
from import_tests.tools import build_run

if TYPE_CHECKING:
    from pathlib import Path

    from benchmarks.results import Label


@dataclass(frozen=True)
class Group:
    """One bundle-import invocation of a scenario.

    Attributes:
        bundles: Its comma-separated bundle descriptors, the invocation's last argument.
        options: Options it adds before them.
    """

    bundles: str
    options: tuple[str, ...] = ()


@dataclass(frozen=True)
class ImportScenario:
    """A scale's import scenario file.

    Attributes:
        path: The file.
        scale: The scale it describes.
        runs: Import runs per side in a floor session.
        pds3_holdings: The PDS3 holdings root, or None at fixture scale.
        pds4_holdings: The PDS4 holdings root, or None at fixture scale.
        groups: The bundle-import invocations, in order; empty at fixture scale.
        largest: The scale's largest bundle, or None to use the run's own largest.
        largest_alone: Whether the largest bundle is also imported on its own.
        incremental: Whether the incremental group runs.
    """

    path: Path
    scale: str
    runs: int
    pds3_holdings: Path | None
    pds4_holdings: Path | None
    groups: tuple[Group, ...]
    largest: str | None
    largest_alone: bool
    incremental: bool


def load_scenario(scale: str) -> ImportScenario:
    """Read the import scenario file of a scale.

    Parameters:
        scale: ``fixture``, ``test`` or ``complete``.

    Returns:
        The scenario.

    Raises:
        RunFailedError: If the file's ``scale`` is not the one asked for.
        benchmarks.app_servers.ServerError: If a holdings path names an environment
            variable that is not set.
    """
    path = SCENARIOS_DIR / f'import_{scale}.toml'
    with path.open('rb') as stream:
        raw = tomllib.load(stream)
    if raw['scale'] != scale:
        raise RunFailedError(f'{path} says scale {raw["scale"]!r}, not {scale!r}')
    holdings = raw.get('holdings')
    largest = raw.get('largest', {})
    return ImportScenario(
        path=path,
        scale=scale,
        runs=int(raw['runs']),
        pds3_holdings=None if holdings is None else expand_path(holdings['pds3']),
        pds4_holdings=None if holdings is None else expand_path(holdings['pds4']),
        groups=tuple(
            Group(bundles=group['bundles'], options=tuple(group.get('options', ())))
            for group in raw.get('groups', ())
        ),
        largest=largest.get('bundle'),
        largest_alone=bool(largest.get('alone', False)),
        incremental=bool(largest.get('incremental', False)),
    )


def holdings_for(label: Label) -> tuple[Path, Path]:
    """Return the holdings roots a label's scale reads, outside any one import run.

    Parameters:
        label: The label.

    Returns:
        The PDS3 and PDS4 roots: at fixture scale a tree built from the checked-in
        fixture in the label's scratch directory (built the first time it is asked
        for, by `import_tests.tools.build_run.build_holdings_tree`); at the holdings
        scales the roots the scale's scenario names.
    """
    if label.scale == 'fixture':
        paths = build_run.RunPaths.under(label.scratch_dir / 'fixture_tree')
        if not paths.pds3_holdings.is_dir():
            build_run.build_holdings_tree(paths)
        return paths.pds3_holdings, paths.pds4_holdings
    scenario = load_scenario(label.scale)
    assert scenario.pds3_holdings is not None
    assert scenario.pds4_holdings is not None
    return scenario.pds3_holdings, scenario.pds4_holdings


def require_empty_errors_log(path: Path, *, at_end: bool = False) -> None:
    """Check that a run's ``ERRORS.log`` is absent or empty.

    Several import steps log an error and still exit zero, so the exit status alone
    would pass a run that failed.

    Parameters:
        path: The run's ``ERRORS.log``.
        at_end: Whether the run has finished, which only changes the message.

    Raises:
        RunFailedError: If the file holds anything.
    """
    if path.exists() and path.stat().st_size > 0:
        when = 'at the end of the run' if at_end else 'before the run started'
        excerpt = path.read_text(encoding='utf-8', errors='replace')[:4000]
        raise RunFailedError(f'{path} is not empty {when}:\n{excerpt}')

"""The import benchmark's worker-count sweep: which counts it runs, and what it refuses."""

import pytest

from benchmarks import bench_import


@pytest.mark.parametrize(
    ('requested', 'cores', 'keys', 'expected'),
    [
        ([1, 2, 4, 8], 8, {}, [1, 2, 4, 6]),
        ([1, 2, 4, 8], 4, {}, [1, 2, 3]),
        ([8, 4, 2, 1], 4, {}, [3, 2, 1]),
        ([1, 2, 4, 8], 8, {'cpu_fraction': 1.0}, [1, 2, 4, 8]),
        ([2, 2, 1], 2, {}, [1]),
        ([1, 4, 8], 8, {'cpu_fraction': 0.5}, [1, 4]),
    ],
    ids=[
        'caps-at-the-ceiling',
        'caps-twice-to-one',
        'keeps-the-order',
        'whole-machine',
        'once-each',
        'fraction-given-as-text',
    ],
)
def test_each_count_is_capped_at_the_ceiling_and_run_once(
    requested: list[int], cores: int, keys: dict[str, object], expected: list[int]
) -> None:
    """The ceiling is the import's, ``max(1, floor(cores * cpu_fraction))``."""
    assert bench_import.sweep_counts(requested, keys, detected=cores) == expected


def test_the_detected_cores_decide(monkeypatch: pytest.MonkeyPatch) -> None:
    """The sweep counts the cores, as the import does."""
    monkeypatch.setattr(bench_import, 'detected_cores', lambda: 30)
    assert bench_import.sweep_counts([1, 32], {}) == [1, 22]


@pytest.mark.parametrize(
    ('extra', 'message'),
    [
        (['--workers-sweep', '1,x'], '--workers-sweep takes whole numbers separated by commas'),
        (['--workers-sweep', '0,2'], '--workers-sweep takes counts of at least 1'),
        (
            ['--workers-sweep', '1,2', '--stop-before-finalization'],
            '--workers-sweep runs imports of its own and takes no other mode',
        ),
        (
            ['--workers-sweep', '1,2', '--import-key', 'cpu_fraction=half'],
            "--import-key cpu_fraction must be greater than 0 and at most 1, not 'half'",
        ),
        (
            ['--workers-sweep', '1,2', '--import-key', 'cpu_fraction=1.5'],
            '--import-key cpu_fraction must be greater than 0 and at most 1, not 1.5',
        ),
    ],
    ids=[
        'not-a-number',
        'zero',
        'another-mode',
        'fraction-not-a-number',
        'fraction-above-one',
    ],
)
def test_a_malformed_sweep_is_refused(
    extra: list[str], message: str, capsys: pytest.CaptureFixture[str]
) -> None:
    """The arguments are checked before anything runs."""
    argv = [
        '--scale', 'test', '--side', 'after', '--pr', 'PR-09', '--session', 'sweep',
        '--python', 'python', '--repo-root', '.', *extra,
    ]  # fmt: skip
    with pytest.raises(SystemExit):
        bench_import._parse_arguments(argv)
    assert message in capsys.readouterr().err

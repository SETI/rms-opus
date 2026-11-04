"""The checks that keep a run that measured the wrong thing out of the results."""

from pathlib import Path
from typing import Any

import pytest

from benchmarks import bench_web, import_scenarios
from benchmarks.bench_web import RequestTiming, WebBench, WebRunError
from benchmarks.monitor import InvocationMonitor, RunFailedError
from benchmarks.sides import Spelling
from import_tests.tools.build_run import StepResult


class _FakeSide:
    """A side whose settings probe answers what the test says."""

    def __init__(self, answer: dict[str, Any]) -> None:
        """Remember the answer."""
        self.answer = answer

    def probe(self, arguments: list[str], *, env: dict[str, str]) -> dict[str, Any]:
        """Return the answer, whatever is asked."""
        return self.answer


class _FakeMemcached:
    """A memcached that is only an address."""

    location = '127.0.0.1:21211'


def _bench(answer: dict[str, Any]) -> WebBench:
    """Return a web bench whose only working parts are the settings check's."""
    bench = WebBench.__new__(WebBench)
    bench.side = _FakeSide(answer)  # type: ignore[assignment]  # a stand-in side
    bench.memcached = _FakeMemcached()  # type: ignore[assignment]  # a stand-in memcached
    bench.env = {}
    return bench


def test_the_local_memory_fallback_is_refused() -> None:
    """Settings that fell back to locmem would measure no shared cache at all."""
    bench = _bench(
        {
            'cache_backend': 'django.core.cache.backends.locmem.LocMemCache',
            'cache_location': None,
        }
    )
    with pytest.raises(WebRunError, match='the local-memory fallback'):
        bench.application_settings()


def test_a_memcached_other_than_the_harness_s_is_refused() -> None:
    """A cache the harness neither owns nor resets would carry state between runs."""
    bench = _bench(
        {
            'cache_backend': 'django.core.cache.backends.memcached.PyMemcacheCache',
            'cache_location': '127.0.0.1:11211',
        }
    )
    with pytest.raises(WebRunError, match='not at the harness memcached'):
        bench.application_settings()


def test_the_harness_memcached_is_accepted() -> None:
    """The settings are returned when they name the harness's own memcached."""
    answer = {
        'cache_backend': 'django.core.cache.backends.memcached.PyMemcacheCache',
        'cache_location': '127.0.0.1:21211',
    }
    assert _bench(answer).application_settings() == answer


def test_an_errors_log_with_content_fails_the_run(tmp_path: Path) -> None:
    """A step can log an error and exit zero; the log is what says it failed."""
    path = tmp_path / 'ERRORS.log'
    path.write_text('ERROR | validation found a problem\n')
    with pytest.raises(RunFailedError, match='is not empty at the end of the run'):
        import_scenarios.require_empty_errors_log(path, at_end=True)


def test_an_errors_log_left_from_before_the_run_is_refused(tmp_path: Path) -> None:
    """A run that starts on a used log could blame its errors on nothing, or the reverse."""
    path = tmp_path / 'ERRORS.log'
    path.write_text('ERROR | an earlier run\n')
    with pytest.raises(RunFailedError, match='is not empty before the run started'):
        import_scenarios.require_empty_errors_log(path)


@pytest.mark.parametrize('content', [None, ''], ids=['absent', 'empty'])
def test_an_absent_or_empty_errors_log_passes(tmp_path: Path, content: str | None) -> None:
    """Nothing logged is a clean run, and checking leaves the log as it was."""
    path = tmp_path / 'ERRORS.log'
    if content is not None:
        path.write_text(content)
    import_scenarios.require_empty_errors_log(path, at_end=True)
    assert (path.read_text() if path.exists() else None) == content


def _monitor() -> InvocationMonitor:
    """Return a monitor that needs no server, for checks that stop before connecting."""
    return InvocationMonitor(
        server=None,  # type: ignore[arg-type]  # never reached by these checks
        schema='bench_x',
        spelling=Spelling.from_help('--do-all-import --drop-cache-tables --validate-perm'),
        expand=lambda groups: [[group] for group in groups],
        timing_file=None,
        excluded_pids=set,
    )


def test_an_invocation_that_exits_non_zero_fails_the_run() -> None:
    """A stopped step is a failed run, whatever its log says."""
    monitor = _monitor()
    monitor.step_started(['--validate-perm'])
    with pytest.raises(RunFailedError, match='`validate` exited 255'):
        monitor.step_finished(StepResult(('--validate-perm',), 255, '', 'boom'))


def test_a_bundle_group_that_was_not_announced_is_refused() -> None:
    """Every group must be expanded up front, so its bundles can be checked after."""
    monitor = _monitor()
    monitor.expect_groups(['COISS_2002'])
    monitor.step_started(['--do-all-import', 'COISS_2002'])
    with pytest.raises(RunFailedError, match="'COISS_2008' was not announced"):
        monitor.step_started(['--do-all-import', 'COISS_2008'])


def test_result_count_reads_the_count_from_its_response() -> None:
    """The last page of a pages scenario comes from this count."""
    timing = RequestTiming('build', 'u', 0.0, 0.1, 200, b'{"data": [{"result_count": 1234}]}')
    assert bench_web.result_count(timing) == 1234


def test_a_failed_result_count_is_not_read() -> None:
    """A 500 has no count; using one would page through nothing."""
    timing = RequestTiming('build', 'u', 0.0, 0.1, 500, b'')
    with pytest.raises(WebRunError, match='answered 500'):
        bench_web.result_count(timing)

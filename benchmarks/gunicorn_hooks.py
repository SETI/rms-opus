"""The gunicorn configuration file the harness starts every side's application with.

gunicorn executes this file by path, in the side's interpreter, so it imports nothing
from `benchmarks` and works on any commit. It does three things, all outside the
application's code:

* **It finishes loading the application at worker start.** Django imports its URLconf,
  and with it every view module, on a process's first request, which costs a fresh
  worker a quarter of a second on its first request whatever that request is. A
  measured request would pay it or not depending on which worker the kernel handed the
  connection to, so ``post_worker_init`` imports the URLconf before the worker accepts
  anything. The harness already records the application as loaded eagerly.
* **It says which worker served each request.** ``post_worker_init`` writes
  ``<pid>\\tREADY`` and ``post_request`` writes ``<pid>\\t<uri>`` to the file the
  `SERVED_LOG_ENV` environment variable names, one line per write, so the harness can
  tell when every worker is ready, prove a cold scenario started on workers that had
  served nothing, and warm every worker before a warm repetition.
* **It sets the Django settings a run asks for.** `DJANGO_SETTINGS_ENV` holds a JSON
  object of setting names and values (``bench_web --django-setting``), which
  ``post_worker_init`` assigns before the worker serves anything, so a run can measure
  a branch the defaults do not take at its scale. A setting the side does not read is
  set and ignored.
"""

import json
import os

#: The environment variable naming the file the hooks append to.
SERVED_LOG_ENV = 'BENCHMARK_SERVED_LOG'

#: The line a worker writes once it has finished loading the application.
READY = 'READY'

#: The environment variable holding the Django settings a run sets, as a JSON object.
DJANGO_SETTINGS_ENV = 'BENCHMARK_DJANGO_SETTINGS'


def apply_settings(settings: object) -> None:
    """Assign each setting `DJANGO_SETTINGS_ENV` names to the application's settings.

    Parameters:
        settings: The settings object, Django's ``django.conf.settings`` in a worker.
    """
    overrides = os.environ.get(DJANGO_SETTINGS_ENV)
    if overrides is None:
        return
    for name, value in json.loads(overrides).items():
        setattr(settings, name, value)


def _record(text: str) -> None:
    """Append one line for this worker to the served log, in a single write.

    Parameters:
        text: What follows the worker's process id on the line.
    """
    path = os.environ.get(SERVED_LOG_ENV)
    if path is None:
        return
    descriptor = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    try:
        os.write(descriptor, f'{os.getpid()}\t{text}\n'.encode())
    finally:
        os.close(descriptor)


def post_worker_init(worker: object) -> None:
    """Set the run's settings, import the URLconf, then record that this worker is ready.

    Parameters:
        worker: The gunicorn worker, unused.
    """
    del worker
    # Imported here, in the worker, where loading the application has set Django up.
    from django.conf import settings
    from django.urls import get_resolver

    apply_settings(settings)
    _ = get_resolver().url_patterns
    _record(READY)


def post_request(worker: object, req: object, environ: object, resp: object) -> None:
    """Record that this worker served a request.

    Parameters:
        worker: The gunicorn worker, unused.
        req: The request, whose ``uri`` is its path and query string.
        environ: The WSGI environment, unused.
        resp: The response, unused.
    """
    del worker, environ, resp
    _record(str(getattr(req, 'uri', '')))

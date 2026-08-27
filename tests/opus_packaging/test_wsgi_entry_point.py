"""Tests for locating the WSGI module without building the application.

Apache's ``WSGIScriptAlias`` needs a *path*, and on a pip-installed server that path is
inside the virtual environment's ``site-packages``, where it moves with the Python
version. The deploy chain therefore resolves it at deploy time and writes a symlink at
a fixed path for the vhost to name.

Resolving it must not *import* :mod:`opus_app.wsgi`. Importing it runs
``get_wsgi_application()``, which calls ``django.setup()``, which applies ``LOGGING``
and opens the log file -- so asking for a path does real work and fails whenever the
environment is not yet complete. That is not hypothetical: the first version of the
deploy step imported the module, the import died on a log directory that did not exist
yet, the command substitution returned an empty string, and ``ln`` was handed an empty
target -- with Apache already stopped.

:func:`importlib.util.find_spec` is what the deploy uses instead. These tests pin the
two properties that makes it depend on: that it finds the file, and that finding it
imports nothing.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.name != 'posix', reason='the deploy chain is bash, and runs only on the servers'
)


def test_the_wsgi_module_can_be_located() -> None:
    """``find_spec`` resolves ``opus_app.wsgi`` to a file that exists.

    ``origin`` being ``None`` -- as it is for a namespace package -- would give the
    deploy an empty symlink target, which is the failure this replaced.
    """
    spec = importlib.util.find_spec('opus_app.wsgi')
    assert spec is not None
    assert spec.origin is not None
    assert Path(spec.origin).is_file()
    assert Path(spec.origin).name == 'wsgi.py'


def test_locating_it_neither_imports_it_nor_configures_django() -> None:
    """Resolving the path has no side effects.

    Run in a subprocess with nothing imported beforehand, because this process has
    already configured Django through pytest-django and could not tell the difference.
    ``opus_app`` itself is imported -- ``find_spec`` has to import the parent package to
    find its ``__path__`` -- so the assertion is about ``opus_app.wsgi`` and about
    Django's settings, not about ``opus_app``.
    """
    program = (
        'import importlib.util, sys\n'
        'spec = importlib.util.find_spec("opus_app.wsgi")\n'
        'assert spec is not None and spec.origin is not None\n'
        'assert "opus_app.wsgi" not in sys.modules, "find_spec imported the module"\n'
        'from django.conf import settings\n'
        'assert not settings.configured, "find_spec configured Django"\n'
        'print("clean")\n'
    )
    result = subprocess.run(
        [sys.executable, '-c', program],
        capture_output=True,
        text=True,
        check=False,
        # A deliberately empty environment but for PATH: no OPUS_CONFIG and no
        # DJANGO_SETTINGS_MODULE, which is the state the deploy step runs in and the
        # state in which importing the module would fail outright.
        env={'PATH': '/usr/bin:/bin'},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == 'clean'


def test_importing_the_wsgi_module_really_does_need_a_configured_environment() -> None:
    """The reason for the above: importing it without OPUS_CONFIG fails.

    Without this the two tests above would pass just as well against an
    ``opus_app.wsgi`` that imports harmlessly, and would be asserting nothing about why
    ``find_spec`` is used. This is the failure ``find_spec`` sidesteps, constructed.
    """
    result = subprocess.run(
        [sys.executable, '-c', 'import opus_app.wsgi'],
        capture_output=True,
        text=True,
        check=False,
        env={'PATH': '/usr/bin:/bin'},
    )
    assert result.returncode != 0, 'importing opus_app.wsgi with no OPUS_CONFIG succeeded'

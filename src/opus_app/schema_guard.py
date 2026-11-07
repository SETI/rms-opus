"""Serve a schema only when it is one this release imported and finished.

A finished schema carries a one-row ``schema_version`` table naming the generation of
the table schemas that imported it, in the ``ready`` state
(`opus_import.schema_version`). `opus_app.wsgi` reads the row as the application is
loaded, and serves the application only when the row is this release's version and
``ready``. Otherwise every request is answered ``503 Service Unavailable`` with a body
saying what is wrong and what fixes it, and repeats the check, so a worker starts
serving once the schema is finished, without a reload.

The check sits in the WSGI entry point rather than in the settings or an application's
``ready`` hook so that ``inspectdb``, the database-free unit suite and every other
management command go on working against any schema. A refusal is a stub application
rather than an exception, because mod_wsgi loads the entry point again on every request
after one that raised.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable, Iterable
from typing import Any

from django.db import DatabaseError, connection

from opus_import.schema_version import TABLE_NAME, problem

#: A WSGI application.
Application = Callable[[dict[str, Any], Callable[..., Any]], Iterable[bytes]]

#: What reads the version rows, or raises `django.db.DatabaseError` when it cannot.
RowReader = Callable[[], list[tuple[Any, ...]]]

#: The status every refused request is answered with.
UNAVAILABLE_STATUS = '503 Service Unavailable'

_LOG = logging.getLogger(__name__)


def read_rows() -> list[tuple[Any, ...]]:
    """Read the served schema's version rows on Django's connection, then close it.

    The connection is closed because the first read is made while the application loads,
    in a thread no request runs on; a refused request's read closes its own thread's
    connection too, which Django opens again when the thread next needs one.

    Returns:
        The ``(version, state)`` rows; empty when the table does not exist.

    Raises:
        django.db.DatabaseError: If the database cannot be reached or read.
    """
    try:
        with connection.cursor() as cursor:
            if TABLE_NAME not in connection.introspection.table_names(cursor):
                return []
            cursor.execute(f'SELECT version, state FROM {TABLE_NAME}')  # nosec B608 - a constant
            return [tuple(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def unavailable(message: str) -> Application:
    """Return an application that answers every request 503, explaining why.

    Parameters:
        message: What keeps the schema from being served, and the remedy.

    Returns:
        The stub application.
    """
    body = f'OPUS is unavailable: {message}.\n'.encode()

    def application(environ: dict[str, Any], start_response: Callable[..., Any]) -> list[bytes]:
        """Answer one request with the 503.

        Parameters:
            environ: The request's WSGI environment, unused.
            start_response: The server's callback.

        Returns:
            The body.
        """
        start_response(
            UNAVAILABLE_STATUS,
            [('Content-Type', 'text/plain; charset=utf-8'), ('Content-Length', str(len(body)))],
        )
        return [body]

    return application


class _Refusing:
    """The application, behind a check that has not yet passed.

    Each request repeats the check. While it fails -- no row, another version, a state
    other than ``ready``, or a database that cannot be read -- the request is answered
    503 with what is wrong. Once it passes, that request and every later one go to the
    application, and the check is not made again. So a worker that loaded before the
    schema was finished serves it once ``opus_import --write-schema-version`` has run,
    without a reload, and a refused worker costs the database one small query a request.
    """

    def __init__(self, application: Application, read: RowReader) -> None:
        """Hold the application until the check passes.

        Parameters:
            application: The Django application.
            read: What reads the version rows.
        """
        self._application = application
        self._read = read
        self._passed = False
        self._lock = threading.Lock()

    def _problem(self) -> str | None:
        """Make the check once.

        Returns:
            None when it passes, else what is wrong.
        """
        try:
            return problem(self._read())
        except DatabaseError as error:
            # The driver's message names the account, so it goes to the log rather than
            # into a public response.
            _LOG.warning('The schema version row could not be read (%s)', error)
            return 'the database could not be read'

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> Any:
        """Serve one request.

        Parameters:
            environ: The request's WSGI environment.
            start_response: The server's callback.

        Returns:
            The application's response once the check passes, else the 503's.
        """
        if not self._passed:
            with self._lock:
                if not self._passed:
                    found = self._problem()
                    if found is not None:
                        return unavailable(found)(environ, start_response)
                    self._passed = True
        return self._application(environ, start_response)


def guard(application: Application, read: RowReader = read_rows) -> Application:
    """Return what the web server should call.

    Parameters:
        application: The Django application.
        read: What reads the version rows; the default reads them through Django.

    Returns:
        The application itself when the schema's row is this release's version and
        ``ready``. Otherwise -- the row absent, another version or not ``ready``, or the
        database unreadable -- the application behind a check every request repeats,
        answering 503 until it passes.
    """
    try:
        found = problem(read())
    except DatabaseError as error:
        # One line: a traceback here says nothing the error does not.
        _LOG.warning(
            'The schema version row could not be read (%s); each request will try again', error
        )
        return _Refusing(application, read)
    if found is None:
        return application
    _LOG.warning('Refusing to serve the schema: %s', found)
    return _Refusing(application, read)

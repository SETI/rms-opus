"""Serve a schema only when it is one this release imported and finished.

A finished schema carries a one-row ``schema_version`` table naming the generation of
the table schemas that imported it, in the ``ready`` state
(`opus_import.schema_version`). `opus_app.wsgi` reads the row once, as the application
is loaded, and serves the application only when the row is this release's version and
``ready``. Otherwise every request is answered ``503 Service Unavailable`` with a body
saying what is wrong and what fixes it.

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

    The connection is closed because it was opened while the application loaded, in a
    thread no request runs on.

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


class _CheckOnRequest:
    """The application, behind a check that could not reach the database when loaded.

    Each request repeats the check until it gets an answer. Then the request, and every
    later one, goes to the application or to the 503 stub, as the answer says. A request
    that still cannot reach the database is answered 503.
    """

    def __init__(self, application: Application, read: RowReader) -> None:
        """Hold the application until the check answers.

        Parameters:
            application: The Django application.
            read: What reads the version rows.
        """
        self._application = application
        self._read = read
        self._decided: Application | None = None
        self._lock = threading.Lock()

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]) -> Any:
        """Serve one request.

        Parameters:
            environ: The request's WSGI environment.
            start_response: The server's callback.

        Returns:
            The response body of whichever application serves the request.
        """
        if self._decided is None:
            with self._lock:
                if self._decided is None:
                    try:
                        self._decided = decide(self._application, self._read())
                    except DatabaseError as error:
                        # The driver's message names the account, so it goes to the log
                        # rather than into a public response.
                        _LOG.warning('The schema version row could not be read (%s)', error)
                        return unavailable('the database could not be read')(
                            environ, start_response
                        )
        return self._decided(environ, start_response)


def decide(application: Application, rows: list[tuple[Any, ...]]) -> Application:
    """Choose what serves requests, given the schema's version rows.

    Parameters:
        application: The Django application.
        rows: The ``(version, state)`` rows.

    Returns:
        The application when the rows pass `opus_import.schema_version.problem`, else
        the 503 stub.
    """
    found = problem(rows)
    return application if found is None else unavailable(found)


def guard(application: Application, read: RowReader = read_rows) -> Application:
    """Return what the web server should call: the application, or the 503 stub.

    Parameters:
        application: The Django application.
        read: What reads the version rows; the default reads them through Django.

    Returns:
        The application when the schema's row is this release's version and ``ready``;
        the 503 stub when it is absent, another version, or not ``ready``; and, when the
        database cannot be read at all, the application behind a check each request
        repeats until the database answers, so a database that is down while the
        application loads is not refused for good.
    """
    try:
        rows = read()
    except DatabaseError as error:
        # One line: a traceback here says nothing the error does not.
        _LOG.warning(
            'The schema version row could not be read (%s); each request will try again', error
        )
        return _CheckOnRequest(application, read)
    return decide(application, rows)

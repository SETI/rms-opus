"""The database interface every import step runs through, independent of brand.

`ImportDBSuper` defines the operations the pipeline needs -- creating and dropping
tables, reading and writing rows, and copying a bundle from the import namespace to the
permanent one -- and leaves the SQL to a subclass per database brand.
`opus_import.importdb.mysql` is the implemented one; every method here that a brand must
supply raises `NotImplementedError`.

Two behaviors are implemented here rather than per brand, because they are the same for
any brand: `ImportDBSuper.convert_raw_to_namespace` and its inverse map a table's raw
name to the namespace it is being used in, and `ImportDBSuper._operation` collects the
Python warnings a database operation emits so they are reported together with the
statements that produced them.
"""

from __future__ import annotations

import contextlib
import threading
import time
import warnings
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from opus_config.config import DEFAULT_TRANSACTION_ROWS
from opus_import.table_keys import is_key_filtered_table

if TYPE_CHECKING:
    from collections.abc import Collection, Iterator, Mapping, Sequence
    from typing import TextIO

    import pdslogger

    from opus_import.table_keys import TableKey

Namespace = Literal['import', 'perm', 'all']
"""Which set of tables an operation applies to.

An import into a schema with a version row writes to prefixed *import* tables and only
copies them over the *perm* (permanent) tables the web application reads once the run
has succeeded. A fresh import writes the observation and mult tables directly: with
`ImportDBSuper.direct` set, ``'import'`` names the permanent observation and mult tables.
``'all'`` means both, and is accepted only where reading both makes sense. When no import
prefix is configured the two namespaces are the same tables.
"""

DBRow = dict[str, Any]
"""One row to write, keyed by column name."""

SchemaColumn = dict[str, Any]
"""One column's definition.

A schema read from a packaged ``table_schemas`` JSON file is a list of these, and
`ImportDBSuper.table_info` returns the same shape built from what the server says the
table currently holds.
"""

ResultRow = tuple[Any, ...]
"""One row of a query result, in the order the query named its columns."""

WarningHandler = Callable[..., None]
"""Anything installable as `warnings.showwarning`.

The parameter list is left open because the two sides of that assignment disagree about
it: the warnings machinery always passes six arguments, while the standard library's own
handler makes the last two optional. Naming either shape would reject the other.
"""


class ImportDBError(Exception):
    """Raised when a database operation fails; always aborts the import."""


@dataclass(frozen=True)
class IndexStatement:
    """One statement that adds keys to one table, for `ImportDBSuper.build_indexes`.

    Attributes:
        sql: The statement.
        label: What the statement adds, as the log and ``--timing-json`` name it.
        space_bytes: The server's estimated temporary space for the sort the statement
            runs, which a space budget counts against.
        sort_bytes: The estimated sort of the largest key the statement builds, which
            the connection sizes its sort memory to before running it; 0 for a statement
            that builds no index.
        key_count: How many indexes the statement builds, which the sort memory is
            shared among; 0 for a statement that builds none.
    """

    sql: str
    label: str
    space_bytes: int
    sort_bytes: int
    key_count: int


class _SpaceBudget:
    """Temporary space the index builds running at once share, in bytes.

    A statement takes its estimate from the budget before it runs and returns it after,
    waiting while the statements already running hold too much for it to fit. No
    statement's estimate exceeds the whole budget, which the caller checks, so a waiting
    statement always fits once the others finish.
    """

    def __init__(self, total: int | None) -> None:
        """Start with the whole budget free.

        Parameters:
            total: The budget, or None for no budget, under which nothing waits.
        """
        self._total = total
        self._free = total
        self._condition = threading.Condition()

    @contextlib.contextmanager
    def held(self, space_bytes: int) -> Iterator[None]:
        """Hold a statement's share of the budget while the body runs.

        Parameters:
            space_bytes: The statement's estimate.

        Yields:
            Nothing; the body runs holding the share.
        """
        if self._total is None:
            yield
            return
        with self._condition:
            assert self._free is not None
            self._condition.wait_for(lambda: self._free is not None and self._free >= space_bytes)
            self._free -= space_bytes
        try:
            yield
        finally:
            with self._condition:
                assert self._free is not None
                self._free += space_bytes
                self._condition.notify_all()


class ImportDBSuper:
    """The brand-independent half of the import pipeline's database interface.

    A subclass supplies the SQL for one database brand; this class holds the connection
    parameters, the namespace mapping and the warning collection its methods share.
    Instances are created through `opus_import.importdb.get_db` rather than directly.

    Attributes:
        conn: The open DB-API connection the subclass created. It is declared but not
            assigned here, because opening it is the subclass's job and there is no
            connection before that.
        log_sql: True to log every statement and its parameters at debug level.
        bulk_load: Whether `bulk_load_rows` may load from a scratch file, as the
            configuration's ``[import] bulk_load`` says. A brand that finds the server
            refusing it writes ``INSERT`` statements instead.
        scratch_dir: The directory the bulk load's scratch files go in, or None for the
            system temporary directory.
        transaction_rows: The most rows one bulk load writes in one transaction.
        tables_created: The tables created through this instance, in creation order,
            so a caller can post-process the ones an import run made. A read-only run
            records the tables it would have created.
        direct: True on a fresh import, which writes the permanent observation and mult
            tables directly: ``'import'`` then names those tables in every method, and
            `create_table` creates each of them with only the keys a load needs
            (`opus_import.table_keys.create_time_keys`). Every other table keeps its
            import namespace. Set by the import's choice of path, never by a caller
            otherwise.
    """

    # Any DB-API 2.0 connection; the base class uses only `cursor()` and `commit()`, and
    # cannot name a brand's own connection type without depending on that brand.
    conn: Any

    def __init__(
        self,
        db_hostname: str,
        db_name: str,
        db_schema: str,
        db_user: str,
        db_password: str,
        mult_form_types: Sequence[str] | None = None,
        import_prefix: str | None = None,
        logger: pdslogger.PdsLogger | None = None,
        read_only: bool = False,
        bulk_load: bool = True,
        scratch_dir: str | None = None,
        transaction_rows: int = DEFAULT_TRANSACTION_ROWS,
    ) -> None:
        """Record what a connection needs, without opening one.

        Parameters:
            db_hostname: The database server's host name.
            db_name: The database name. MySQL has no such concept above the schema and
                ignores it.
            db_schema: The schema (MySQL database) holding the OPUS tables.
            db_user: The user to connect as.
            db_password: That user's password.
            mult_form_types: The ``param_info`` form types that have a ``mult_`` table,
                or None for none of them.
            import_prefix: The prefix distinguishing an import table from its permanent
                counterpart, or None to make the two namespaces the same tables.
            logger: Where to report progress, statements and warnings, or None to report
                nothing. With None, the Python-warning collection below is also skipped,
                since there would be nowhere to report the warnings.
            read_only: True to log every mutating statement instead of executing it.
                Reads still run.
            bulk_load: Whether `bulk_load_rows` may load from a scratch file.
            scratch_dir: The directory the bulk load's scratch files go in, or None for
                the system temporary directory.
            transaction_rows: The most rows one bulk load writes in one transaction; at
                least 1.

        Raises:
            ValueError: If `transaction_rows` is less than 1, which would make every bulk
                load write nothing.
        """
        if transaction_rows < 1:
            raise ValueError(f'transaction_rows must be at least 1, not {transaction_rows}')
        self.log_sql = False

        self.db_hostname = db_hostname
        self.db_name = db_name
        self.db_schema = db_schema
        self.db_user = db_user
        self.db_password = db_password
        self.import_prefix = import_prefix
        self.logger = logger
        self.read_only = read_only
        self._mult_form_types = [] if mult_form_types is None else mult_form_types
        self.bulk_load = bulk_load
        self.scratch_dir = scratch_dir
        self.transaction_rows = transaction_rows

        self.tables_created: list[str] = []
        self.direct = False

        self._enter_stack: list[str] = []
        self._cmds_executed: list[str] = []
        self._log_sql_char_limit = 10000

        # Where Python warnings will be written
        self._warning_list: list[str] = []
        self._old_warning_handler: WarningHandler | None = None
        # True only while our handler is installed, so _exit() restores exactly
        # when _enter() installed. A separate flag is needed because
        # _old_warning_handler is reset to None on restore, so it cannot serve
        # as both the sentinel and the saved value.
        self._warning_handler_installed = False

    def _is_prefixed(self, table_name: str) -> bool:
        """Return whether a table name carries the import prefix.

        Parameters:
            table_name: The table name as the database spells it.

        Returns:
            True if an import prefix is configured and the name starts with it, matched
            without regard to case.
        """
        if self.import_prefix is None:
            return False
        return table_name.lower().startswith(self.import_prefix.lower())

    def _is_direct_table(self, raw_table_name: str) -> bool:
        """Return whether ``'import'`` names a table's permanent copy in this run.

        Parameters:
            raw_table_name: The table's raw name.

        Returns:
            True when `direct` is set and the table is an observation or mult table.
        """
        return self.direct and is_key_filtered_table(raw_table_name)

    def _is_import_namespace(self, table_name: str) -> bool:
        """Return whether a table, as the database spells it, is in the import namespace.

        Parameters:
            table_name: The table name as the database spells it.

        Returns:
            With `direct` set, True for an unprefixed observation or mult table and False
            for a prefixed one, which the permanent table stands in for. Otherwise, True
            if an import prefix is configured and the name starts with it, matched
            without regard to case; False when no prefix is configured, because then no
            table belongs to the import namespace alone.
        """
        if self._is_prefixed(table_name):
            raw = table_name[len(self.import_prefix or '') :]
            return not self._is_direct_table(raw)
        return self._is_direct_table(table_name)

    def _is_perm_namespace(self, table_name: str) -> bool:
        """Return whether a table name lacks the import prefix.

        Parameters:
            table_name: The table name as the database spells it.

        Returns:
            True if no import prefix is configured, or the name does not start with it.
        """
        if self.import_prefix is None:
            return True
        return not table_name.lower().startswith(self.import_prefix.lower())

    def convert_raw_to_namespace(self, namespace: Namespace, raw_table_name: str) -> str:
        """Return the name a table has when it is used in the given namespace.

        Parameters:
            namespace: The namespace to name the table in.
            raw_table_name: The table name without any namespace prefix.

        Returns:
            The prefixed name for ``'import'``, and the unchanged name otherwise, when no
            import prefix is configured, or for an observation or mult table under
            `direct`.
        """
        if self.import_prefix is None or self._is_direct_table(raw_table_name):
            return raw_table_name
        if namespace == 'import':
            return self.import_prefix + raw_table_name
        elif namespace == 'perm' or namespace == 'all':
            return raw_table_name
        raise NotImplementedError

    def convert_namespace_to_raw(self, namespace: Namespace, table_name: str) -> str:
        """Return a table's raw name, stripping the prefix the namespace added.

        Parameters:
            namespace: The namespace the name is currently in.
            table_name: The name as the database spells it.

        Returns:
            The name with the import prefix removed for ``'import'``, and the unchanged
            name otherwise, when no import prefix is configured, or for an observation or
            mult table under `direct`.
        """
        if self.import_prefix is None or (
            not self._is_prefixed(table_name) and self._is_direct_table(table_name)
        ):
            return table_name
        if namespace == 'import':
            assert table_name.lower().startswith(self.import_prefix.lower())
            return table_name.replace(self.import_prefix, '').replace(
                self.import_prefix.lower(), ''
            )
        elif namespace == 'perm' or namespace == 'all':
            return table_name
        raise NotImplementedError

    def _execute(
        self,
        cmd: str,
        param_list: Sequence[Any] | None = None,
        cur: Any = None,
        mutates: bool = False,
    ) -> None:
        """Execute one statement, or log it and skip it in a read-only run.

        Parameters:
            cmd: The statement. Any value it compares against or writes must be a `%s`
                placeholder, never text.
            param_list: The parameters those placeholders consume, or None when there
                are none. An empty sequence is not the same as None: MySQLdb interprets
                the statement as a format string whenever parameters are given.
            cur: An open cursor to run on, or None to open one and commit afterwards.
            mutates: True if the statement changes the database, which is what a
                read-only run refuses to execute.
        """
        if self.log_sql and self.logger:
            pretty_cmd = cmd.strip()
            if pretty_cmd.find('\n') >= 0:
                pretty_cmd = '\n' + pretty_cmd
            else:
                pretty_cmd = ' ' + pretty_cmd
            sim_str = ''
            if self.read_only and mutates:
                sim_str = '[SIM] '
            self.logger.log(
                'debug',
                f'{sim_str} SQL COMMAND:'
                + pretty_cmd[: self._log_sql_char_limit]
                + f' PARAMS: {param_list}',
            )
        self._cmds_executed.append(cmd)
        if not self.read_only or not mutates:
            if cur:
                cur.execute(cmd, param_list)
            else:
                with self.conn.cursor() as cur:
                    cur.execute(cmd, param_list)
                    self.conn.commit()

    def _execute_and_fetchall(
        self, cmd: str, func_name: str, param_list: Sequence[Any] | None = None
    ) -> Sequence[ResultRow]:
        """Execute one query and return every row of its result.

        Parameters:
            cmd: The query, parameterized as `_execute` requires.
            func_name: The calling method's name, used in the failure message.
            param_list: The parameters the query's placeholders consume, or None.

        Returns:
            The result rows, in the order the server returned them.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::_execute_and_fetchall must be overridden')

    @staticmethod
    def _make_warning_handler(warning_list: list[str]) -> WarningHandler:
        """Return a `warnings.showwarning` that appends each warning to a list.

        Parameters:
            warning_list: The list to append each warning's text to.

        Returns:
            A handler with `warnings.showwarning`'s signature, which records the message
            alone and discards the category, location and formatted line.
        """

        def _warning_handler(
            message: Warning | str,
            category: type[Warning],
            filename: str,
            lineno: int,
            file: TextIO | None,
            line: str | None,
        ) -> None:
            """Append one warning's text to the captured list.

            Parameters:
                message: The warning, or its text.
                category: The warning class. Not recorded.
                filename: Where the warning was raised. Not recorded.
                lineno: The line it was raised on. Not recorded.
                file: Where the standard handler would have written it. Unused.
                line: The source line, if the caller supplied one. Not recorded.
            """
            warning_list.append(str(message))

        return _warning_handler

    @contextlib.contextmanager
    def _operation(self, func_name: str) -> Iterator[None]:
        """Run the body of a database operation between `_enter` and `_exit`.

        `_exit` runs however the body ends, so an operation that raises still pops the
        nesting stack and puts back the warning handler `_enter` installed.

        Parameters:
            func_name: The calling method's name.

        Yields:
            Nothing; the body runs inside.
        """
        self._enter(func_name)
        try:
            yield
        finally:
            self._exit()

    def _enter(self, func_name: str) -> None:
        """Begin a database operation, starting warning collection at the outermost one.

        Calls nest: only the outermost `_enter` clears the accumulated statements and
        warnings and installs the warning handler, so an operation implemented in terms
        of others still reports as one.

        Parameters:
            func_name: The calling method's name, pushed on the nesting stack.
        """
        self._enter_stack.append(func_name)
        if len(self._enter_stack) == 1:
            self._cmds_executed = []
            self._warning_list = []
            if self.logger:
                self._old_warning_handler = warnings.showwarning
                self._warning_handler_installed = True
                warnings.showwarning = self._make_warning_handler(self._warning_list)

    def _exit(self) -> None:
        """End a database operation, reporting its warnings at the outermost one.

        The outermost `_exit` logs every warning the operation produced, each preceded by
        every statement it ran, and restores the warning handler `_enter` replaced.
        """
        self._enter_stack.pop()
        if len(self._enter_stack) == 0:
            if self.logger and len(self._warning_list) > 0:
                self.logger.log('warning', 'Warnings found during database operation:')
                for cmd in self._cmds_executed:
                    self.logger.log('warning', '  ' + cmd)
                for w in self._warning_list:
                    self.logger.log('warning', '  ' + w)
            # Restore only if we installed (i.e. only when self.logger was set);
            # restoring unconditionally would assign None to
            # warnings.showwarning, and the next warnings.warn() would then
            # raise TypeError.
            if self._warning_handler_installed:
                # The flag is set only where the handler was saved, which is what makes
                # this true; the checker cannot follow the pairing across two methods.
                assert self._old_warning_handler is not None
                warnings.showwarning = self._old_warning_handler
                self._old_warning_handler = None
                self._warning_handler_installed = False

    def quote_identifier(self, s: str) -> str:
        """Return a name quoted for use as an identifier in a statement.

        Parameters:
            s: The table, column or schema name.

        Returns:
            The quoted name.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::quote_identifier must be overridden')

    def open_sibling_connection(self) -> ImportDBSuper:
        """Open a second connection to the same schema, configured as this one is.

        The sibling has no logger: `_enter` and `_exit` swap the process-wide
        `warnings.showwarning`, which is not safe to do from several threads at once, so
        a sibling reports nothing and its caller logs on its behalf. It shares `direct`.

        Returns:
            A new instance of this brand, connected.

        Raises:
            ImportDBError: If the connection fails.
        """
        sibling = type(self)(
            self.db_hostname,
            self.db_name,
            self.db_schema,
            self.db_user,
            self.db_password,
            mult_form_types=self._mult_form_types,
            import_prefix=self.import_prefix,
            logger=None,
            read_only=self.read_only,
            bulk_load=self.bulk_load,
            scratch_dir=self.scratch_dir,
            transaction_rows=self.transaction_rows,
        )
        sibling.direct = self.direct
        return sibling

    def build_indexes(
        self,
        table_to_statements: Mapping[str, Sequence[IndexStatement]],
        *,
        workers: int = 1,
        server_tmpdir: str | None = None,
        space_budget: int | None = None,
        serial: bool = False,
    ) -> dict[str, list[tuple[str, float]]]:
        """Run statements that add keys, different tables at once across sibling connections.

        Each table's statements run in order on one connection. Up to ``workers`` tables
        build at once, each over a sibling connection of its own (`open_sibling_connection`),
        unless ``serial`` asks for one table at a time on this connection. Every
        connection is prepared for the builds first (`_prepare_index_session`), and sizes
        its sort memory to each statement before running it (`_size_index_sort`). Under a
        space budget a statement waits until its estimate fits beside the statements
        already running. A failed statement stops its table's later statements; the
        other tables finish, and the failures are raised together once every table is
        done.

        Parameters:
            table_to_statements: Each table's statements, keyed by raw table name. A table
                with none is skipped.
            workers: The most tables that build at once; at least 1.
            server_tmpdir: The directory on the database server's host its sorts write
                to, or None to leave the server's setting.
            space_budget: The temporary space, in bytes, the statements running at once
                may hold together, or None for no budget. No statement's estimate may
                exceed it.
            serial: True to build one table at a time on this connection.

        Returns:
            Each table's statements, keyed by table, as ``(label, seconds)`` pairs in the
            order they ran, the table's own logged duration being their sum.

        Raises:
            ImportDBError: If any statement failed, naming every failure.
            ValueError: If ``workers`` is less than 1, or a statement's estimate exceeds
                the budget, before anything runs.
        """
        if workers < 1:
            raise ValueError(f'workers must be at least 1, not {workers}')
        tables = [table for table in sorted(table_to_statements) if table_to_statements[table]]
        if space_budget is not None:
            for table in tables:
                for statement in table_to_statements[table]:
                    if statement.space_bytes > space_budget:
                        raise ValueError(
                            f'{table}: {statement.label} needs an estimated '
                            f'{statement.space_bytes} bytes of temporary space, more than the '
                            f'{space_budget} available'
                        )
        budget = _SpaceBudget(space_budget)
        durations: dict[str, list[tuple[str, float]]] = {}
        failures: list[str] = []

        def build_table(db: ImportDBSuper, table: str) -> list[tuple[str, float]]:
            """Run one table's statements in order on one connection.

            Parameters:
                db: The connection to run them on.
                table: The table.

            Returns:
                Each statement's label and seconds.
            """
            timed: list[tuple[str, float]] = []
            for statement in table_to_statements[table]:
                with budget.held(statement.space_bytes):
                    db._size_index_sort(statement.sort_bytes, statement.key_count)
                    started = time.perf_counter()
                    db.run_ddl(statement.sql)
                    timed.append((statement.label, time.perf_counter() - started))
            return timed

        def report(table: str, timed: list[tuple[str, float]]) -> None:
            """Record and log one finished table.

            Parameters:
                table: The table.
                timed: Its statements' labels and seconds.
            """
            durations[table] = timed
            if self.logger:
                self.logger.log(
                    'info', f'  Built keys on "{table}" in {sum(s for _, s in timed):.2f} s'
                )

        if serial or workers == 1:
            self._prepare_index_session(1 if serial else workers, server_tmpdir)
            for table in tables:
                try:
                    report(table, build_table(self, table))
                except ImportDBError as e:
                    failures.append(f'{table}: {e}')
        else:
            local = threading.local()
            siblings: list[ImportDBSuper] = []
            siblings_lock = threading.Lock()

            def build_on_sibling(table: str) -> list[tuple[str, float]]:
                """Run one table's statements on this thread's sibling connection.

                Parameters:
                    table: The table.

                Returns:
                    Each statement's label and seconds.
                """
                sibling = getattr(local, 'sibling', None)
                if sibling is None:
                    sibling = self.open_sibling_connection()
                    try:
                        sibling._prepare_index_session(workers, server_tmpdir)
                    except BaseException:
                        sibling.close()
                        raise
                    local.sibling = sibling
                    with siblings_lock:
                        siblings.append(sibling)
                return build_table(sibling, table)

            try:
                with ThreadPoolExecutor(max_workers=workers) as pool:
                    futures = {pool.submit(build_on_sibling, table): table for table in tables}
                    for future in as_completed(futures):
                        table = futures[future]
                        try:
                            report(table, future.result())
                        except ImportDBError as e:
                            failures.append(f'{table}: {e}')
            finally:
                for sibling in siblings:
                    sibling.close()
        if failures:
            message = 'Building keys failed: ' + '; '.join(sorted(failures))
            if self.logger:
                self.logger.log('fatal', message)
            raise ImportDBError(message)
        return durations

    def _prepare_index_session(self, workers: int, server_tmpdir: str | None) -> None:
        """Set this connection's session up for building indexes.

        Parameters:
            workers: How many connections build at once, which the server's sort memory
                is divided among.
            server_tmpdir: The directory on the database server's host its sorts write
                to, or None to leave the server's setting.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::_prepare_index_session must be overridden')

    def _size_index_sort(self, sort_bytes: int, key_count: int) -> None:
        """Size this connection's sort memory for the next statement that builds indexes.

        Parameters:
            sort_bytes: The estimated sort of the largest key the statement builds.
            key_count: How many indexes the statement builds.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::_size_index_sort must be overridden')

    def run_ddl(self, cmd: str) -> None:
        """Run one statement that changes a table's definition.

        Parameters:
            cmd: The statement, which carries no parameters.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::run_ddl must be overridden')

    def close(self) -> None:
        """Close the connection.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::close must be overridden')

    def read_table_keys(self, namespace: Namespace) -> dict[str, list[TableKey]]:
        """Return the keys every table of a namespace has, as the server reports them.

        Parameters:
            namespace: The namespace to read.

        Returns:
            Each table's keys, keyed by raw table name; a table with no key is absent.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::read_table_keys must be overridden')

    def add_keys_statement(
        self, namespace: Namespace, raw_table_name: str, keys: Sequence[TableKey]
    ) -> str:
        """Return one statement that adds plain, unique or primary keys to a table.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            keys: The keys to add; no foreign key.

        Returns:
            The statement.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::add_keys_statement must be overridden')

    def add_foreign_key_statement(
        self, namespace: Namespace, raw_table_name: str, key: TableKey
    ) -> str:
        """Return one statement that adds a foreign key to a table.

        Parameters:
            namespace: The namespace holding the table and the one it references.
            raw_table_name: The table, without its namespace prefix.
            key: The foreign key.

        Returns:
            The statement.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::add_foreign_key_statement must be overridden')

    def add_foreign_keys(self, statements: Sequence[IndexStatement]) -> list[tuple[str, float]]:
        """Add foreign keys one at a time, without checking the rows already there.

        Parameters:
            statements: The statements, from `add_foreign_key_statement`.

        Returns:
            Each statement's label and seconds, in the order they ran.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::add_foreign_keys must be overridden')

    def key_space_bytes(
        self,
        namespace: Namespace,
        raw_table_name: str,
        schema: Sequence[SchemaColumn],
        key: TableKey,
    ) -> int:
        """Estimate the temporary space the server's sort needs to build one key.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            schema: The table's schema, which gives its columns' widths.
            key: The key.

        Returns:
            The estimate, in bytes.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::key_space_bytes must be overridden')

    def index_space_budget(self, server_tmpdir: str | None) -> int | None:
        """Return the temporary space the index builds running at once may hold together.

        Parameters:
            server_tmpdir: The directory on the database server's host its sorts write
                to, or None when none is configured.

        Returns:
            The budget in bytes, or None when there is none to enforce.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::index_space_budget must be overridden')

    def table_names(
        self, namespace: Namespace, prefix: str | list[str] | tuple[str, ...] | None = None
    ) -> Collection[str]:
        """Return the names of the tables in a namespace.

        Parameters:
            namespace: The namespace to list.
            prefix: One prefix, or several, that a name must start with; None for every
                name.

        Returns:
            The matching table names, sorted. An implementation must sort them, because a
            caller handing out row ids while iterating this would otherwise produce a
            different database on a different machine.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::table_names must be overridden')

    def table_exists(self, namespace: Namespace, table_name: str) -> bool:
        """Return whether a table exists in a namespace.

        Parameters:
            namespace: The namespace to look in.
            table_name: The table, without its namespace prefix.

        Returns:
            True if a table of that name exists, matched without regard to case, because
            table names are case-sensitive on some operating systems and not others.
        """
        with self._operation('table_exists'):
            table_names = [x.lower() for x in self.table_names(namespace)]
        return table_name.lower() in table_names

    def table_info(self, namespace: Namespace, raw_table_name: str) -> list[SchemaColumn]:
        """Return the columns of a table as the database currently defines them.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.

        Returns:
            One dictionary per column, in the table's column order.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::table_info must be overridden')

    def drop_table(
        self, namespace: Namespace, raw_table_name: str, ignore_if_not_exists: bool = True
    ) -> None:
        """Delete a table.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            ignore_if_not_exists: True to do nothing when the table is absent, False to
                treat that as a failure.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::drop_table must be overridden')

    def rename_tables_atomically(
        self,
        namespace: Namespace,
        renames: Sequence[tuple[str, str]],
        *,
        lock_wait_timeout_s: int,
        attempts: int,
    ) -> None:
        """Rename several tables in one statement, which takes effect all at once or not at all.

        A reader sees every table under its old name or every table under its new one,
        never a mixture and never a moment with a name missing. The renames apply in
        order, so a pair may name a table an earlier pair just freed.

        Parameters:
            namespace: The namespace holding every table named.
            renames: ``(from, to)`` raw table names, in the order they apply.
            lock_wait_timeout_s: How long one attempt waits for the tables' locks, which
                a reader's open transaction holds, before it gives up.
            attempts: How many times to try before the wait is a failure.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::rename_tables_atomically must be overridden')

    def create_table(
        self,
        namespace: Namespace,
        raw_table_name: str,
        schema: Sequence[SchemaColumn],
        ignore_if_exists: bool = True,
    ) -> bool:
        """Create a table from an OPUS table schema.

        Parameters:
            namespace: The namespace to create the table in.
            raw_table_name: The table, without its namespace prefix.
            schema: The column definitions, as `opus_import.import_util` read them from
                the packaged JSON schema.
            ignore_if_exists: True to leave an existing table alone, False to attempt the
                creation regardless.

        Returns:
            True if the table was created, False if it already existed and
            ``ignore_if_exists`` was True.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::create_table must be overridden')

    def analyze_table(self, namespace: Namespace, raw_table_name: str) -> None:
        """Recompute a table's key distribution statistics.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::analyze_table must be overridden')

    def read_rows(
        self,
        namespace: Namespace,
        raw_table_name: str,
        column_names: Sequence[str],
        where: str | None = None,
        where_params: Sequence[Any] | None = None,
    ) -> Sequence[ResultRow]:
        """Return the given columns of the rows the WHERE clause selects.

        Parameters:
            namespace: 'import', 'perm' or 'all'.
            raw_table_name: The table, without its namespace prefix.
            column_names: The columns to read, quoted and validated here.
            where: The WHERE clause, or None for every row. Any value it
                compares against must be a `%s` placeholder, never text.
            where_params: The parameters that clause's placeholders consume.

        Returns:
            One tuple per row, with the values in ``column_names`` order.
        """
        with self._operation('read_rows'):
            table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

            q = self.quote_identifier
            columns = ','.join([q(c) for c in column_names])

            # Identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$). The
            # caller's `where` fragment is appended verbatim below and is not
            # validated; only the values inside it are bound, through where_params.
            # This method is for trusted callers.
            cmd = f'SELECT {columns} FROM {q(table_name)}'  # nosec B608
            if where:
                cmd += f' WHERE {where}'
            res = self._execute_and_fetchall(
                cmd, 'read_rows', list(where_params) if where_params else None
            )
        return res

    def insert_row(self, namespace: Namespace, raw_table_name: str, row: DBRow) -> None:
        """Insert one row.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            row: The values to write, keyed by column name.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::insert_row must be overridden')

    def insert_rows(self, namespace: Namespace, raw_table_name: str, rows: Sequence[DBRow]) -> None:
        """Insert many rows.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            rows: The rows to write. Every row must have the same columns.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::insert_rows must be overridden')

    def bulk_load_rows(
        self, namespace: Namespace, raw_table_name: str, rows: Sequence[DBRow]
    ) -> None:
        """Write many rows the fastest way the server allows.

        A brand loads them from a scratch file where the server accepts one, at most
        `transaction_rows` rows to a transaction, and checks after each load that every
        row arrived unchanged; otherwise it writes them as `insert_rows` does.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            rows: The rows to write. Every row must have the same columns.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::bulk_load_rows must be overridden')

    def update_row(
        self,
        namespace: Namespace,
        raw_table_name: str,
        row: DBRow,
        where: str,
        where_params: Sequence[Any] | None = None,
    ) -> None:
        """Assign new values to the columns of the rows a WHERE clause selects.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            row: The values to assign, keyed by column name.
            where: The WHERE clause. Any value it compares against must be a `%s`
                placeholder, never text.
            where_params: The parameters that clause's placeholders consume.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::update_row must be overridden')

    def upsert_row(
        self, namespace: Namespace, raw_table_name: str, key_name: str, row: DBRow
    ) -> None:
        """Insert one row, or update it if its key is already present.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            key_name: The column identifying the row, which is written on an insert but
                never assigned on an update.
            row: The values to write, keyed by column name.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::upsert_row must be overridden')

    def upsert_rows(
        self, namespace: Namespace, raw_table_name: str, key_name: str, rows: Sequence[DBRow]
    ) -> None:
        """Insert many rows, updating each one whose key is already present.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            key_name: The column identifying a row, which is written on an insert but
                never assigned on an update.
            rows: The rows to write. They need not share a column set.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::upsert_rows must be overridden')

    def delete_rows(
        self,
        namespace: Namespace,
        raw_table_name: str,
        where: str | None = None,
        where_params: Sequence[Any] | None = None,
        *,
        all_rows: bool = False,
    ) -> None:
        """Delete the rows a WHERE clause selects, or every row when asked to.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            where: The WHERE clause. Any value it compares against must be a `%s`
                placeholder, never text.
            where_params: The parameters that clause's placeholders consume.
            all_rows: True to delete every row, which is the only way to; ``where`` must
                then be None.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::delete_rows must be overridden')

    def copy_rows_between_namespaces(
        self,
        src_namespace: Namespace,
        dest_namespace: Namespace,
        raw_table_name: str,
        where: str | None = None,
        where_params: Sequence[Any] | None = None,
    ) -> None:
        """Copy rows of one table from one namespace to the same table in another.

        Parameters:
            src_namespace: The namespace to read from.
            dest_namespace: The namespace to write to.
            raw_table_name: The table, without its namespace prefix.
            where: The WHERE clause selecting the rows to copy, or None for every row.
                Any value it compares against must be a `%s` placeholder, never text.
            where_params: The parameters that clause's placeholders consume.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::copy_rows_between_namespaces must be overridden')

    def general_select(
        self, cmd: str, param_list: Sequence[Any] | None = None
    ) -> Sequence[ResultRow]:
        """Run a query the caller assembled and return every row.

        Parameters:
            cmd: Everything after the SELECT keyword.
            param_list: The parameters that query's placeholders consume.

        Returns:
            One tuple per row, in the order the query named its columns.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::general_select must be overridden')

    def find_column_max(self, namespace: Namespace, raw_table_name: str, column_name: str) -> Any:
        """Return the largest value in a column.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            column_name: The column to take the maximum of.

        Returns:
            The maximum, or None if the table has no rows.

        Raises:
            NotImplementedError: Always; a brand subclass must override this.
        """
        raise NotImplementedError('ImportDBSuper::find_column_max must be overridden')

"""The MySQL implementation of the import pipeline's database interface.

`ImportDBMySQL` is the one brand `opus_import.importdb.get_db` can return. It renders the
OPUS table schemas as MySQL DDL and builds the statements that read and write rows.

Every identifier it emits is validated against a strict pattern and then backtick-quoted,
and the row statements bind their values as parameters rather than formatting them into
the text. The DDL is the exception: `ImportDBMySQL.create_table` formats a column's
default and its enum option list straight into the statement, which is safe only because
those come from the table schemas packaged with `opus_import` and never from input.

Observation rows are written by `ImportDBMySQL.bulk_load_rows`, which loads them from a
scratch file with ``LOAD DATA LOCAL INFILE`` when the server allows it and checks the
server's counts after every load, since such a load skips a duplicate key and turns a
value it cannot store into a warning rather than failing. Where the server refuses local
files, it writes ``INSERT`` statements instead, and the import log says which path ran.

The driver is imported defensively, so that the module still imports without
``mysqlclient`` installed and a package-wide sweep -- Sphinx autodoc, or a test
collection -- does not fail on it. An instance built without the driver forces itself
read-only and discards every statement rather than running or logging it, so it reports
no tables and reads no rows; it is not a simulation anything can be driven through.
"""

from __future__ import annotations

import contextlib
import numbers
import os
import re
import tempfile
import time
from typing import TYPE_CHECKING, Any

try:
    import MySQLdb

    MYSQLDB_AVAILABLE = True
except ImportError:
    MYSQLDB_AVAILABLE = False

from opus_config.config import DEFAULT_TRANSACTION_ROWS
from opus_import.importdb.super import (
    DBRow,
    ImportDBError,
    ImportDBSuper,
    IndexStatement,
    ResultRow,
    SchemaColumn,
)
from opus_import.table_keys import (
    KeyKind,
    OnDelete,
    TableKey,
    create_time_keys,
    declared_keys,
    is_key_filtered_table,
)

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

    import pdslogger

ERR_UNKNOWN_DATABASE = 1049

#: The SQL type each fixed ``field_type`` of a table schema renders as. Two more forms
#: are rendered by `create_table` itself: a width type (`MYSQL_WIDTH_FIELD_TYPE`), and
#: ``enum``, whose values come from the column's ``field_enum_options``.
MYSQL_FIELD_TYPE_SQL: dict[str, str] = {
    'int1': 'tinyint',
    'int2': 'smallint',
    'int3': 'mediumint',
    'int4': 'int',
    'int8': 'bigint',
    'uint1': 'tinyint unsigned',
    'uint2': 'smallint unsigned',
    'uint3': 'mediumint unsigned',
    'uint4': 'int unsigned',
    'uint8': 'bigint unsigned',
    'real4': 'float',
    'real8': 'double',
    'text': 'text',
    'mult_list': 'JSON',
    'json': 'JSON',
    # A flag and a mult index both hold the id of a mult table row.
    'flag_yesno': 'int unsigned',
    'flag_onoff': 'int unsigned',
    'mult_idx': 'int unsigned',
    'timestamp': 'timestamp',
    'datetime': 'datetime',
    # A SHA-256 digest, stored as its bytes.
    'binary32': 'binary(32)',
}

#: A ``field_type`` that names a character type and its width, such as ``char12`` or
#: ``varchar255``: the type, then the width.
MYSQL_WIDTH_FIELD_TYPE = re.compile(r'(char|varchar)([1-9][0-9]*)')

#: The ``field_type`` whose values a column lists in ``field_enum_options``.
MYSQL_ENUM_FIELD_TYPE = 'enum'


def _free_bytes(path: str) -> int | None:
    """Return the bytes free to an unprivileged writer on a directory's filesystem.

    Parameters:
        path: The directory.

    Returns:
        The free bytes, or None when the path cannot be read from here.
    """
    try:
        stat = os.statvfs(path)
    except OSError:
        return None
    return stat.f_bavail * stat.f_frsize


def is_renderable_field_type(field_type: str) -> bool:
    """Return whether `ImportDBMySQL.create_table` can render a ``field_type``.

    Parameters:
        field_type: The value of a column's ``field_type``.

    Returns:
        True for a key of `MYSQL_FIELD_TYPE_SQL`, a `MYSQL_WIDTH_FIELD_TYPE` or
        `MYSQL_ENUM_FIELD_TYPE`.
    """
    return (
        field_type in MYSQL_FIELD_TYPE_SQL
        or MYSQL_WIDTH_FIELD_TYPE.fullmatch(field_type) is not None
        or field_type == MYSQL_ENUM_FIELD_TYPE
    )


#: The bytes one value of a fixed ``field_type`` takes in an index entry, for the space
#: estimate of an index build (`ImportDBMySQL.key_space_bytes`). A width type takes up to
#: four bytes a character, utf8mb4's widest, and a ``varchar`` two more for its length; a
#: type absent here cannot be indexed without a prefix and is estimated by
#: `MYSQL_UNSIZED_KEY_BYTES`.
MYSQL_KEY_BYTES: dict[str, int] = {
    'int1': 1,
    'int2': 2,
    'int3': 3,
    'int4': 4,
    'int8': 8,
    'uint1': 1,
    'uint2': 2,
    'uint3': 3,
    'uint4': 4,
    'uint8': 8,
    'real4': 4,
    'real8': 8,
    'flag_yesno': 4,
    'flag_onoff': 4,
    'mult_idx': 4,
    'timestamp': 4,
    'datetime': 5,
    'enum': 2,
    'binary32': 32,
}

#: The index-entry bytes assumed for a column type `MYSQL_KEY_BYTES` does not size: the
#: most an index key prefix may take under InnoDB's DYNAMIC row format.
MYSQL_UNSIZED_KEY_BYTES = 3072

#: The bytes an index entry carries beyond its key and the primary key, in the estimate
#: ``rows x (key bytes + primary key bytes + 10) x 1.3``.
MYSQL_INDEX_ENTRY_OVERHEAD = 10

#: The factor the estimate allows for the sort's own overhead.
MYSQL_INDEX_SORT_FACTOR = 1.3

#: The host names that put the server on the computer running the import, where a
#: directory on the server's host can be read from here.
LOCAL_HOSTS = frozenset({'localhost', '127.0.0.1', '::1'})

#: The largest ``innodb_ddl_buffer_size`` the server accepts.
MYSQL_MAX_DDL_BUFFER_SIZE = 4_294_967_295

#: The smallest ``innodb_ddl_buffer_size`` the server accepts.
MYSQL_MIN_DDL_BUFFER_SIZE = 65_536

#: The server's "lock wait timeout exceeded", which a statement fails with when it waited
#: ``lock_wait_timeout`` seconds for a table another session holds.
ERR_LOCK_WAIT_TIMEOUT = 1205

#: The errors that mean the server or the connection refuses ``LOAD DATA LOCAL INFILE``:
#: the server's "not allowed" (1148) and "loading local data is disabled" (3948), and the
#: client library's own refusal of the server's file request (2068).
ERRS_LOCAL_INFILE_REFUSED = frozenset({1148, 2068, 3948})

#: What the import log names as the bulk-load path, on a line starting
#: `BULK_LOAD_PATH_PREFIX`.
BULK_LOAD_PATH_FILE = 'LOAD DATA LOCAL INFILE'
BULK_LOAD_PATH_INSERT = 'insert_rows packets'
BULK_LOAD_PATH_PREFIX = 'Bulk load path: '

# The counts the server reports after a LOAD DATA statement, as `Connection.info` returns
# them: "Records: 3  Deleted: 0  Skipped: 0  Warnings: 0".
_LOAD_INFO_RE = re.compile(
    r'Records:\s*(?P<records>\d+)\s+Deleted:\s*\d+\s+Skipped:\s*(?P<skipped>\d+)\s+'
    r'Warnings:\s*(?P<warnings>\d+)'
)

# The characters LOAD DATA's default escape rules need escaped in a field: the escape
# character itself, the field and line terminators, and the two control characters a
# terminator scan could otherwise misread. Each becomes a backslash sequence the load
# reads back as the original character.
_LOAD_DATA_ESCAPES = str.maketrans(
    {'\\': '\\\\', '\t': '\\t', '\n': '\\n', '\r': '\\r', '\0': '\\0'}
)

# The only identifier shape OPUS uses: table, column and schema names come from
# the checked-in table schemas, from the configuration, and from bundle ids, and
# none of them ever needs a character outside this set. Backticks quote an
# identifier but do not escape a backtick inside one, so validating the name is
# what keeps a computed identifier from ending the quoting early.
_IDENTIFIER_RE = re.compile(r'\A[A-Za-z0-9_]+\Z')


def load_data_text(value: Any) -> str:
    """Return one value as a field of the text ``LOAD DATA`` reads.

    The text is the statement's default format: fields separated by tabs, rows ended
    by newlines, ``\\N`` for NULL, and a backslash before each tab, newline, carriage
    return, NUL or backslash in a value. A value is rendered the way `insert_rows` would
    have sent it, so the two paths store the same thing: a float by its ``repr``, which
    names the exact double; a boolean as ``1`` or ``0``, as the driver sends one; and
    anything else, a JSON string included, as its text.

    Parameters:
        value: The value of one column of one row.

    Returns:
        The field's text, escaped.

    Raises:
        TypeError: If the value is bytes, which no column a load writes holds and which
            the text has no faithful rendering for.
    """
    if value is None:
        return '\\N'
    if isinstance(value, bool):
        return '1' if value else '0'
    if isinstance(value, numbers.Integral):
        return str(int(value))
    if isinstance(value, float):
        return float.__repr__(value)
    if isinstance(value, (bytes, bytearray)):
        raise TypeError(f'a bulk load cannot write bytes: {value!r}')
    return str(value).translate(_LOAD_DATA_ESCAPES)


class _LocalInfileRefusedError(Exception):
    """Raised by a load the server or the connection refused to read a local file for."""


class ImportDBMySQL(ImportDBSuper):
    """The import pipeline's database interface, rendered as MySQL.

    Attributes:
        default_engine: The storage engine every table is created with.
        mysql_version: The server's version string, or ``'Simulated'`` when the driver is
            absent.
        bulk_load_path: How `bulk_load_rows` writes rows: `BULK_LOAD_PATH_FILE` or
            `BULK_LOAD_PATH_INSERT`.
    """

    # Note that for MySQL, we ignore the db_name and only use the schema_name
    def __init__(
        self,
        db_hostname: str,
        db_name: str,
        db_schema: str,
        db_user: str,
        db_password: str,
        mult_form_types: Sequence[str] | None = None,
        logger: pdslogger.PdsLogger | None = None,
        read_only: bool = False,
        bulk_load: bool = True,
        scratch_dir: str | None = None,
        transaction_rows: int = DEFAULT_TRANSACTION_ROWS,
    ) -> None:
        """Open the connection to a MySQL server, creating the schema if it is absent.

        A read-only connection never creates the schema: an absent one is an error.

        The parameters are `ImportDBSuper`'s, and ``db_name`` is ignored: MySQL has no
        level above the schema. Once connected, the session is set up for the import's
        writes (`_prepare_import_session`).

        Parameters:
            db_hostname: The MySQL server's host name.
            db_name: Unused.
            db_schema: The schema (MySQL database) holding the OPUS tables. It is
                created if the server does not already have it, unless ``read_only``.
            db_user: The user to connect as.
            db_password: That user's password.
            mult_form_types: The ``param_info`` form types that have a ``mult_`` table,
                or None for none of them.
            logger: Where to report progress, statements and warnings, or None to report
                nothing.
            read_only: True to log every mutating statement instead of executing it.
            bulk_load: Whether `bulk_load_rows` may load from a scratch file. True also
                lets the connection send local files.
            scratch_dir: The directory the scratch files go in, or None for the system
                temporary directory.
            transaction_rows: The most rows one bulk load writes in one transaction.

        Raises:
            ImportDBError: If the server cannot be reached, the schema can be neither
                used nor created, the schema is absent on a read-only connection, or the
                session's SQL mode cannot be set.
            ValueError: If `transaction_rows` is less than 1, before anything connects.
        """
        super().__init__(
            db_hostname,
            db_name,
            db_schema,
            db_user,
            db_password,
            mult_form_types=mult_form_types,
            logger=logger,
            read_only=read_only,
            bulk_load=bulk_load,
            scratch_dir=scratch_dir,
            transaction_rows=transaction_rows,
        )
        self.bulk_load_path = BULK_LOAD_PATH_INSERT
        self._ddl_buffer_bounds: tuple[int, int, int] | None = None
        self._ddl_buffer_size: int | None = None
        with self._operation('__init__'):
            self._table_info_cache: dict[str, list[SchemaColumn]] = {}

            if not MYSQLDB_AVAILABLE:
                self.read_only = True
                if self.logger:
                    self.logger.log(
                        'warning',
                        'Python package MySQLdb not available - simulating all '
                        + 'database accesses!',
                    )

            self.default_engine = 'INNODB'

            if not MYSQLDB_AVAILABLE:
                self.conn = None
                if self.logger:
                    self.logger.log(
                        'info',
                        f'[SIM] Connected to MySQL server "{self.db_hostname}" '
                        + f'as "{self.db_user}"',
                    )
            else:
                try:
                    self.conn = MySQLdb.connect(
                        host=self.db_hostname,
                        user=self.db_user,
                        passwd=self.db_password,
                        local_infile=self.bulk_load,
                    )
                except MySQLdb.Error as e:
                    if self.logger:
                        self.logger.log(
                            'fatal',
                            'Unable to connect to MySQL server ' + f'"{self.db_hostname}": {e}',
                        )
                    raise ImportDBError(e) from e

                if self.logger:
                    self.logger.log(
                        'info',
                        f'Connected to MySQL server "{self.db_hostname}" ' + f'as "{self.db_user}"',
                    )

                try:
                    cmd = f'USE {self.quote_identifier(self.db_schema)}'
                    self._execute(cmd)
                except MySQLdb.Error as e:
                    err_code = e.args[0] if e.args else None
                    if err_code == ERR_UNKNOWN_DATABASE and self.read_only:
                        message = (
                            f'Database "{self.db_schema}" does not exist, and a read-only '
                            'run does not create it'
                        )
                        if self.logger:
                            self.logger.log('fatal', message)
                        raise ImportDBError(message) from e
                    if err_code == ERR_UNKNOWN_DATABASE:
                        try:
                            cmd = f'CREATE DATABASE {self.quote_identifier(self.db_schema)}'
                            self._execute(cmd)
                        except MySQLdb.Error as create_err:
                            if self.logger:
                                self.logger.log(
                                    'fatal',
                                    f'Unable to create new database "{self.db_schema}"'
                                    + f': {create_err}',
                                )
                            raise ImportDBError(create_err) from create_err
                        if self.logger:
                            self.logger.log('warning', f'  Created new database "{self.db_schema}"')

                        try:
                            cmd = f'USE {self.quote_identifier(self.db_schema)}'
                            self._execute(cmd)
                        except MySQLdb.Error as use_err:
                            if self.logger:
                                self.logger.log(
                                    'fatal',
                                    'Unable to use new database '
                                    + f'"{self.db_schema}": {use_err}',
                                )
                            raise ImportDBError(use_err) from use_err
                    else:
                        if self.logger:
                            self.logger.log(
                                'fatal',
                                'Unable to use existing database ' + f'"{self.db_schema}": {e}',
                            )
                        raise ImportDBError(e) from e

            if self.logger:
                self.logger.log('info', f'  Using database "{self.db_schema}"')

            # We keep a cached list of table names so we don't have to keep doing
            # SQL queries - go ahead and populate it now
            self._table_names: set[str] | None = None
            self.table_names('all')
            assert self._table_names is not None

            # A list of all the tables we've created so we know which ones we have
            # to do post-processing on
            self.tables_created = []

            if not MYSQLDB_AVAILABLE:
                self.mysql_version = 'Simulated'
            else:
                cmd = 'SELECT VERSION()'
                res = self._execute_and_fetchall(cmd, '__init__')
                self.mysql_version = res[0][0]
                if self.logger:
                    self.logger.log('info', f'  MySQL version: {self.mysql_version}')

                try:
                    cmd = (
                        "set sql_mode = 'NO_ZERO_DATE,NO_ZERO_IN_DATE,"
                        'ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,'
                        'STRICT_ALL_TABLES'
                    )
                    if self.mysql_version[0] == '5':
                        cmd += ',NO_AUTO_CREATE_USER'
                    cmd += "'"
                    self._execute(cmd)
                except MySQLdb.Error as e:
                    if self.logger:
                        self.logger.log('fatal', f'Failed to set STRICT_ALL_TABLES mode: {e}')
                    raise ImportDBError(e) from e

                self._prepare_import_session()

    def _prepare_import_session(self) -> None:
        """Choose the bulk-load path, and keep the import's writes out of the binary log.

        Both depend on server settings an administrator controls, so each is changed
        here where the account may and reported where it may not; neither stops the
        import. Every line goes to the log at info level, since a warning would read as
        a defect in the import rather than in the server's configuration. A read-only run
        writes nothing, so it changes neither and writes `INSERT` statements it never
        sends.
        """
        if self.read_only:
            self._log_bulk_load_path('a read-only run')
            return
        local_infile, log_bin = self._execute_and_fetchall(
            'SELECT @@GLOBAL.local_infile, @@GLOBAL.log_bin', '__init__'
        )[0]
        if not self.bulk_load:
            self._log_bulk_load_path('[import] bulk_load is false')
        elif local_infile:
            self.bulk_load_path = BULK_LOAD_PATH_FILE
            self._log_bulk_load_path()
        else:
            try:
                self._execute('SET GLOBAL local_infile = ON')
            except MySQLdb.Error as e:
                self._log_bulk_load_path(
                    'the server refuses local files and this account may not change that '
                    f'({e}); an administrator can run "SET GLOBAL local_infile = ON", or set '
                    "local_infile = ON in the server's configuration"
                )
            else:
                if self.logger:
                    self.logger.log('info', "  Turned on the server's local_infile")
                self.bulk_load_path = BULK_LOAD_PATH_FILE
                self._log_bulk_load_path()
        if log_bin:
            try:
                self._execute('SET sql_log_bin = 0')
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log(
                        'info',
                        '  The server writes a binary log and this account may not turn it '
                        f'off for the import ({e}); starting the server with --skip-log-bin, '
                        'or granting the account SESSION_VARIABLES_ADMIN, saves writing '
                        'every imported row to it',
                    )
            else:
                if self.logger:
                    self.logger.log('info', "  The import's writes skip the binary log")

    def _log_bulk_load_path(self, reason: str | None = None) -> None:
        """Log which path `bulk_load_rows` writes rows by, on the line the harness reads.

        Parameters:
            reason: Why the path is `BULK_LOAD_PATH_INSERT`, or None for no reason.
        """
        if self.logger:
            because = '' if reason is None else f' ({reason})'
            self.logger.log('info', f'  {BULK_LOAD_PATH_PREFIX}{self.bulk_load_path}{because}')

    def _execute(
        self,
        cmd: str,
        param_list: Sequence[Any] | None = None,
        cur: Any = None,
        mutates: bool = False,
    ) -> None:
        """Execute one statement, or do nothing at all when the driver is absent.

        Parameters:
            cmd: The statement, parameterized as `ImportDBSuper._execute` requires.
            param_list: The parameters its placeholders consume, or None.
            cur: An open cursor to run on, or None to open one and commit afterwards.
            mutates: True if the statement changes the database.
        """
        if not MYSQLDB_AVAILABLE:
            return
        super()._execute(cmd, param_list, cur=cur, mutates=mutates)

    def _execute_and_fetchall(
        self, cmd: str, func_name: str, param_list: Sequence[Any] | None = None
    ) -> Sequence[ResultRow]:
        """Execute one query and return every row of its result.

        Parameters:
            cmd: The query, parameterized as `ImportDBSuper._execute` requires.
            func_name: The calling method's name, used in the failure message.
            param_list: The parameters its placeholders consume, or None.

        Returns:
            The result rows, in the order the server returned them, or no rows at all
            when the driver is absent.

        Raises:
            ImportDBError: If the server rejects the query.
        """
        if not MYSQLDB_AVAILABLE:
            return []

        try:
            with self.conn.cursor() as cur:
                self._execute(cmd, param_list, cur=cur)
                self.conn.commit()
                rows: Sequence[ResultRow] = cur.fetchall()
                return rows
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal', f'Failed in {func_name}: {e}')
            raise ImportDBError(e) from e

    def quote_identifier(self, s: str) -> str:
        """Return `s` backtick-quoted for use as an identifier.

        Parameters:
            s: The table, column or schema name.

        Returns:
            The name wrapped in backticks.

        Raises:
            ImportDBError: If the name is not made up solely of ASCII letters,
                digits and underscores.
        """
        if not isinstance(s, str) or not _IDENTIFIER_RE.match(s):
            raise ImportDBError(f'Unsafe SQL identifier: {s!r}')
        return '`' + s + '`'

    def _quoted_column_list(self, column_names: Sequence[str]) -> str:
        """Return the column names quoted and comma-separated.

        Parameters:
            column_names: The columns, in the order they should appear.

        Returns:
            The quoted names joined by commas, ready for a column list.

        Raises:
            ImportDBError: If any name is not a legal identifier.
        """
        return ','.join(self.quote_identifier(c) for c in column_names)

    @staticmethod
    def _row_placeholders(row: DBRow, column_names: Sequence[str], param_list: list[Any]) -> str:
        """Append a row's values to param_list and return their placeholders.

        Every value is a parameter, including None: MySQLdb renders that as NULL,
        so no value is ever formatted into the statement text.

        Parameters:
            row: The values to write, keyed by column name.
            column_names: The columns to take, in the order the statement names them.
            param_list: The statement's parameter list, extended in place.

        Returns:
            One `%s` per column, comma-separated.
        """
        for column_name in column_names:
            param_list.append(row[column_name])
        return ','.join(['%s'] * len(column_names))

    def table_names(
        self, prefix: str | list[str] | tuple[str, ...] | None = None
    ) -> Collection[str]:
        """Return the names of the tables in the schema.

        The names are read from the server once and cached, so a run that creates and
        drops tables through this instance never re-queries for them.

        Parameters:
            prefix: One prefix, or several, that a name must start with; None for every
                name.

        Returns:
            The matching table names, sorted. That order is part of the contract, because
            a caller handing out row ids while iterating this would otherwise produce a
            different database on a different machine. Every path returns a new list.
        """
        with self._operation('table_names'):
            if self._table_names is None:
                cmd = """
SELECT `TABLE_NAME` FROM `INFORMATION_SCHEMA`.`TABLES` WHERE
`TABLE_TYPE`='BASE TABLE' AND `TABLE_SCHEMA`=%s"""
                res = self._execute_and_fetchall(cmd, 'table_names', [self.db_schema])
                # Note: SQL table names are case-insensitive on SOME OSes and this
                # query returns them in whatever case SQL returns them in.
                # But table_exists does a case-insensitive match.
                self._table_names = {x[0] for x in res}
                # if self.logger:
                #     self.logger.log('debug',
                #             f'  Current table names: {sorted(self._table_names)}')

        # Sorted, because the cache is a set filled from a query with no ORDER BY, so
        # its iteration order depends on both the hash seed and the order the server
        # happened to return rows in. A caller that hands out row ids in this order --
        # `do_param_info` does -- would otherwise give the same database different ids on
        # different machines, which is a difference nothing else can explain.
        ret_names = sorted(self._table_names)

        if prefix is None:
            return ret_names

        if isinstance(prefix, (list, tuple)):
            ret_list: list[str] = []
            for name in ret_names:
                for p in prefix:
                    if name.startswith(p):
                        ret_list.append(name)
                        break
            return ret_list

        return [x for x in ret_names if x.startswith(prefix)]

    def table_info(self, table_name: str) -> list[SchemaColumn]:
        """Return the columns of a table as the server currently defines them.

        The answer is cached per table and discarded whenever a table is created or
        dropped through this instance.

        Parameters:
            table_name: The table.

        Returns:
            One dictionary per column, in the table's column order, each carrying
            ``field_name``, ``field_default``, ``field_notnull`` and the OPUS
            ``field_type`` the server's own type maps to. A table the server does not
            have produces no columns rather than an error. This is the cached list
            itself, so a caller that reorders or edits it changes what every later call
            returns.

        Raises:
            NotImplementedError: If a column has a server type OPUS has no name for.
        """
        if table_name in self._table_info_cache:
            return self._table_info_cache[table_name]
        with self._operation('table_info'):
            cmd = """
SELECT `COLUMN_NAME`, `COLUMN_DEFAULT`, `IS_NULLABLE`, `DATA_TYPE`,
`CHARACTER_MAXIMUM_LENGTH`, `COLUMN_TYPE`
FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`=%s AND
`TABLE_NAME`=%s ORDER BY `ORDINAL_POSITION`"""
            rows = self._execute_and_fetchall(cmd, 'table_info', [self.db_schema, table_name])

            column_list = []

            for row in rows:
                (column_name, column_default, is_nullable, data_type, char_len, column_type) = row
                if data_type == 'tinyint':
                    field_type = 'int1'
                elif data_type == 'smallint':
                    field_type = 'int2'
                elif data_type == 'mediumint':
                    field_type = 'int3'
                elif data_type == 'int':
                    field_type = 'int4'
                elif data_type == 'bigint':
                    field_type = 'int8'
                elif data_type == 'char':
                    field_type = f'char({char_len})'
                elif data_type == 'varchar':
                    field_type = f'varchar({char_len})'
                elif data_type == 'float':
                    field_type = 'real4'
                elif data_type == 'double':
                    field_type = 'real8'
                elif data_type == 'enum':
                    field_type = 'enum'
                elif data_type == 'json':
                    field_type = 'json'
                elif data_type == 'timestamp':
                    field_type = 'timestamp'
                elif data_type == 'datetime':
                    field_type = 'datetime'
                elif data_type == 'binary' and char_len == 32:
                    field_type = 'binary32'
                elif data_type == 'text':
                    field_type = 'text'
                elif data_type == 'mult_list':
                    field_type = 'mult_list'
                else:
                    raise NotImplementedError(data_type)
                if field_type.startswith('int') and column_type.find('unsigned') != -1:
                    field_type = 'u' + field_type

                column_dict = {
                    'field_name': column_name,
                    'field_default': column_default,
                    'field_notnull': is_nullable == 'NO',
                    'field_type': field_type,
                }
                column_list.append(column_dict)

        self._table_info_cache[table_name] = column_list
        return column_list

    def drop_table(self, table_name: str, ignore_if_not_exists: bool = True) -> None:
        """Delete the given table if it exists.

        Parameters:
            table_name: The table.
            ignore_if_not_exists: True to do nothing when the table is absent.

        Raises:
            ImportDBError: If the table is absent and ``ignore_if_not_exists`` is False,
                or the server rejects the statement.
        """
        with self._operation('drop_table'):
            # table_exists caches the table names, which we need below for read_only
            if not self.table_exists(table_name):
                if ignore_if_not_exists:
                    if self.logger:
                        self.logger.log('debug', f'drop_table "{table_name}" - no table found')
                else:
                    if self.logger:
                        self.logger.log(
                            'fatal', f'Attempted to drop table "{table_name}" that doesn\'t exist'
                        )
                    raise ImportDBError()
            else:
                try:
                    cmd = f'DROP TABLE {self.quote_identifier(table_name)}'
                    self._execute(cmd, mutates=True)
                except MySQLdb.Error as e:
                    if self.logger:
                        self.logger.log('fatal', f'Failed in drop_table on "{table_name}": {e}')
                    raise ImportDBError(e) from e

                if self.logger:
                    if self.read_only:
                        self.logger.log('debug', f'[SIM] Dropped table "{table_name}"')
                    else:
                        self.logger.log('debug', f'Dropped table "{table_name}"')

                # __init__ populates the cache and nothing clears it, so it is a set from
                # the moment the instance exists; the None is only the load-once sentinel.
                assert self._table_names is not None
                if table_name in self._table_names:
                    self._table_names.remove(table_name)
                else:
                    assert table_name.lower() in self._table_names, table_name
                    self._table_names.remove(table_name.lower())

            self._table_info_cache.clear()

    def rename_tables_atomically(
        self,
        renames: Sequence[tuple[str, str]],
        *,
        lock_wait_timeout_s: int,
        attempts: int,
    ) -> None:
        """Rename several tables with one ``RENAME TABLE``, which MySQL applies atomically.

        A foreign key follows the table it references through a rename, and a key name the
        server generated from the old table name is renamed with it.

        Each attempt runs with the session's ``lock_wait_timeout`` lowered to
        ``lock_wait_timeout_s``, so a rename waiting behind a reader's transaction does not
        in turn hold up every reader queued behind it for the server's default of a year.
        A timed-out attempt is logged at info level and tried again; the session's own
        value is restored afterwards.

        Parameters:
            renames: ``(from, to)`` table names, in the order they apply.
            lock_wait_timeout_s: How long one attempt waits for the tables' locks.
            attempts: How many times to try before the wait is a failure.

        Raises:
            ImportDBError: If the server rejects the statement, or every attempt timed out.
            ValueError: If ``attempts`` is less than 1, before anything is changed.
        """
        if attempts < 1:
            raise ValueError(f'attempts must be at least 1, not {attempts}')
        with self._operation('rename_tables_atomically'):
            q = self.quote_identifier
            cmd = 'RENAME TABLE ' + ', '.join(f'{q(old)} TO {q(new)}' for old, new in renames)
            if self.read_only:
                self._execute(cmd, mutates=True)
                if self.logger:
                    self.logger.log('debug', f'[SIM] Renamed tables: {cmd}')
                return

            previous = self._execute_and_fetchall(
                'SELECT @@SESSION.lock_wait_timeout', 'rename_tables_atomically'
            )[0][0]
            self._execute('SET SESSION lock_wait_timeout = %s', [lock_wait_timeout_s])
            try:
                for attempt in range(1, attempts + 1):
                    try:
                        self._execute(cmd, mutates=True)
                        break
                    except MySQLdb.Error as e:
                        if e.args and e.args[0] == ERR_LOCK_WAIT_TIMEOUT and attempt < attempts:
                            if self.logger:
                                self.logger.log(
                                    'info',
                                    f'  RENAME TABLE waited {lock_wait_timeout_s} s for a lock '
                                    f'(attempt {attempt} of {attempts}); trying again',
                                )
                            continue
                        if self.logger:
                            self.logger.log('fatal', f'Failed in RENAME TABLE: {e}')
                        raise ImportDBError(e) from e
            finally:
                self._execute('SET SESSION lock_wait_timeout = %s', [previous])

            if self.logger:
                self.logger.log('debug', f'Renamed tables: {cmd}')
            assert self._table_names is not None
            for old, new in renames:
                if old in self._table_names:
                    self._table_names.remove(old)
                else:
                    self._table_names.remove(old.lower())
                self._table_names.add(new)
            self._table_info_cache.clear()

    def create_table(
        self,
        table_name: str,
        schema: Sequence[SchemaColumn],
        ignore_if_exists: bool = True,
    ) -> bool:
        """Create a new table from the given OPUS table schema.

        The table carries every key its schema declares, except an observation or mult
        table, which carries only the keys a load needs
        (`opus_import.table_keys.create_time_keys`); finalization adds the rest.

        Parameters:
            table_name: The table.
            schema: The column definitions, as `opus_import.import_util` read them from
                the packaged JSON schema. An entry carrying ``constraint`` contributes
                that text instead of a column; one carrying ``pi_referred_slug``
                describes a ``param_info`` row rather than a column and is skipped.
            ignore_if_exists: True to leave an existing table alone.

        Returns:
            True if the table was created, False if it already existed and
            ``ignore_if_exists`` was True.

        Raises:
            ImportDBError: If the server rejects the statement.
            NotImplementedError: If a column has a ``field_type`` MySQL has no rendering
                for.
        """
        with self._operation('create_table'):
            if ignore_if_exists and self.table_exists(table_name):
                return False

            cmd = ''

            for column in schema:
                if 'pi_referred_slug' in column:
                    continue
                if 'field_name' not in column and 'constraint' not in column:
                    # A table-level key, which the key clauses below render.
                    continue

                if cmd != '':
                    cmd += ',\n'

                if 'constraint' in column:
                    cmd += '  ' + column['constraint'] + '\n'
                    continue

                field_name = column['field_name']
                field_type = column['field_type']

                cmd += f'  {self.quote_identifier(field_name)} '
                width_type = MYSQL_WIDTH_FIELD_TYPE.fullmatch(field_type)
                if field_type in MYSQL_FIELD_TYPE_SQL:
                    cmd += MYSQL_FIELD_TYPE_SQL[field_type]
                elif width_type is not None:
                    cmd += f'{width_type[1]}({width_type[2]})'
                elif field_type == MYSQL_ENUM_FIELD_TYPE:
                    enum_str = column.get('field_enum_options', None)
                    assert enum_str, (table_name, column)
                    cmd += f'enum({enum_str})'
                else:
                    raise NotImplementedError(field_type)

                field_default = column.get('field_default', 'NULL')
                if field_default is None:
                    field_default = 'NULL'
                if column.get('field_notnull', False):
                    cmd += ' NOT NULL'
                    if field_default == 'NULL':
                        field_default = ''

                if field_type == 'timestamp':
                    field_default = 'CURRENT_TIMESTAMP'

                if field_default != '':
                    if (
                        field_default != 'NULL'
                        and field_default != 'CURRENT_TIMESTAMP'
                        and not field_default.isdigit()
                    ):
                        field_default = "'" + field_default + "'"
                    cmd += f' DEFAULT {field_default}'

                if column.get('field_autoincrement', False):
                    cmd += ' AUTO_INCREMENT'

                if field_type == 'timestamp':
                    cmd += ' ON UPDATE CURRENT_TIMESTAMP'

                foreign_key = column.get('field_key_foreign', False)
                assert not foreign_key or column.get('field_key') == 'foreign'

            if is_key_filtered_table(table_name):
                keys = create_time_keys(table_name, schema)
            else:
                keys = declared_keys(schema)
            key_cmd = ',\n'.join(f'  {self._create_key_clause(key)}' for key in keys)
            if key_cmd != '':
                cmd += ',\n' + key_cmd
            cmd = f'CREATE TABLE {self.quote_identifier(table_name)} (\n' + cmd + '\n)'
            cmd += f' ENGINE={self.default_engine}\n'

            try:
                self._execute(cmd, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed to create table "{table_name}": {e}')
                raise ImportDBError(e) from e

            if self.logger:
                if self.read_only:
                    self.logger.log('debug', f'[SIM] Created table "{table_name}"')
                else:
                    self.logger.log('debug', f'Created table "{table_name}"')
            if not self.read_only:
                # A read-only run created nothing, so the cache does not claim it did:
                # a later read of the table would expect it to be there.
                assert self._table_names is not None
                self._table_names.add(table_name)

            self.tables_created.append(table_name)
            self._table_info_cache.clear()

        return True

    def _create_key_clause(self, key: TableKey) -> str:
        """Return a key as a ``CREATE TABLE`` clause names it.

        A plain or unique key is named after its first column, as the server would name
        it, and a foreign key is left for the server to name.

        Parameters:
            key: The key.

        Returns:
            The clause.
        """
        q = self.quote_identifier
        columns = ', '.join(q(column) for column in key.columns)
        if key.kind == 'primary':
            return f'PRIMARY KEY ({columns})'
        if key.kind == 'foreign':
            assert key.references is not None
            table, referenced = key.references
            referenced_columns = ', '.join(q(column) for column in referenced)
            return (
                f'FOREIGN KEY ({columns}) REFERENCES '
                f'{q(table)}({referenced_columns}) '
                f'ON DELETE {key.on_delete.upper()} ON UPDATE CASCADE'
            )
        prefix = 'UNIQUE KEY' if key.kind == 'unique' else 'KEY'
        return f'{prefix} {q(key.columns[0])} ({columns})'

    def add_keys_statement(self, table_name: str, keys: Sequence[TableKey]) -> str:
        """Return one ``ALTER TABLE`` that adds plain, unique or primary keys to a table.

        The keys are unnamed, so the server names each after its first column, as it
        would have in ``CREATE TABLE``, or with a suffix where that name is taken.

        Parameters:
            table_name: The table.
            keys: The keys to add; no foreign key.

        Returns:
            The statement.
        """
        q = self.quote_identifier
        clauses = []
        for key in keys:
            assert key.kind != 'foreign', key
            columns = ', '.join(q(column) for column in key.columns)
            kind = {'primary': 'PRIMARY KEY', 'unique': 'UNIQUE KEY', 'key': 'KEY'}[key.kind]
            clauses.append(f'ADD {kind} ({columns})')
        return f'ALTER TABLE {q(table_name)} ' + ', '.join(clauses)

    def add_foreign_key_statement(self, table_name: str, key: TableKey) -> str:
        """Return one ``ALTER TABLE`` that adds a foreign key to a table.

        Parameters:
            table_name: The table.
            key: The foreign key.

        Returns:
            The statement, rendered as ``CREATE TABLE`` renders the key.
        """
        clause = self._create_key_clause(key)
        return f'ALTER TABLE {self.quote_identifier(table_name)} ADD {clause}'

    def read_table_keys(self) -> dict[str, list[TableKey]]:
        """Return the keys every table in the schema has, from ``information_schema``.

        Plain, unique and primary keys come from ``STATISTICS``, and foreign keys from
        ``KEY_COLUMN_USAGE`` joined to ``REFERENTIAL_CONSTRAINTS``; a ``FULLTEXT`` or
        spatial index is not a key here and is left out.

        Returns:
            Each table's keys, keyed by table name, plain, unique and primary keys
            first, in the order the server lists them; a table with no key is absent.

        Raises:
            ImportDBError: If the server rejects a query.
        """
        index_rows = self._execute_and_fetchall(
            """
SELECT `TABLE_NAME`, `INDEX_NAME`, `NON_UNIQUE`, `COLUMN_NAME`, `INDEX_TYPE`
FROM `INFORMATION_SCHEMA`.`STATISTICS` WHERE `TABLE_SCHEMA`=%s
ORDER BY `TABLE_NAME`, `INDEX_NAME`, `SEQ_IN_INDEX`""",
            'read_table_keys',
            [self.db_schema],
        )
        foreign_rows = self._execute_and_fetchall(
            """
SELECT `k`.`TABLE_NAME`, `k`.`CONSTRAINT_NAME`, `k`.`COLUMN_NAME`,
`k`.`REFERENCED_TABLE_NAME`, `k`.`REFERENCED_COLUMN_NAME`, `r`.`DELETE_RULE`
FROM `INFORMATION_SCHEMA`.`KEY_COLUMN_USAGE` `k`
JOIN `INFORMATION_SCHEMA`.`REFERENTIAL_CONSTRAINTS` `r`
ON `r`.`CONSTRAINT_SCHEMA`=`k`.`CONSTRAINT_SCHEMA`
AND `r`.`CONSTRAINT_NAME`=`k`.`CONSTRAINT_NAME` AND `r`.`TABLE_NAME`=`k`.`TABLE_NAME`
WHERE `k`.`TABLE_SCHEMA`=%s
ORDER BY `k`.`TABLE_NAME`, `k`.`CONSTRAINT_NAME`, `k`.`ORDINAL_POSITION`""",
            'read_table_keys',
            [self.db_schema],
        )

        indexes: dict[tuple[str, str], tuple[KeyKind, list[str]]] = {}
        for table_name, index_name, non_unique, column_name, index_type in index_rows:
            if index_type not in ('BTREE', 'HASH'):
                continue
            kind: KeyKind
            if index_name == 'PRIMARY':
                kind = 'primary'
            elif int(non_unique) == 0:
                kind = 'unique'
            else:
                kind = 'key'
            indexes.setdefault((table_name, index_name), (kind, []))[1].append(column_name)
        foreign: dict[tuple[str, str], tuple[str, list[str], list[str], OnDelete]] = {}
        for table_name, constraint_name, column_name, ref_table, ref_column, rule in foreign_rows:
            on_delete: OnDelete = 'cascade' if rule == 'CASCADE' else 'restrict'
            entry = foreign.setdefault(
                (table_name, constraint_name), (ref_table, [], [], on_delete)
            )
            entry[1].append(column_name)
            entry[2].append(ref_column)

        keys: dict[str, list[TableKey]] = {}
        for (table_name, _index_name), (kind, columns) in indexes.items():
            keys.setdefault(table_name, []).append(TableKey(kind, tuple(columns)))
        for (table_name, _name), (ref_table, columns, ref_columns, on_delete) in foreign.items():
            keys.setdefault(table_name, []).append(
                TableKey('foreign', tuple(columns), (ref_table, tuple(ref_columns)), on_delete)
            )
        return keys

    def key_space_bytes(
        self,
        table_name: str,
        schema: Sequence[SchemaColumn],
        key: TableKey,
    ) -> int:
        """Estimate the temporary space the server's sort needs to build one key.

        The estimate is ``rows x (key bytes + primary key bytes + 10) x 1.3``, with the
        rows the server's statistics count and each column's bytes from
        `MYSQL_KEY_BYTES`.

        Parameters:
            table_name: The table.
            schema: The table's schema, which gives its columns' types.
            key: The key.

        Returns:
            The estimate, in bytes.

        Raises:
            ImportDBError: If the server rejects the query.
        """
        res = self._execute_and_fetchall(
            'SELECT `TABLE_ROWS` FROM `INFORMATION_SCHEMA`.`TABLES` WHERE `TABLE_SCHEMA`=%s '
            'AND `TABLE_NAME`=%s',
            'key_space_bytes',
            [self.db_schema, table_name],
        )
        rows = int(res[0][0] or 0) if res else 0
        types = {
            column['field_name']: column['field_type']
            for column in schema
            if 'field_name' in column
        }
        primary = [k for k in declared_keys(schema) if k.kind == 'primary']
        primary_columns = primary[0].columns if primary else ()

        def width(columns: Sequence[str]) -> int:
            """Return the index-entry bytes of some columns' values together."""
            total = 0
            for column in columns:
                field_type = types.get(column, '')
                width_type = MYSQL_WIDTH_FIELD_TYPE.fullmatch(field_type)
                if field_type in MYSQL_KEY_BYTES:
                    total += MYSQL_KEY_BYTES[field_type]
                elif width_type is not None:
                    total += 4 * int(width_type[2]) + (2 if width_type[1] == 'varchar' else 0)
                else:
                    total += MYSQL_UNSIZED_KEY_BYTES
            return total

        entry = width(key.columns) + width(primary_columns) + MYSQL_INDEX_ENTRY_OVERHEAD
        return int(rows * entry * MYSQL_INDEX_SORT_FACTOR)

    def index_space_budget(self, server_tmpdir: str | None) -> int | None:
        """Return the temporary space the index builds running at once may hold together.

        There is a budget only when the server shares this computer (its host is one of
        `LOCAL_HOSTS`) and ``server_tmpdir`` is given and is a directory this process can
        read the free space of: the budget is that free space, or the server's data
        directory's when that is less and readable too. A path read on any other host
        would be this computer's directory of that name, not the server's.

        Parameters:
            server_tmpdir: The directory on the database server's host its sorts write
                to, or None when none is configured.

        Returns:
            The budget in bytes, or None.

        Raises:
            ImportDBError: If the server rejects the query.
        """
        if server_tmpdir is None or self.db_hostname not in LOCAL_HOSTS:
            return None
        free = _free_bytes(server_tmpdir)
        if free is None:
            return None
        datadir = self._execute_and_fetchall('SELECT @@GLOBAL.datadir', 'index_space_budget')
        if datadir:
            datadir_free = _free_bytes(str(datadir[0][0]))
            if datadir_free is not None:
                free = min(free, datadir_free)
        return free

    def _prepare_index_session(self, workers: int, server_tmpdir: str | None) -> None:
        """Bound this session's sort memory for index builds, and point its sorts at a directory.

        Where the server has ``innodb_ddl_buffer_size``, what `_size_index_sort` sizes
        each statement's buffer from is recorded: the session's value as the server sets
        it, this connection's share of the sort memory -- a quarter of the buffer pool
        divided by ``workers``, so the builds running at once hold at most a quarter of
        the pool together -- and ``innodb_ddl_threads``, which is left at the server's
        value. ``innodb_tmpdir`` is set only when ``server_tmpdir`` is given.

        Parameters:
            workers: How many connections build at once.
            server_tmpdir: The directory on the database server's host its sorts write
                to, or None to leave the server's setting.

        Raises:
            ImportDBError: If the server refuses a setting.
        """
        if not MYSQLDB_AVAILABLE or self.read_only:
            return
        res = self._execute_and_fetchall(
            "SHOW VARIABLES WHERE `Variable_name` IN ('innodb_ddl_buffer_size', "
            "'innodb_ddl_threads', 'innodb_buffer_pool_size')",
            '_prepare_index_session',
        )
        variables = {str(name): int(value) for name, value in res}
        if 'innodb_ddl_buffer_size' in variables:
            current = variables['innodb_ddl_buffer_size']
            share = variables['innodb_buffer_pool_size'] // 4 // workers
            threads = max(1, variables.get('innodb_ddl_threads', 1))
            self._ddl_buffer_bounds = (current, share, threads)
            self._ddl_buffer_size = current
        if server_tmpdir is not None:
            try:
                self._execute('SET SESSION innodb_tmpdir = %s', [server_tmpdir])
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed to prepare the session for index builds: {e}')
                raise ImportDBError(e) from e

    def _size_index_sort(self, sort_bytes: int, key_count: int) -> None:
        """Size this session's ``innodb_ddl_buffer_size`` for the next index build.

        The server holds a whole buffer for each index it is building at once -- every
        index the statement adds, up to ``innodb_ddl_threads`` of them -- so the ceiling
        is this connection's share divided by that many, and a buffer far larger than
        the sort costs time on every index while saving none. The size is the estimate,
        raised to the session's value as the server sets it, within that ceiling and the
        server's limits on the variable. The session is changed only when the size
        differs from its current one. Nothing is set on a server without the variable or
        before the session was prepared.

        Parameters:
            sort_bytes: The estimated sort of the largest key the statement builds.
            key_count: How many indexes the statement builds.

        Raises:
            ImportDBError: If the server refuses the setting.
        """
        if self._ddl_buffer_bounds is None:
            return
        current, share, threads = self._ddl_buffer_bounds
        ceiling = share // max(1, min(key_count, threads))
        ceiling = max(MYSQL_MIN_DDL_BUFFER_SIZE, min(MYSQL_MAX_DDL_BUFFER_SIZE, ceiling))
        size = min(ceiling, max(current, sort_bytes))
        if size == self._ddl_buffer_size:
            return
        try:
            self._execute('SET SESSION innodb_ddl_buffer_size = %s', [size])
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal', f'Failed to size the sort for an index build: {e}')
            raise ImportDBError(e) from e
        self._ddl_buffer_size = size

    def run_ddl(self, cmd: str) -> None:
        """Run one statement that changes a table's definition.

        Parameters:
            cmd: The statement, which carries no parameters.

        Raises:
            ImportDBError: If the server rejects it.
        """
        with self._operation('run_ddl'):
            try:
                self._execute(cmd, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed in "{cmd}": {e}')
                raise ImportDBError(e) from e
            self._table_info_cache.clear()

    def set_next_id(self, table_name: str, next_id: int) -> None:
        """Make the next row a table's auto-increment key hands out take a given id.

        Parameters:
            table_name: The table, whose primary key is an auto-increment column.
            next_id: The id the next row is given.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        self.run_ddl(
            f'ALTER TABLE {self.quote_identifier(table_name)} AUTO_INCREMENT = {int(next_id)}'
        )

    def add_foreign_keys(self, statements: Sequence[IndexStatement]) -> list[tuple[str, float]]:
        """Add foreign keys one at a time, with ``foreign_key_checks`` off.

        With the checks off, ``ADD FOREIGN KEY`` is an in-place change that does not read
        the rows already there; the import's validation counts orphans instead. The
        session's checks are turned back on however the statements end.

        Parameters:
            statements: The statements, from `add_foreign_key_statement`.

        Returns:
            Each statement's label and seconds, in the order they ran.

        Raises:
            ImportDBError: If the server rejects a statement.
        """
        timed: list[tuple[str, float]] = []
        if not statements:
            return timed
        with self.foreign_keys_unchecked():
            for statement in statements:
                started = time.perf_counter()
                self.run_ddl(statement.sql)
                timed.append((statement.label, time.perf_counter() - started))
        return timed

    def _set_foreign_key_checks(self, enabled: bool) -> None:
        """Set the session's ``foreign_key_checks``.

        Parameters:
            enabled: True to check foreign keys, False not to.
        """
        self._execute(f'SET SESSION foreign_key_checks = {1 if enabled else 0}')

    def close(self) -> None:
        """Close the connection; an instance without the driver has none to close."""
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def socket_descriptor(self) -> int | None:
        """Return the file descriptor of the connection's socket.

        Returns:
            The descriptor, or None when there is no open connection.
        """
        if self.conn is None:
            return None
        descriptor: int = self.conn.fileno()
        return descriptor

    def analyze_table(self, table_name: str) -> None:
        """Analyze the given table. This recomputes key distribution.

        Parameters:
            table_name: The table.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        with self._operation('analyze_table'):
            cmd = f'ANALYZE TABLE {self.quote_identifier(table_name)}'

            try:
                self._execute(cmd, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed to analyze table "{table_name}": {e}')
                raise ImportDBError(e) from e

            if self.logger:
                if self.read_only:
                    self.logger.log('debug', f'[SIM] Analyzed table "{table_name}"')
                else:
                    self.logger.log('debug', f'Analyzed table "{table_name}"')

    def insert_row(self, table_name: str, row: DBRow) -> None:
        """Insert one row.

        Parameters:
            table_name: The table.
            row: The values to write, keyed by column name.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        with self._operation('insert_row'):
            sorted_column_names = sorted(row.keys())
            param_list: list[Any] = []
            placeholders = self._row_placeholders(row, sorted_column_names, param_list)
            # Table and column names are the only interpolations and identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$);
            # every row value is a %s placeholder bound through param_list.
            cmd = (
                f'INSERT INTO {self.quote_identifier(table_name)} '  # nosec B608
                f'({self._quoted_column_list(sorted_column_names)}) '
                f'VALUES({placeholders})'
            )

            try:
                self._execute(cmd, param_list, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed to insert row into "{table_name}": {e}')
                raise ImportDBError(e) from e

    def insert_rows(self, table_name: str, rows: Sequence[DBRow]) -> None:
        """Insert multiple rows, a thousand at a time.

        Parameters:
            table_name: The table.
            rows: The rows to write. All rows must have the same columns; an empty
                sequence writes nothing.

        Raises:
            ImportDBError: If the server rejects a statement.
        """

        if len(rows) == 0:
            return

        with self._operation('insert_rows'):
            packet_size = 1000  # Limit number of rows at a time - MySQL barfs

            num_packets = ((len(rows) - 1) // packet_size) + 1

            for packet_num in range(num_packets):
                start_row = packet_size * packet_num
                end_row = min(len(rows), packet_size * (packet_num + 1))

                sorted_column_names = sorted(rows[0].keys())

                param_list: list[Any] = []
                value_tuples = []
                for row in rows[start_row:end_row]:
                    assert sorted_column_names == sorted(row.keys()), (
                        sorted_column_names,
                        sorted(row.keys()),
                    )
                    placeholders = self._row_placeholders(row, sorted_column_names, param_list)
                    value_tuples.append(f'({placeholders})')

                cmd = (
                    f'INSERT INTO {self.quote_identifier(table_name)} '
                    f'({self._quoted_column_list(sorted_column_names)}) VALUES'
                    + ','.join(value_tuples)
                )

                try:
                    self._execute(cmd, param_list, mutates=True)
                except MySQLdb.Error as e:
                    if self.logger:
                        self.logger.log('fatal', f'Failed to insert row into "{table_name}": {e}')
                    raise ImportDBError(e) from e

    def bulk_load_rows(self, table_name: str, rows: Sequence[DBRow]) -> None:
        """Write many rows with ``LOAD DATA LOCAL INFILE``, or as `insert_rows` does.

        The rows go in chunks of at most `transaction_rows`. Each chunk is written to a
        scratch file of its own, made by `tempfile.mkstemp` in `scratch_dir` so that two
        imports sharing the directory never touch each other's file, then loaded and
        committed as one transaction, and the file is deleted however the load ends.
        Rows are written to the file one at a time from ``rows``, never copied into a
        list of their own.

        After each load the server's counts are checked (`_check_load`), and a chunk
        that did not arrive whole and unchanged is rolled back and raised. Where the
        server or the connection refuses local files, at the start of the run or at
        this load, this chunk and every later one are written by `insert_rows`, and the
        log says so.

        Parameters:
            table_name: The table.
            rows: The rows to write. Every row must have the same columns; an empty
                sequence writes nothing.

        Raises:
            ImportDBError: If a load is refused for any other reason, or does not write
                every row of its chunk unchanged.
        """
        if len(rows) == 0:
            return
        if self.bulk_load_path != BULK_LOAD_PATH_FILE:
            self.insert_rows(table_name, rows)
            return
        with self._operation('bulk_load_rows'):
            column_names = sorted(rows[0].keys())
            for start in range(0, len(rows), self.transaction_rows):
                end = min(len(rows), start + self.transaction_rows)
                try:
                    self._load_chunk(table_name, column_names, rows, start, end)
                except _LocalInfileRefusedError as e:
                    self.bulk_load_path = BULK_LOAD_PATH_INSERT
                    self._log_bulk_load_path(f'the server refused a local file: {e}')
                    self.insert_rows(table_name, rows[start:])
                    return

    def _load_chunk(
        self,
        table_name: str,
        column_names: Sequence[str],
        rows: Sequence[DBRow],
        start: int,
        end: int,
    ) -> None:
        """Write rows ``start`` to ``end`` to a scratch file and load it.

        Parameters:
            table_name: The table, as the server names it.
            column_names: The columns, in the order the file holds them.
            rows: Every row of the load.
            start: The first row of the chunk.
            end: One past its last row.

        Raises:
            ImportDBError: If the load fails or does not write every row unchanged.
            _LocalInfileRefusedError: If the server or the connection refuses the file.
        """
        fd, path = tempfile.mkstemp(dir=self.scratch_dir, prefix=f'{table_name}_', suffix='.tsv')
        try:
            columns = set(column_names)
            # newline='' writes each '\n' as itself on every platform, which is the line
            # terminator the statement names.
            with os.fdopen(fd, 'w', encoding='utf-8', newline='') as scratch:
                for index in range(start, end):
                    row = rows[index]
                    assert row.keys() == columns, (column_names, sorted(row.keys()))
                    scratch.write(
                        '\t'.join(load_data_text(row[name]) for name in column_names) + '\n'
                    )
            self._load_file(table_name, column_names, path, end - start)
        finally:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(path)

    def _load_file(
        self, table_name: str, column_names: Sequence[str], path: str, row_count: int
    ) -> None:
        """Load one scratch file into a table as one transaction, and check the result.

        Parameters:
            table_name: The table, as the server names it.
            column_names: The columns, in the order the file holds them.
            path: The scratch file.
            row_count: How many rows the file holds.

        Raises:
            ImportDBError: If the load fails or does not write every row unchanged; the
                transaction is rolled back first.
            _LocalInfileRefusedError: If the server or the connection refuses the file.
        """
        # The table and column names are validated by quote_identifier
        # (^[A-Za-z0-9_]+$), and the file name travels as a parameter. CHARACTER SET is
        # required: the statement reads the file in character_set_database and ignores
        # SET NAMES. The FIELDS and LINES clauses are the statement's defaults, written
        # out so the format `load_data_text` writes is stated beside the statement.
        cmd = (
            f'LOAD DATA LOCAL INFILE %s INTO TABLE {self.quote_identifier(table_name)} '
            "CHARACTER SET utf8mb4 FIELDS TERMINATED BY '\\t' ESCAPED BY '\\\\' "
            f"LINES TERMINATED BY '\\n' ({self._quoted_column_list(column_names)})"
        )
        try:
            with self.conn.cursor() as cur:
                self._execute(cmd, [path], cur=cur, mutates=True)
                problem = self._check_load(cur, row_count)
                if problem is not None:
                    self.conn.rollback()
                    if self.logger:
                        self.logger.log('fatal', f'Bulk load into "{table_name}": {problem}')
                    raise ImportDBError(f'Bulk load into "{table_name}": {problem}')
                self.conn.commit()
        except MySQLdb.Error as e:
            self.conn.rollback()
            if e.args and e.args[0] in ERRS_LOCAL_INFILE_REFUSED:
                raise _LocalInfileRefusedError(e) from e
            if self.logger:
                self.logger.log('fatal', f'Failed to bulk load into "{table_name}": {e}')
            raise ImportDBError(e) from e

    def _check_load(self, cur: Any, row_count: int) -> str | None:
        """Return what went wrong with the load just run on a cursor, or None.

        ``LOAD DATA LOCAL`` behaves as though ``IGNORE`` were given, even under
        ``STRICT_ALL_TABLES``: a row whose key is already present is skipped, and a value
        the column cannot hold is converted with a warning. Neither raises, so the
        server's counts for the statement are what show it. The counts belong to this
        connection's last statement, so another connection loading at the same time
        cannot change them.

        Parameters:
            cur: The cursor the load ran on.
            row_count: How many rows the file held.

        Returns:
            None when the server read every row and skipped none, with no warnings;
            otherwise the counts, and the first warning's text when there is one.
        """
        info = self.conn.info()
        match = _LOAD_INFO_RE.search(info or '')
        if match is None:
            return f'the server reported no counts for the load ({info!r})'
        records = int(match['records'])
        skipped = int(match['skipped'])
        warning_count = int(match['warnings'])
        if records == row_count and skipped == 0 and warning_count == 0:
            return None
        problem = f'{records} rows read of {row_count}, {skipped} skipped, {warning_count} warnings'
        if warning_count > 0:
            self._execute('SHOW WARNINGS LIMIT 1', cur=cur)
            first = cur.fetchone()
            if first is not None:
                problem += f'; the first: {first[2]}'
        return problem

    def update_row(
        self,
        table_name: str,
        row: DBRow,
        where: str,
        where_params: Sequence[Any] | None = None,
    ) -> None:
        """Assign new values to the columns of the rows a WHERE clause selects.

        Parameters:
            table_name: The table.
            row: The values to assign, keyed by column name.
            where: The WHERE clause. Any value it compares against must be a `%s`
                placeholder, never text.
            where_params: The parameters that clause's placeholders consume. They follow
                the assigned values in the statement's parameter list.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        with self._operation('insert_row'):
            sorted_column_names = sorted(row.keys())
            set_cmds = []
            param_list: list[Any] = []
            for column_name in sorted_column_names:
                set_cmds.append(f'{self.quote_identifier(column_name)}=%s')
                param_list.append(row[column_name])
            # Identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$) and every
            # row value is a %s placeholder bound through param_list. The caller's
            # `where` fragment, however, is appended verbatim and is not validated:
            # only the values inside it are bound. This method is for trusted callers.
            cmd = (
                f'UPDATE {self.quote_identifier(table_name)} SET '  # nosec B608
                + ','.join(set_cmds)
                + f' WHERE {where}'
            )
            param_list += list(where_params or [])

            try:
                self._execute(cmd, param_list, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed to update row in "{table_name}": {e}')
                raise ImportDBError(e) from e

    def upsert_row(self, table_name: str, key_name: str, row: DBRow) -> None:
        """Insert one row, or update it if its key is already present.

        Parameters:
            table_name: The table.
            key_name: The column identifying the row. It is written on an insert and
                never assigned on an update; a row of nothing but the key produces a
                plain insert.
            row: The values to write, keyed by column name.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        with self._operation('upsert_row'):
            sorted_column_names = sorted(row.keys())
            param_list: list[Any] = []
            placeholders = self._row_placeholders(row, sorted_column_names, param_list)

            assign_list = []
            dup_param_list: list[Any] = []
            for column_name in sorted_column_names:
                if column_name != key_name:
                    assign_list.append(f'{self.quote_identifier(column_name)}=%s')
                    dup_param_list.append(row[column_name])

            # Table and column names are the only interpolations and identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$);
            # every row value is a %s placeholder bound through param_list.
            cmd = (
                f'INSERT INTO {self.quote_identifier(table_name)} '  # nosec B608
                f'({self._quoted_column_list(sorted_column_names)}) '
                f'VALUES({placeholders})'
            )
            if assign_list:
                # A row of nothing but the key has nothing to assign, and an empty
                # assignment list is a syntax error. `upsert_rows` guards the same case.
                # Its update clause needs a row alias and this one does not: a statement
                # here carries a single row, so each new value is already at hand as a
                # bound parameter.
                cmd += ' ON DUPLICATE KEY UPDATE ' + ','.join(assign_list)

            try:
                self._execute(cmd, param_list + dup_param_list, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed to insert row into "{table_name}": {e}')
                raise ImportDBError(e) from e

    def upsert_rows(self, table_name: str, key_name: str, rows: Sequence[DBRow]) -> None:
        """Insert or update multiple rows, a packet of rows per statement.

        Parameters:
            table_name: The table.
            key_name: The column identifying a row. It is written on an insert and never
                assigned on an update; rows of nothing but the key produce a plain
                insert.
            rows: The rows to write. They do not have to share a column set; rows that
                do are batched together, in the order they were given. An empty sequence
                writes nothing.

        Raises:
            ImportDBError: If the server rejects a statement.
        """

        if len(rows) == 0:
            return

        with self._operation('upsert_rows'):
            # Group by column set so that every row in one statement contributes the
            # same VALUES tuple. In practice all the rows of a mult table match.
            groups: dict[tuple[str, ...], list[DBRow]] = {}
            for row in rows:
                groups.setdefault(tuple(sorted(row.keys())), []).append(row)

            packet_size = 1000  # Limit number of rows at a time - MySQL barfs

            for sorted_column_names, group_rows in groups.items():
                quoted_columns = self._quoted_column_list(sorted_column_names)
                # ON DUPLICATE KEY UPDATE has to name each row's new value indirectly,
                # because one statement carries many rows. The row alias MySQL 8.0.19
                # added is how: it names the row being inserted, so `new`.`col` is that
                # row's value for that column. The alternative spelling, VALUES(col), is
                # deprecated as of 8.0.20. The alias is what puts the server floor at
                # 8.0.19, which README.md and the developer guide's prerequisites state.
                # MySQL requires the row alias to differ from the table name, so a
                # table called `new` would produce a syntax error deep inside an import.
                # No OPUS table is called that, but the schema is data rather than a
                # guarantee, so the one colliding name is answered here instead of being
                # assumed away.
                # Compared case-insensitively: MySQL folds identifiers for this check
                # even where the file system makes table names case-sensitive.
                row_alias = self.quote_identifier(
                    'new_row' if table_name.lower() == 'new' else 'new'
                )
                assign_list = ','.join(
                    f'{self.quote_identifier(c)}={row_alias}.{self.quote_identifier(c)}'
                    for c in sorted_column_names
                    if c != key_name
                )

                num_packets = ((len(group_rows) - 1) // packet_size) + 1
                for packet_num in range(num_packets):
                    start_row = packet_size * packet_num
                    end_row = min(len(group_rows), packet_size * (packet_num + 1))

                    value_tuples = []
                    param_list: list[Any] = []
                    for row in group_rows[start_row:end_row]:
                        placeholders = self._row_placeholders(row, sorted_column_names, param_list)
                        value_tuples.append(f'({placeholders})')

                    cmd = (
                        f'INSERT INTO {self.quote_identifier(table_name)} '
                        f'({quoted_columns}) VALUES' + ','.join(value_tuples)
                    )
                    if assign_list:
                        # The alias is emitted only with the clause that reads it. A row
                        # of nothing but the key has nothing to assign, and an alias with
                        # no ON DUPLICATE KEY UPDATE after it would name a row nothing
                        # refers to.
                        cmd += f' AS {row_alias} ON DUPLICATE KEY UPDATE ' + assign_list

                    try:
                        self._execute(cmd, param_list, mutates=True)
                    except MySQLdb.Error as e:
                        if self.logger:
                            self.logger.log(
                                'fatal', f'Failed to insert row into "{table_name}": {e}'
                            )
                        raise ImportDBError(e) from e

    def delete_rows(
        self,
        table_name: str,
        where: str | None = None,
        where_params: Sequence[Any] | None = None,
        *,
        all_rows: bool = False,
    ) -> None:
        """Delete the rows a WHERE clause selects, or every row when asked to.

        A missing WHERE clause is refused rather than read as "every row", so a caller
        whose clause came out empty deletes nothing instead of the whole table.

        Parameters:
            table_name: The table.
            where: The WHERE clause. Any value it compares against must be a `%s`
                placeholder, never text.
            where_params: The parameters that clause's placeholders consume.
            all_rows: True to delete every row; ``where`` must then be None.

        Raises:
            ImportDBError: If there is a WHERE clause and ``all_rows`` is True, or neither,
                or the server rejects the statement.
        """
        if bool(where) == all_rows:
            raise ImportDBError(
                f'delete_rows on "{table_name}" needs a WHERE clause or all_rows=True, and not both'
            )
        with self._operation('delete_rows'):
            # The table name is validated by quote_identifier (^[A-Za-z0-9_]+$). The
            # caller's `where` fragment is appended verbatim below and is not
            # validated; only the values inside it are bound, through where_params.
            # This method is for trusted callers.
            cmd = f'DELETE FROM {self.quote_identifier(table_name)}'  # nosec B608
            if where:
                cmd += f' WHERE {where}'

            try:
                self._execute(cmd, list(where_params) if where_params else None, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed to delete rows from "{table_name}": {e}')
                raise ImportDBError(e) from e

    def delete_joined_rows(
        self,
        table_name: str,
        join_column: str,
        parent_table: str,
        parent_column: str,
        where: str,
        where_params: Sequence[Any],
    ) -> None:
        """Delete the rows of a table that join a parent row a WHERE clause selects.

        Renders ``DELETE c FROM <table> AS c JOIN <parent> AS p ON p.<parent_column> =
        c.<join_column> WHERE <where>``.

        Parameters:
            table_name: The table rows are deleted from.
            join_column: Its column naming a parent row.
            parent_table: The parent table.
            parent_column: The parent's column `join_column` holds.
            where: The WHERE clause selecting parent rows, over the parent's columns
                qualified by `JOINED_PARENT_ALIAS`. Any value it compares against must be
                a `%s` placeholder, never text.
            where_params: The parameters that clause's placeholders consume.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        q = self.quote_identifier
        child, parent = q('c'), q(self.JOINED_PARENT_ALIAS)
        with self._operation('delete_joined_rows'):
            # Every identifier is validated by quote_identifier; the caller's `where`
            # fragment is appended verbatim, and only its values are bound.
            cmd = (
                f'DELETE {child} FROM {q(table_name)} AS {child} '  # nosec B608
                f'JOIN {q(parent_table)} AS {parent} '
                f'ON {parent}.{q(parent_column)} = {child}.{q(join_column)} WHERE {where}'
            )
            try:
                self._execute(cmd, list(where_params), mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal', f'Failed to delete rows from "{table_name}": {e}')
                raise ImportDBError(e) from e

    def general_select(
        self, cmd: str, param_list: Sequence[Any] | None = None
    ) -> Sequence[ResultRow]:
        """Run `SELECT <cmd>` and return every row.

        Parameters:
            cmd: Everything after the SELECT keyword. Identifiers in it must be
                quoted with `quote_identifier`; any value it compares against
                must be a `%s` placeholder, never text.
            param_list: The parameters those placeholders consume.

        Returns:
            One tuple per row, in the order the query named its columns.

        Raises:
            ImportDBError: If the server rejects the query.
        """
        with self._operation('cmd'):
            res = self._execute_and_fetchall('SELECT ' + cmd, 'general_select', param_list)
        return res

    def find_column_max(self, table_name: str, column_name: str) -> Any:
        """Return the largest value in a column.

        Parameters:
            table_name: The table.
            column_name: The column to take the maximum of.

        Returns:
            The maximum, or None if the table has no rows.

        Raises:
            ImportDBError: If the server rejects the query.
        """
        with self._operation('find_column_max'):
            # Column and table names are the only interpolations and identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$).
            # This statement carries no values at all.
            cmd = (
                f'SELECT MAX({self.quote_identifier(column_name)}) '  # nosec B608
                f'FROM {self.quote_identifier(table_name)}'
            )
            res = self._execute_and_fetchall(cmd, 'find_column_max')
        return res[0][0]

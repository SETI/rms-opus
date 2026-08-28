"""The MySQL implementation of the import pipeline's database interface.

`ImportDBMySQL` is the one brand `opus_import.importdb.get_db` can return. It renders the
OPUS table schemas as MySQL DDL and builds the statements that read and write rows.

Every identifier it emits is validated against a strict pattern and then backtick-quoted,
and the row statements bind their values as parameters rather than formatting them into
the text. The DDL is the exception: `ImportDBMySQL.create_table` formats a column's
default and its enum option list straight into the statement, which is safe only because
those come from the table schemas packaged with `opus_import` and never from input.

The driver is imported defensively, so that the module still imports without
``mysqlclient`` installed and a package-wide sweep -- Sphinx autodoc, or a test
collection -- does not fail on it. An instance built without the driver forces itself
read-only and discards every statement rather than running or logging it, so it reports
no tables and reads no rows; it is not a simulation anything can be driven through.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

try:
    import MySQLdb

    MYSQLDB_AVAILABLE = True
except ImportError:
    MYSQLDB_AVAILABLE = False

from opus_import.importdb.super import (
    DBRow,
    ImportDBError,
    ImportDBSuper,
    Namespace,
    ResultRow,
    SchemaColumn,
)

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

    import pdslogger

ERR_UNKNOWN_DATABASE = 1049

# The only identifier shape OPUS uses: table, column and schema names come from
# the checked-in table schemas, from the configuration, and from bundle ids, and
# none of them ever needs a character outside this set. Backticks quote an
# identifier but do not escape a backtick inside one, so validating the name is
# what keeps a computed identifier from ending the quoting early.
_IDENTIFIER_RE = re.compile(r'\A[A-Za-z0-9_]+\Z')


class ImportDBMySQL(ImportDBSuper):
    """The import pipeline's database interface, rendered as MySQL.

    Attributes:
        default_engine: The storage engine every table is created with.
        mysql_version: The server's version string, or ``'Simulated'`` when the driver is
            absent.
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
        import_prefix: str | None = None,
        logger: pdslogger.PdsLogger | None = None,
        read_only: bool = False,
    ) -> None:
        """Open the connection to a MySQL server, creating the schema if it is absent.

        The parameters are `ImportDBSuper`'s, and ``db_name`` is ignored: MySQL has no
        level above the schema.

        Parameters:
            db_hostname: The MySQL server's host name.
            db_name: Unused.
            db_schema: The schema (MySQL database) holding the OPUS tables. It is
                created if the server does not already have it.
            db_user: The user to connect as.
            db_password: That user's password.
            mult_form_types: The ``param_info`` form types that have a ``mult_`` table,
                or None for none of them.
            import_prefix: The prefix distinguishing an import table from its permanent
                counterpart, or None to make the two namespaces the same tables.
            logger: Where to report progress, statements and warnings, or None to report
                nothing.
            read_only: True to log every mutating statement instead of executing it.

        Raises:
            ImportDBError: If the server cannot be reached, the schema can be neither
                used nor created, or the session's SQL mode cannot be set.
        """
        super().__init__(
            db_hostname,
            db_name,
            db_schema,
            db_user,
            db_password,
            mult_form_types=mult_form_types,
            import_prefix=import_prefix,
            logger=logger,
            read_only=read_only,
        )
        super()._enter('__init__')

        self._table_info_cache: dict[tuple[Namespace, str], list[SchemaColumn]] = {}

        if not MYSQLDB_AVAILABLE:
            self.read_only = True
            if self.logger:
                self.logger.log(
                    'warning',
                    'Python package MySQLdb not available - simulating all ' + 'database accesses!',
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
                    host=self.db_hostname, user=self.db_user, passwd=self.db_password
                )
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log(
                        'fatal',
                        'Unable to connect to MySQL server ' + f'"{self.db_hostname}": {e.args[1]}',
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
                err_code = e.args[0]
                if err_code == ERR_UNKNOWN_DATABASE:
                    try:
                        cmd = f'CREATE DATABASE {self.quote_identifier(self.db_schema)}'
                        self._execute(cmd)
                    except MySQLdb.Error as create_err:
                        if self.logger:
                            self.logger.log(
                                'fatal',
                                f'Unable to create new database "{self.db_schema}"'
                                + f': {create_err.args[1]}',
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
                                + f'"{self.db_schema}": {use_err.args[1]}',
                            )
                        raise ImportDBError(use_err) from use_err
                else:
                    if self.logger:
                        self.logger.log(
                            'fatal',
                            'Unable to use existing database ' + f'"{self.db_schema}": {e.args[1]}',
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
                    self.logger.log('fatal', f'Failed to set STRICT_ALL_TABLES mode: {e.args[1]}')
                raise ImportDBError(e) from e

        super()._exit()

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
                self.logger.log('fatal', f'Failed in {func_name}: {e.args[1]}')
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
        self, namespace: Namespace, prefix: str | list[str] | tuple[str, ...] | None = None
    ) -> Collection[str]:
        """Return the names of the tables in a namespace.

        The names are read from the server once and cached, so a run that creates and
        drops tables through this instance never re-queries for them.

        Parameters:
            namespace: The namespace to list. ``'import'`` and ``'perm'`` return raw
                names, with the import prefix stripped; ``'all'`` returns the names as
                the server spells them.
            prefix: One prefix, or several, that a name must start with; None for every
                name.

        Returns:
            The matching table names, in no particular order. Passing a prefix always
            gives a new list; asking for ``'all'`` without one gives the cache itself,
            which the caller must not modify.

        Raises:
            NotImplementedError: If the namespace is not one of the three.
        """
        super()._enter('table_names')

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
        super()._exit()

        ret_names: Collection[str]
        if namespace == 'all':
            ret_names = self._table_names
        elif namespace == 'import':
            ret_names = [
                self.convert_namespace_to_raw(namespace, x)
                for x in self._table_names
                if self._is_import_namespace(x)
            ]
        elif namespace == 'perm':
            ret_names = [
                self.convert_namespace_to_raw(namespace, x)
                for x in self._table_names
                if self._is_perm_namespace(x)
            ]
        else:
            raise NotImplementedError(namespace)

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

    def table_info(self, namespace: Namespace, raw_table_name: str) -> list[SchemaColumn]:
        """Return the columns of a table as the server currently defines them.

        The answer is cached per table and discarded whenever a table is created or
        dropped through this instance.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.

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
        cache_key = (namespace, raw_table_name)
        if cache_key in self._table_info_cache:
            return self._table_info_cache[cache_key]
        super()._enter('table_info')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

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

        super()._exit()
        self._table_info_cache[cache_key] = column_list
        return column_list

    def drop_table(
        self, namespace: Namespace, raw_table_name: str, ignore_if_not_exists: bool = True
    ) -> None:
        """Delete the given table if it exists.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            ignore_if_not_exists: True to do nothing when the table is absent.

        Raises:
            ImportDBError: If the table is absent and ``ignore_if_not_exists`` is False,
                or the server rejects the statement.
        """
        super()._enter('drop_table')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        # table_exists caches the table names, which we need below for read_only
        if not self.table_exists(namespace, raw_table_name):
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
                    self.logger.log('fatal', f'Failed in drop_table on "{table_name}": {e.args[1]}')
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

        super()._exit()

    def create_table(
        self,
        namespace: Namespace,
        raw_table_name: str,
        schema: Sequence[SchemaColumn],
        ignore_if_exists: bool = True,
    ) -> bool:
        """Create a new table from the given OPUS table schema.

        Parameters:
            namespace: The namespace to create the table in.
            raw_table_name: The table, without its namespace prefix.
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
        super()._enter('create_table')

        if ignore_if_exists and self.table_exists(namespace, raw_table_name):
            super()._exit()
            return False

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        cmd = ''
        key_cmd = ''

        for column in schema:
            if 'pi_referred_slug' in column:
                continue

            if cmd != '':
                cmd += ',\n'

            if 'constraint' in column:
                cmd += '  ' + column['constraint'] + '\n'
                continue

            field_name = column['field_name']
            field_type = column['field_type']

            cmd += f'  {self.quote_identifier(field_name)} '
            if field_type == 'int1':
                cmd += 'tinyint'
            elif field_type == 'int2':
                cmd += 'smallint'
            elif field_type == 'int3':
                cmd += 'mediumint'
            elif field_type == 'int4':
                cmd += 'int'
            elif field_type == 'int8':
                cmd += 'bigint'

            elif field_type == 'uint1':
                cmd += 'tinyint unsigned'
            elif field_type == 'uint2':
                cmd += 'smallint unsigned'
            elif field_type == 'uint3':
                cmd += 'mediumint unsigned'
            elif field_type == 'uint4':
                cmd += 'int unsigned'
            elif field_type == 'uint8':
                cmd += 'bigint unsigned'

            elif field_type == 'real4':
                cmd += 'float'
            elif field_type == 'real8':
                cmd += 'double'

            elif field_type[:4] == 'char':
                cmd += 'char(' + field_type[4:] + ')'
            elif field_type[:7] == 'varchar':
                cmd += 'varchar(' + field_type[7:] + ')'
            elif field_type == 'text':
                cmd += 'text'
            elif field_type in ('mult_list', 'json'):
                cmd += 'JSON'
            elif field_type == 'enum':
                enum_str = column.get('field_enum_options', None)
                assert enum_str, (raw_table_name, column)
                cmd += f'enum({enum_str})'
            elif (
                field_type == 'flag_yesno' or field_type == 'flag_onoff' or field_type == 'mult_idx'
            ):
                cmd += 'int unsigned'  # Index for mult table
            elif field_type == 'timestamp':
                cmd += 'timestamp'
            elif field_type == 'datetime':
                cmd += 'datetime'
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

            key_type = column.get('field_key', False)
            foreign_key = column.get('field_key_foreign', False)
            assert not foreign_key or key_type == 'foreign'
            if key_type:
                if key_cmd != '':
                    key_cmd += ',\n'
                if key_type == 'unique':
                    quoted_field = self.quote_identifier(field_name)
                    key_cmd += f'  UNIQUE KEY {quoted_field} ({quoted_field})'
                elif key_type == 'primary':
                    key_cmd += f'  PRIMARY KEY ({self.quote_identifier(field_name)})'
                elif key_type == 'foreign':
                    assert foreign_key
                    key_cmd += f'  FOREIGN KEY ({self.quote_identifier(field_name)})'
                    key_cmd += ' REFERENCES '
                    f_table = self.convert_raw_to_namespace(namespace, foreign_key[0])
                    key_cmd += self.quote_identifier(f_table)
                    key_cmd += f'({self.quote_identifier(foreign_key[1])})'
                    key_cmd += ' ON DELETE RESTRICT ON UPDATE CASCADE'
                else:
                    quoted_field = self.quote_identifier(field_name)
                    key_cmd += f'  KEY {quoted_field} ({quoted_field})'

        if key_cmd != '':
            cmd += ',\n' + key_cmd
        cmd = f'CREATE TABLE {self.quote_identifier(table_name)} (\n' + cmd + '\n)'
        cmd += f' ENGINE={self.default_engine}\n'

        try:
            self._execute(cmd, mutates=True)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal', f'Failed to create table "{table_name}": {e.args[1]}')
            raise ImportDBError(e) from e

        if self.logger:
            if self.read_only:
                self.logger.log('debug', f'[SIM] Created table "{table_name}"')
            else:
                self.logger.log('debug', f'Created table "{table_name}"')
                # Don't pretend the table has been created if it really hasn't
                # because we might try to read from it later expecting it to
                # really be there!
                assert self._table_names is not None
                self._table_names.add(table_name)

        self.tables_created.append(table_name)
        self._table_info_cache.clear()

        super()._exit()
        return True

    def analyze_table(self, namespace: Namespace, raw_table_name: str) -> None:
        """Analyze the given table. This recomputes key distribution.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        super()._enter('analyze_table')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        cmd = f'ANALYZE TABLE {self.quote_identifier(table_name)}'

        try:
            self._execute(cmd, mutates=True)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal', f'Failed to analyze table "{table_name}": {e.args[1]}')
            raise ImportDBError(e) from e

        if self.logger:
            if self.read_only:
                self.logger.log('debug', f'[SIM] Analyzed table "{table_name}"')
            else:
                self.logger.log('debug', f'Analyzed table "{table_name}"')

        super()._exit()

    def insert_row(self, namespace: Namespace, raw_table_name: str, row: DBRow) -> None:
        """Insert one row.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            row: The values to write, keyed by column name.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        super()._enter('insert_row')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

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
                self.logger.log('fatal', f'Failed to insert row into "{table_name}": {e.args[1]}')
            raise ImportDBError(e) from e

        super()._exit()

    def insert_rows(self, namespace: Namespace, raw_table_name: str, rows: Sequence[DBRow]) -> None:
        """Insert multiple rows, a thousand at a time.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            rows: The rows to write. All rows must have the same columns; an empty
                sequence writes nothing.

        Raises:
            ImportDBError: If the server rejects a statement.
        """

        if len(rows) == 0:
            return

        super()._enter('insert_rows')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

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
                f'({self._quoted_column_list(sorted_column_names)}) VALUES' + ','.join(value_tuples)
            )

            try:
                self._execute(cmd, param_list, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log(
                        'fatal', f'Failed to insert row into "{table_name}": {e.args[1]}'
                    )
                raise ImportDBError(e) from e

        super()._exit()

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
            where_params: The parameters that clause's placeholders consume. They follow
                the assigned values in the statement's parameter list.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        super()._enter('insert_row')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

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
                self.logger.log('fatal', f'Failed to update row in "{table_name}": {e.args[1]}')
            raise ImportDBError(e) from e

        super()._exit()

    def upsert_row(
        self, namespace: Namespace, raw_table_name: str, key_name: str, row: DBRow
    ) -> None:
        """Insert one row, or update it if its key is already present.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            key_name: The column identifying the row. It is written on an insert and
                never assigned on an update; a row of nothing but the key produces a
                plain insert.
            row: The values to write, keyed by column name.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        super()._enter('upsert_row')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

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
                self.logger.log('fatal', f'Failed to insert row into "{table_name}": {e.args[1]}')
            raise ImportDBError(e) from e

        super()._exit()

    def upsert_rows(
        self, namespace: Namespace, raw_table_name: str, key_name: str, rows: Sequence[DBRow]
    ) -> None:
        """Insert or update multiple rows, a packet of rows per statement.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
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

        super()._enter('upsert_rows')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

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
            # MySQL requires the row alias to differ from the table name, and a
            # `perm`-namespace name is the raw one, so a table called `new` would
            # produce a syntax error deep inside an import. No OPUS table is called
            # that, but the schema is data rather than a guarantee, so the one
            # colliding name is answered here instead of being assumed away.
            # Compared case-insensitively: MySQL folds identifiers for this check
            # even where the file system makes table names case-sensitive.
            row_alias = self.quote_identifier('new_row' if table_name.lower() == 'new' else 'new')
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
                            'fatal', f'Failed to insert row into "{table_name}": {e.args[1]}'
                        )
                    raise ImportDBError(e) from e

        super()._exit()

    def delete_rows(
        self,
        namespace: Namespace,
        raw_table_name: str,
        where: str | None = None,
        where_params: Sequence[Any] | None = None,
    ) -> None:
        """Delete the rows a WHERE clause selects.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            where: The WHERE clause, or None to delete every row. Any value it compares
                against must be a `%s` placeholder, never text.
            where_params: The parameters that clause's placeholders consume.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        super()._enter('delete_rows')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

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
                self.logger.log('fatal', f'Failed to delete rows from "{table_name}": {e.args[1]}')
            raise ImportDBError(e) from e

        self._exit()

    def copy_rows_between_namespaces(
        self,
        src_namespace: Namespace,
        dest_namespace: Namespace,
        raw_table_name: str,
        where: str | None = None,
        where_params: Sequence[Any] | None = None,
    ) -> None:
        """Copy rows of one table from one namespace to the same table in another.

        Both tables must have the same columns in the same order, which they do because
        both are created from the same OPUS table schema.

        Parameters:
            src_namespace: The namespace to read from.
            dest_namespace: The namespace to write to.
            raw_table_name: The table, without its namespace prefix.
            where: The WHERE clause selecting the rows to copy, or None for every row.
                Any value it compares against must be a `%s` placeholder, never text.
            where_params: The parameters that clause's placeholders consume.

        Raises:
            ImportDBError: If the server rejects the statement.
        """
        super()._enter('copy_rows')

        src_table_name = self.convert_raw_to_namespace(src_namespace, raw_table_name)
        dest_table_name = self.convert_raw_to_namespace(dest_namespace, raw_table_name)

        # Both table names are validated by quote_identifier (^[A-Za-z0-9_]+$).
        # The caller's `where` fragment is appended verbatim below and is not
        # validated; only the values inside it are bound, through where_params.
        # This method is for trusted callers.
        cmd = (
            f'INSERT INTO {self.quote_identifier(dest_table_name)} SELECT * '  # nosec B608
            f'FROM {self.quote_identifier(src_table_name)}'
        )
        if where:
            cmd += f' WHERE {where}'

        try:
            self._execute(cmd, list(where_params) if where_params else None, mutates=True)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log(
                    'fatal',
                    f'Failed to copy rows from "{src_table_name}" to '
                    f'"{dest_table_name}": {e.args[1]}',
                )
            raise ImportDBError(e) from e

        self._exit()

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
        super()._enter('cmd')

        res = self._execute_and_fetchall('SELECT ' + cmd, 'general_select', param_list)
        self._exit()
        return res

    def find_column_max(self, namespace: Namespace, raw_table_name: str, column_name: str) -> Any:
        """Return the largest value in a column.

        Parameters:
            namespace: The namespace holding the table.
            raw_table_name: The table, without its namespace prefix.
            column_name: The column to take the maximum of.

        Returns:
            The maximum, or None if the table has no rows.

        Raises:
            ImportDBError: If the server rejects the query.
        """
        super()._enter('find_column_max')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        # Column and table names are the only interpolations and identifiers are validated by quote_identifier (^[A-Za-z0-9_]+$).
        # This statement carries no values at all.
        cmd = (
            f'SELECT MAX({self.quote_identifier(column_name)}) '  # nosec B608
            f'FROM {self.quote_identifier(table_name)}'
        )
        res = self._execute_and_fetchall(cmd, 'find_column_max')
        self._exit()
        return res[0][0]

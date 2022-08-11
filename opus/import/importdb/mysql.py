from functools import lru_cache

try:
    import MySQLdb
    MYSQLDB_AVAILABLE = True
except ImportError:
    MYSQLDB_AVAILABLE = False

from importdb.super import ImportDBSuper, ImportDBException

ERR_UNKNOWN_DATABASE = 1049

class ImportDBMySQL(ImportDBSuper):
    # Note that for MySQL, we ignore the db_name and only use the schema_name
    def __init__(self, *args, **kwargs):
        """Open the connection to a MySQL server. Note this will also
           create the database if it doesn't already exist."""
        super(ImportDBMySQL, self).__init__(*args, **kwargs)
        super(ImportDBMySQL, self)._enter('__init__')

        if not MYSQLDB_AVAILABLE:
            self.read_only = True
            self.logger.log('warning',
                'Python package MySQLdb not available - simulating all '+
                'database accesses!')

        self.default_engine = 'INNODB'
        if 'engine' in kwargs:
            self.default_engine = kwargs['engine']

        if not MYSQLDB_AVAILABLE:
            self.conn = None
            if self.logger:
                self.logger.log('info',
                        f'[SIM] Connected to MySQL server "{self.db_hostname}" '
                       +f'as "{self.db_user}"')
        else:
            try:
                self.conn = MySQLdb.connect(host=self.db_hostname,
                                            user=self.db_user,
                                            passwd=self.db_password)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal',
                            'Unable to connect to MySQL server '
                           +f'"{self.db_hostname}": {e.args[1]}')
                raise ImportDBException(e)

            if self.logger:
                self.logger.log('info',
                        f'Connected to MySQL server "{self.db_hostname}" '
                       +f'as "{self.db_user}"')

            try:
                cmd = f'USE `{self.db_schema}`'
                self._execute(cmd)
            except MySQLdb.Error as e:
                err_code = e.args[0]
                if err_code == ERR_UNKNOWN_DATABASE:
                    try:
                        cmd = f'CREATE DATABASE `{self.db_schema}`'
                        self._execute(cmd)
                    except MySQLdb.Error as e:
                        if self.logger:
                            self.logger.log('fatal',
                            f'Unable to create new database "{self.db_schema}"'+
                            f': {e.args[1]}')
                        raise ImportDBException(e)
                    if self.logger:
                        self.logger.log('warning',
                                f'  Created new database "{self.db_schema}"')

                    try:
                        cmd = f'USE `{self.db_schema}`'
                        self._execute(cmd)
                    except MySQLdb.Error as e:
                        if self.logger:
                            self.logger.log('fatal',
                                'Unable to use new database '+
                                f'"{self.db_schema}": {e.args[1]}')
                        raise ImportDBException(e)
                else:
                    if self.logger:
                        self.logger.log('fatal',
                            'Unable to use existing database '+
                            f'"{self.db_schema}": {e.args[1]}')
                    raise ImportDBException(e)

        if self.logger:
            self.logger.log('info',
                            f'  Using database "{self.db_schema}"')

        # We keep a cached list of table names so we don't have to keep doing
        # SQL queries - go ahead and populate it now
        self._table_names = None
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
            self.logger.log('info', f'  MySQL version: {self.mysql_version}')

            try:
                cmd = "set sql_mode = 'NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION,STRICT_ALL_TABLES"
                if self.mysql_version[0] == '5':
                    cmd += ',NO_AUTO_CREATE_USER'
                cmd += "'"
                self._execute(cmd)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal',
                        f'Failed to set STRICT_ALL_TABLES mode: {e.args[1]}')
                raise ImportDBException(e)

        super(ImportDBMySQL, self)._exit()

    def _execute(self, *args, **kwargs):
        if not MYSQLDB_AVAILABLE:
            return
        super(ImportDBMySQL, self)._execute(*args, **kwargs)

    def _execute_and_fetchall(self, cmd, func_name):
        if not MYSQLDB_AVAILABLE:
            return []

        try:
            with self.conn.cursor() as cur:
                self._execute(cmd, cur=cur)
                self.conn.commit()
                return cur.fetchall()
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                    f'Failed in {func_name}: {e.args[1]}')
            raise ImportDBException(e)

    def quote_identifier(self, s):
        return '`' + s + '`'

    def table_names(self, namespace, prefix=None):
        "Return a list of all table names in the schema."
        super(ImportDBMySQL, self)._enter('table_names')

        if self._table_names is None:
            cmd = f"""
SELECT `TABLE_NAME` FROM `INFORMATION_SCHEMA`.`TABLES` WHERE
`TABLE_TYPE`='BASE TABLE' AND `TABLE_SCHEMA`='{self.db_schema}'"""
            res = self._execute_and_fetchall(cmd, 'table_names')
            # Note: SQL table names are case-insensitive on SOME OSes and this
            # query returns them in whatever case SQL returns them in.
            # But table_exists does a case-insensitive match.
            self._table_names = set(x[0] for x in res)
            # if self.logger:
            #     self.logger.log('debug',
            #             f'  Current table names: {sorted(self._table_names)}')
        super(ImportDBMySQL, self)._exit()

        if namespace == 'all':
            ret_names = self._table_names
        elif namespace == 'import':
            ret_names = [self.convert_namespace_to_raw(namespace, x)
                            for x in self._table_names if
                                self._is_import_namespace(x)]
        elif namespace == 'perm':
            ret_names = [self.convert_namespace_to_raw(namespace, x)
                            for x in self._table_names if
                                self._is_perm_namespace(x)]
        else:
            assert False

        if prefix is None:
            return ret_names

        if isinstance(prefix, list) or isinstance(prefix, tuple):
            ret_list = []
            for name in ret_names:
                for p in prefix:
                    if name.startswith(p):
                        ret_list.append(name)
                        break
            return ret_list

        return [x for x in ret_names if x.startswith(prefix)]

    @lru_cache(maxsize=None)
    def table_info(self, namespace, raw_table_name):
        "Return a list containing information about the table columns."
        super(ImportDBMySQL, self)._enter('table_info')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        cmd = f"""
SELECT `COLUMN_NAME`, `COLUMN_DEFAULT`, `IS_NULLABLE`, `DATA_TYPE`, `CHARACTER_MAXIMUM_LENGTH`, `COLUMN_TYPE`
FROM `INFORMATION_SCHEMA`.`COLUMNS` WHERE `TABLE_SCHEMA`='{self.db_schema}' AND
`TABLE_NAME`='{table_name}' ORDER BY `ORDINAL_POSITION`"""
        rows = self._execute_and_fetchall(cmd, 'table_info')

        column_list = []

        for row in rows:
            (column_name, column_default, is_nullable,
             data_type, char_len, column_type) = row
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
            elif data_type == 'multisel':
                field_type = 'multisel'
            else:
                assert False, data_type
            if (field_type.startswith('int') and
                column_type.find('unsigned') != -1):
                field_type = 'u' + field_type

            column_dict = {
                'field_name': column_name,
                'field_default': column_default,
                'field_notnull': is_nullable == 'NO',
                'field_type': field_type
            }
            column_list.append(column_dict)

        super(ImportDBMySQL, self)._exit()
        return column_list

    def drop_table(self, namespace, raw_table_name, ignore_if_not_exists=True):
        "Delete the given table if it exists."
        super(ImportDBMySQL, self)._enter('drop_table')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        # table_exists caches the table names, which we need below for read_only
        if not self.table_exists(namespace, raw_table_name):
            if ignore_if_not_exists:
                if self.logger:
                    self.logger.log('debug',
                        f'drop_table "{table_name}" - no table found')
            else:
                if self.logger:
                    self.logger.log('fatal',
            f'Attempted to drop table "{table_name}" that doesn\'t exist')
                raise ImportDBException()
        else:
            try:
                cmd = f'DROP TABLE `{table_name}`'
                self._execute(cmd, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal',
                        f'Failed in drop_table on "{table_name}": {e.args[1]}')
                raise ImportDBException(e)

            if self.logger:
                if self.read_only:
                    self.logger.log('debug',
                            f'[SIM] Dropped table "{table_name}"')
                else:
                    self.logger.log('debug',
                            f'Dropped table "{table_name}"')

            if table_name in self._table_names:
                self._table_names.remove(table_name)
            else:
                assert table_name.lower() in self._table_names, table_name
                self._table_names.remove(table_name.lower())

        self.table_info.cache_clear()

        super(ImportDBMySQL, self)._exit()

    def create_table(self, namespace, raw_table_name, schema,
                     ignore_if_exists=True):
        """Create a new table from the given schema. Returns True if
           table successfully created; False if table already existed
           and ignore_if_exists==True."""
        super(ImportDBMySQL, self)._enter('create_table')

        if ignore_if_exists and self.table_exists(namespace, raw_table_name):
            super(ImportDBMySQL, self)._exit()
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
                cmd += '  '+column['constraint']+'\n'
                continue

            field_name = column['field_name']
            field_type = column['field_type']

            cmd += f'  `{field_name}` '
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
                cmd += 'char('+field_type[4:]+')'
            elif field_type[:7] == 'varchar':
                cmd += 'varchar('+field_type[7:]+')'
            elif field_type == 'text':
                cmd += 'text'
            elif field_type in ('multisel', 'json'):
                cmd += 'JSON'
            elif field_type == 'enum':
                enum_str = column.get('field_enum_options', None)
                assert enum_str, (raw_table_name, column)
                cmd += f'enum({enum_str})'
            elif field_type == 'flag_yesno':
                cmd += 'int unsigned' # Index for mult table
            elif field_type == 'flag_onoff':
                cmd += 'int unsigned' # Index for mult table
            elif field_type == 'mult_idx':
                cmd += 'int unsigned' # Index for mult table
            elif field_type == 'timestamp':
                cmd += 'timestamp'
            elif field_type == 'datetime':
                cmd += 'datetime'
            else:
                assert False, field_type

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
                if (field_default != 'NULL' and
                    field_default != 'CURRENT_TIMESTAMP'
                    and not field_default.isdigit()):
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
                    key_cmd += f'  UNIQUE KEY `{field_name}` (`{field_name}`)'
                elif key_type == 'primary':
                    key_cmd += f'  PRIMARY KEY (`{field_name}`)'
                elif key_type == 'foreign':
                    assert foreign_key
                    key_cmd += f'  FOREIGN KEY (`{field_name}`)'
                    key_cmd += ' REFERENCES '
                    f_table = self.convert_raw_to_namespace(namespace,
                                                            foreign_key[0])
                    key_cmd += f'`{f_table}`'
                    key_cmd += f'(`{foreign_key[1]}`)'
                    key_cmd += ' ON DELETE RESTRICT ON UPDATE CASCADE'
                else:
                    key_cmd += f'  KEY `{field_name}` (`{field_name}`)'

        if key_cmd != '':
            cmd += ',\n' + key_cmd
        cmd = f'CREATE TABLE `{table_name}` (\n' + cmd + '\n)'
        cmd += f' ENGINE={self.default_engine}\n'

        try:
            self._execute(cmd, mutates=True)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                        f'Failed to create table "{table_name}": {e.args[1]}')
            raise ImportDBException(e)

        if self.logger:
            if self.read_only:
                self.logger.log('debug', f'[SIM] Created table "{table_name}"')
            else:
                self.logger.log('debug', f'Created table "{table_name}"')
                # Don't pretend the table has been created if it really hasn't
                # because we might try to read from it later expecting it to
                # really be there!
                self._table_names.add(table_name)

        self.tables_created.append(table_name)
        self.table_info.cache_clear()

        super(ImportDBMySQL, self)._exit()
        return True

    def analyze_table(self, namespace, raw_table_name):
        """Analyze the given table. This recomputes key distribution."""
        super(ImportDBMySQL, self)._enter('analyze_table')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        cmd = f'ANALYZE TABLE `{table_name}`'

        try:
            self._execute(cmd, mutates=True)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                        f'Failed to analyze table "{table_name}": {e.args[1]}')
            raise ImportDBException(e)

        if self.logger:
            if self.read_only:
                self.logger.log('debug', f'[SIM] Analyzed table "{table_name}"')
            else:
                self.logger.log('debug', f'Analyzed table "{table_name}"')

        super(ImportDBMySQL, self)._exit()

    def insert_row(self, namespace, raw_table_name, row):
        super(ImportDBMySQL, self)._enter('insert_row')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        sorted_column_names = sorted(row.keys())
        cmd = f'INSERT INTO `{table_name}` ('
        cmd += ','.join(['`'+s+'`' for s in sorted(sorted_column_names)])

        val_list = []
        param_list = []
        for column_name in sorted_column_names:
            val = row[column_name]
            if val is None:
                val_list.append('NULL')
            elif isinstance(val, str):
                param_list.append(val)
                val_list.append('%s')
            else:
                val_list.append(str(val))
        cmd += ') VALUES(' + ','.join(val_list) + ')'

        try:
            self._execute(cmd, param_list, mutates=True)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                        f'Failed to insert row into "{table_name}": {e.args[1]}')
            raise ImportDBException(e)

        super(ImportDBMySQL, self)._exit()

    def insert_rows(self, namespace, raw_table_name, rows):
        """Insert multiple rows as one transation.

        All rows must have the same columns!"""

        if len(rows) == 0:
            return

        super(ImportDBMySQL, self)._enter('insert_rows')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        packet_size = 1000 # Limit number of rows at a time - MySQL barfs

        num_packets = ((len(rows)-1) // packet_size) + 1

        for packet_num in range(num_packets):
            start_row = packet_size * packet_num
            end_row = min(len(rows),
                          packet_size * (packet_num+1))

            sorted_column_names = sorted(rows[0].keys())
            cmd = f'INSERT INTO `{table_name}` ('
            cmd += ','.join(['`'+s+'`' for s in sorted(sorted_column_names)])

            cmd += ') VALUES'

            first_row = True
            param_list = []
            for row in rows[start_row:end_row]:
                val_list = []
                assert sorted_column_names == sorted(row.keys()), \
                        (sorted_column_names, sorted(row.keys()))
                for column_name in sorted_column_names:
                    val = row[column_name]
                    if val is None:
                        val_list.append('NULL')
                    elif isinstance(val, str):
                        val_list.append('%s')
                        param_list.append(val)
                    else:
                        val_list.append(str(val))
                if not first_row:
                    cmd += ','
                first_row = False
                cmd += '(' + ','.join(val_list) + ')'

            try:
                self._execute(cmd, param_list, mutates=True)
            except MySQLdb.Error as e:
                if self.logger:
                    self.logger.log('fatal',
                    f'Failed to insert row into "{table_name}": {e.args[1]}')
                raise ImportDBException(e)

        super(ImportDBMySQL, self)._exit()

    def update_row(self, namespace, raw_table_name, row, where):
        super(ImportDBMySQL, self)._enter('insert_row')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        sorted_column_names = sorted(row.keys())
        cmd = f'UPDATE `{table_name}` SET '

        set_cmds = []
        param_list = []
        for column_name in sorted_column_names:
            set_cmd = f'`{column_name}`='
            val = row[column_name]
            if val is None:
                set_cmd += 'NULL'
            elif isinstance(val, str):
                set_cmd += '%s'
                param_list.append(val)
            else:
                set_cmd += str(val)
            set_cmds.append(set_cmd)
        cmd += ','.join(set_cmds)
        cmd += ' WHERE '+where

        try:
            self._execute(cmd, param_list, mutates=True)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                        f'Failed to update row in "{table_name}": {e.args[1]}')
            raise ImportDBException(e)

        super(ImportDBMySQL, self)._exit()

    def upsert_row(self, namespace, raw_table_name, key_name, row):
        super(ImportDBMySQL, self)._enter('upsert_row')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        sorted_column_names = sorted(row.keys())
        cmd = f'INSERT INTO `{table_name}` ('
        cmd += ','.join(['`'+s+'`' for s in sorted(sorted_column_names)])

        val_list = []
        assign_list = []
        param_list = []
        dup_param_list = []
        for column_name in sorted_column_names:
            val = row[column_name]
            if val is None:
                val_list.append('NULL')
                if column_name != key_name:
                    assign_list.append('`'+column_name+'`=NULL')
            elif isinstance(val, str):
                val_list.append('%s')
                param_list.append(val)
                if column_name != key_name:
                    assign_list.append('`'+column_name+'`=%s')
                    dup_param_list.append(val)
            else:
                val_list.append(str(val))
                if column_name != key_name:
                    assign_list.append('`'+column_name + '`=' + str(val))
        cmd += ') VALUES(' + ','.join(val_list) + ') '
        cmd += 'ON DUPLICATE KEY UPDATE ' + ','.join(assign_list)

        try:
            self._execute(cmd, param_list+dup_param_list, mutates=True)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                        f'Failed to insert row into "{table_name}": {e.args[1]}')
            raise ImportDBException(e)

        super(ImportDBMySQL, self)._exit()

    def upsert_rows(self, namespace, table_name, key_name, rows):
        super(ImportDBMySQL, self)._enter('upsert_rows')

        for row in rows:
            self.upsert_row(namespace, table_name, key_name, row)

        super(ImportDBMySQL, self)._exit()

    def delete_rows(self, namespace, raw_table_name, where=None):
        super(ImportDBMySQL, self)._enter('delete_rows')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        cmd = f"DELETE FROM `{table_name}`"
        if where:
            cmd += f" WHERE {where}"
        self._execute(cmd, mutates=True)
        self._exit()

    def copy_rows_between_namespaces(self, src_namespace, dest_namespace,
                                     raw_table_name, where=None):
        super(ImportDBMySQL, self)._enter('copy_rows')

        src_table_name = self.convert_raw_to_namespace(src_namespace,
                                                       raw_table_name)
        dest_table_name = self.convert_raw_to_namespace(dest_namespace,
                                                        raw_table_name)

        cmd = f"INSERT INTO `{dest_table_name}` SELECT * "
        cmd += f"FROM `{src_table_name}`"
        if where:
            cmd += f" WHERE {where}"
        self._execute(cmd, mutates=True)
        self._exit()

    def general_select(self, cmd):
        super(ImportDBMySQL, self)._enter('cmd')

        res = self._execute_and_fetchall('SELECT '+cmd, 'general_select')
        self._exit()
        return res

    def find_column_max(self, namespace, raw_table_name, column_name):
        super(ImportDBMySQL, self)._enter('find_column_max')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        cmd = f"SELECT MAX(`{column_name}`) FROM `{table_name}`"
        res = self._execute_and_fetchall(cmd, 'find_column_max')
        self._exit()
        return res[0][0]

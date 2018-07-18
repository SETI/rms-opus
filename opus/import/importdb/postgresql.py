import csv
import psycopg2 as pg

from importdb.super import ImportDBSuper

class ImportDBPostgreSQL(ImportDBSuper):
    def __init__(self, *args, **kwargs):
        super(ImportDBMySQL, self).__init__(*args, **kwargs)

        try:
            self.conn = MySQLdb.connect(user=self.db_user,
                                        passwd=self.db_password,
                                        db=self.db_name)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                                f'Unable to connect to MySQL server: {e}')
            raise

        if self.logger:
            self.logger.log('info',
            f'Connected to MySQL server DB "{self.db_name}" as "{self.db_user}"')

    def table_exists(self, table_name):
        "Checks to see if the given table exists and returns True or False."
        try:
            cur = self.conn.cursor()
            cmd = f"""
SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE
TABLE_TYPE='BASE TABLE' AND TABLE_SCHEMA='{self.db_name}' AND
TABLE_NAME='{table_name}'"""
            if self.log_sql and self.logger:
                self.logger.log('debug', cmd)
            cur.execute(cmd)
            res = cur.fetchone()[0]
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                                f'Failed in tables_exists on "{table_name}": {e}')
            raise

        return res

    def create_table(self, table_name, schema_filename):
        with open(schema_filename, 'r') as f:
            reader = csv.reader(f)
            key_cmd = ''
            cmd = ''
            for entry in reader:
                (field_name, type_name, size, enum_str, null_ok,
                 key_type, default_value, extras) = entry
                if size == '':
                    size = None
                else:
                    size = int(size)
                enum_str = enum_str.replace(';',',')

                if cmd != '':
                    cmd += ',\n'

                cmd += f'  `{field_name}` '
                if type_name == 'int':
                    if size <= 2:
                        cmd += 'tinyint'
                    elif size <= 4:
                        cmd += 'smallint'
                    elif size <= 6:
                        cmd += 'mediumint'
                    elif size <= 9:
                        cmd += 'int'
                    else:
                        cmd += 'bigint'
                    cmd += f'({size})'
                elif type_name == 'unsigned int':
                    if size <= 2:
                        cmd += 'tinyint'
                    elif size <= 4:
                        cmd += 'smallint'
                    elif size <= 7:
                        cmd += 'mediumint'
                    elif size <= 9:
                        cmd += 'int'
                    else:
                        cmd += 'bigint'
                    cmd += f'({size})'
                elif type_name == 'real':
                    if size == 4:
                        cmd += 'float'
                    elif size == 8:
                        cmd += 'double'
                    else:
                        assert False
                elif type_name == 'char':
                    cmd += 'char'
                    if size is not None:
                        cmd += f'({size})'
                elif type_name == 'enum':
                    cmd += f'enum({enum_str})'
                elif type_name == 'timestamp':
                    cmd += 'timestamp'
                else:
                    assert False

                if null_ok == 'NO':
                    cmd += ' NOT NULL'
                    if default_value == 'NULL':
                        default_value = ''

                if default_value != '':
                    if (default_value != 'NULL' and
                        default_value != 'CURRENT_TIMESTAMP'):
                        default_value = "'" + default_value + "'"
                    cmd += f' DEFAULT {default_value}'

                if extras != '':
                    cmd += ' ' + extras

                if key_type != '':
                    if key_cmd != '':
                        key_cmd += ',\n'
                if key_type == 'PRI':
                    key_cmd += f'PRIMARY KEY (`{field_name}`)'
                elif key_type == 'UNI':
                    key_cmd += f'UNIQUE KEY `{field_name}` (`{field_name}`)'
                elif key_type == 'MUL':
                    key_cmd += f'KEY `{field_name}` (`{field_name}`)'

            if key_cmd != '':
                cmd += ',\n' + key_cmd
            cmd = f'CREATE TABLE `{table_name}` (\n' + cmd + '\n)\n'

        if self.logger:
            self.logger.log('info', f'Creating table "{table_name}"')

        try:
            cur = self.conn.cursor()
            cur.execute(cmd)
        except MySQLdb.Error as e:
            if self.logger:
                self.logger.log('fatal',
                                f'Failed to create table "{table_name}": {e}')
            raise

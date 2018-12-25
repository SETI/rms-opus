import warnings

class ImportDBException(BaseException):
    pass

class ImportDBSuper:
    def __init__(self, db_hostname, db_name, db_schema, db_user, db_password,
                 mult_form_types=[], import_prefix=None, logger=None,
                 read_only=False):
        self.log_sql = False

        self.db_hostname = db_hostname
        self.db_name = db_name
        self.db_schema = db_schema
        self.db_user = db_user
        self.db_password = db_password
        self.import_prefix = import_prefix
        self.logger = logger
        self.read_only = read_only
        self._mult_form_types = mult_form_types

        self.tables_created = []

        self._enter_stack = []
        self._cmds_executed = []
        self._log_sql_char_limit = 10000

        # Where Python warnings will be written
        self._warning_list = []
        self._old_warning_handler = None

    def _is_import_namespace(self, table_name):
        if self.import_prefix is None:
            return False
        return table_name.lower().startswith(self.import_prefix.lower())

    def _is_perm_namespace(self, table_name):
        if self.import_prefix is None:
            return True
        return not table_name.lower().startswith(self.import_prefix.lower())

    def convert_raw_to_namespace(self, namespace, raw_table_name):
        if self.import_prefix is None:
            return raw_table_name
        if namespace == 'import':
            return self.import_prefix + raw_table_name
        elif namespace == 'perm' or namespace == 'all':
            return raw_table_name
        assert False

    def convert_namespace_to_raw(self, namespace, table_name):
        if self.import_prefix is None:
            return table_name
        if namespace == 'import':
            assert table_name.lower().startswith(self.import_prefix.lower())
            return (table_name.replace(self.import_prefix, '')
                              .replace(self.import_prefix.lower(), ''))
        elif namespace == 'perm' or namespace == 'all':
            return table_name
        assert False

    def _execute(self, cmd, param_list=None, cur=None, mutates=False):
        if self.log_sql and self.logger:
            pretty_cmd = cmd.strip()
            if pretty_cmd.find('\n') >= 0:
                pretty_cmd = '\n' + pretty_cmd
            else:
                pretty_cmd = ' ' + pretty_cmd
            sim_str = ''
            if self.read_only and mutates:
                sim_str = '[SIM] '
            self.logger.log('debug', f'{sim_str} SQL COMMAND:'+
                                     pretty_cmd[:self._log_sql_char_limit]
                                     +f' PARAMS: {param_list}')
        self._cmds_executed.append(cmd)
        if not self.read_only or not mutates:
            if cur:
                cur.execute(cmd, param_list)
            else:
                with self.conn.cursor() as cur:
                    cur.execute(cmd, param_list)
                    self.conn.commit()

    def _execute_and_fetchall(self, cmd, func_name, cur=None):
        assert False, 'ImportDBSuper::_execute_and_fetchall must be overriden'

    @staticmethod
    def _make_warning_handler(warning_list):
        def _warning_handler(message, category, filename, lineno, file, line):
            warning_list.append(str(message))
        return _warning_handler

    def _enter(self, func_name):
        self._enter_stack.append(func_name)
        if len(self._enter_stack) == 1:
            self._cmds_executed = []
            self._warning_list = []
            if self.logger:
                self._old_warning_handler = warnings.showwarning
                warnings.showwarning = self._make_warning_handler(
                                                self._warning_list)

    def _exit(self):
        self._enter_stack.pop()
        if len(self._enter_stack) == 0:
            if self.logger and len(self._warning_list) > 0:
                self.logger.log('warning',
                           f'Warnings found during database operation:')
                for cmd in self._cmds_executed:
                    self.logger.log('warning', '  '+cmd)
                for w in self._warning_list:
                    self.logger.log('warning', '  '+w)
            warnings.showarning = self._old_warning_handler
            self._old_warning_handler = None

    def quote_identifier(self, s):
        assert False, 'ImportDBSuper::quote_identifier must be overriden'

    def table_names(self, namespace, prefix=None):
        assert False, 'ImportDBSuper::table_names must be overriden'

    def table_exists(self, namespace, table_name):
        self._enter('table_exists')
        table_names = [x.lower() for x in self.table_names(namespace)]
        self._exit()
        return table_name.lower() in table_names

    def table_info(self, namespace, table_name):
        assert False, 'ImportDBSuper::table_info must be overriden'

    def drop_table(self, namespace, raw_table_name, ignore_if_not_exists=True):
        assert False, 'ImportDBSuper::drop_table must be overriden'

    def create_table(self, namespace, raw_table_name, schema_filename,
                     ignore_if_exists=True):
        assert False, 'ImportDBSuper::create_table must be overriden'

    def analyze_table(self, namespace, raw_table_name):
        assert False, 'ImportDBSuper::analyze_table must be overriden'

    def read_rows(self, namespace, raw_table_name, column_names, where=None):
        self._enter('read_rows')

        table_name = self.convert_raw_to_namespace(namespace, raw_table_name)

        q = self.quote_identifier
        columns = ','.join([q(c) for c in column_names])

        cmd = f"SELECT {columns} FROM {q(table_name)}"
        if where:
            cmd += f" WHERE {where}"
        res = self._execute_and_fetchall(cmd, 'read_rows')
        self._exit()
        return res

    def insert_row(self, namespace, raw_table_name, row):
        assert False, 'ImportDBSuper::insert_row must be overriden'

    def insert_rows(self, namespace, raw_table_name, rows):
        assert False, 'ImportDBSuper::insert_rows must be overriden'

    def update_row(self, namespace, raw_table_name, row, where):
        assert False, 'ImportDBSuper::update_row must be overriden'

    def upsert_row(self, namespace, raw_table_name, key_name, row):
        assert False, 'ImportDBSuper::upsert_row must be overriden'

    def upsert_rows(self, namespace, raw_table_name, key_name, rows):
        assert False, 'ImportDBSuper::upsert_rows must be overriden'

    def delete_rows(self, namespace, table_name, where):
        assert False, 'ImportDBSuper::delete_rows must be overriden'

    def copy_rows_between_namespaces(self, src_namespace, dest_namespace,
                                     raw_table_name, where=None):
        assert False, ('ImportDBSuper::copy_rows_between_namespaces must be '+
                       'overriden')

    def general_select(self, cmd):
        assert False, 'ImportDBSuper::general_select must be overriden'

    def find_column_max(self, namespace, table_name, column_name):
        assert False, 'ImportDBSuper::find_column_max must be overriden'

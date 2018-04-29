import os, sys, glob
sys.path.append('c:/seti/opus/pds-tools')
from datetime import datetime

import MySQLdb
import json
import pdsparser

ERR_UNKNOWN_DATABASE = 1049
ERR_UNKNOWN_TABLE = 1051

class ImportDictionaryData(object):
    """Import utilities for the dictionary DB."""
    db_table = "definitions"
    tables = {}
    tables[db_table] = (
        f"CREATE TABLE IF NOT EXISTS `{db_table}` ("
        "   `term` char(255) NOT NULL,"
        "   `context` char(25) NOT NULL,"
        "   `def` text NOT NULL,"
        "   `expanded` text COMMENT 'expanded definition; text will work w/the imageURL to create a more expanded definition of term',"
        "   `image_URL` char(255) DEFAULT NULL COMMENT 'URL of image to be used with the expanded definition',"
        "   `more_info_URL` char(255) DEFAULT NULL COMMENT 'URL of pdf or image to be used to create a full page fully expanded definition',"
        "   `more_info_label` varchar(150) DEFAULT NULL COMMENT 'Required only if more_info_url is not blank.  Label for the page.',"
        "   `modified` tinyint(3) unsigned zerofill NOT NULL COMMENT 'set if row has been edited',"
        "   `import_date` date DEFAULT NULL,"
        "  PRIMARY KEY (`term`,`context`)"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8")

    schema_path = "C:/seti/opus/import/table_schemas/obs*.json"
    insert_query = (f"INSERT INTO `{db_table}` "
                        "(term, context, def, modified, import_date) "
                        "VALUES (%s, %s, %s, %s, %s)")

    def __init__(self, db_hostname, db_schema, db_user, db_password):
        self.db_hostname = db_hostname
        self.db_schema = db_schema
        self.db_user = db_user
        self.db_password = db_password

        self.definitions = []

        try:
            self.conn = MySQLdb.connect(host=self.db_hostname,
                                        user=self.db_user,
                                        passwd=self.db_password,
                                        db=self.db_schema)
        except MySQLdb.Error as e:
            print(f'Unable to connect to MySQL server: {e.args[1]}')

        else:
            print("Connection established")

    def __del__(self):
        self.conn.close()
        print("Connection closed")

    def create_dictionary(self, **kwargs):
        pds_file = "c:/seti/opus_dbs/pdsdd.full"
        json_list = glob.glob(self.schema_path)
        cursor = self.conn.cursor()
        if 'drop' in kwargs:
            print("Dropping table...")
            try:
                cursor.execute(f"DROP TABLE `{self.db_table}`")
            except MySQLdb.Error as e:
                if e.args[0] != ERR_UNKNOWN_TABLE:
                    print(f"Error in dropping table {self.db_table} - {e.args[0]}: {e.args[1]}")
        # create table if not exists; faster than checking to see if table exists first...
        try:
            cursor.execute(self.tables[self.db_table])
        except MySQLdb.Error as e:
            print(f"Error in creating table {self.db_table} - {e.args[0]}: {e.args[1]}")
            return

        if 'PDS' in kwargs:
            pds_file = kwargs['PDS']

        print(f"Importing {pds_file}")
        self.import_PDS(pds_file)

        if 'JSON' in kwargs: # If args is not empty.
            json_list = kwargs['JSON']

        for file_name in json_list:
            print(f"Importing {file_name}")
            self.import_JSON(file_name)

        cursor.close()

    def update_dictionary(self, term, context, definition):
        """ update_dictionary fetches a row from the dictionary database; if it exists,
            checks to see if the data has been modified.  If not, overwrites the data
            in that row with the new terms.
            If the term+context does not exist, update_dictionary will insert a new row.
        """
        cursor = self.conn.cursor()
        query = (f"SELECT * from {self.db_table} "
                 "WHERE term like %s AND context like %s")

        cursor.execute(query, (term, context))
        row = cursor.fetchone()
        if row is not None:
            if row['modified'] is not 0:
                query = (f"UPDATE {self.db_table} "
                     "SET def=%s"
                     "WHERE term like %s AND context like %s")
                cursor.execute(query, (definition, term, context))
                self.conn.commit()
        else:
            now = datetime.now().strftime('%Y-%m-%d')
            self.definitions.append((term, context, definition, 0, now))
            #self.cursor.execute(query, (term, context, def, 0))
            #self.conn.commit()
        cursor.close()

    def import_PDS(self, file_name):
        self.definitions = []
        context = "PSDD"
        try:
            label = pdsparser.PdsLabel.from_file(file_name)
            for item in range(0, len(label)):
                term = label[item]['NAME'].__str__().rstrip('\r\n')
                try:
                    definition = ' '.join(label[item]['DESCRIPTION'].__str__().split())
                    self.update_dictionary(term, context, definition)
                except:
                    print(F" item: {str(item)}")
                    print(sys.exc_info())
            if len(self.definitions):
                cursor = self.conn.cursor()
                cursor.executemany(self.insert_query, self.definitions)
                self.conn.commit()

        except IOError as e:
            print("I/O error  {e.errno}:  {str(e.strerror)}")

        except:
            print(term)
            print(sys.exc_info())

    def import_JSON(self, file_name):
        self.definitions = []
        try:
            with open(file_name, 'r') as fp:
                labels = json.load(fp)

            for label in labels:
                warning = ""
                if "definition" in label:
                    definition = label['definition']
                    if "pi_dict_name" in label and label['pi_dict_name'] is not None:
                        term = label['pi_dict_name']
                    else:
                        term = "UNKNOWN"
                        warning = f"WARNING: missing term for {definition}"

                    if "pi_dict_context" in label:
                        context = label['pi_dict_context']
                    else:
                        warning = f"WARNING: missing context for {term}: {definition}"

                    if not warning:
                        self.update_dictionary(term, context, definition)
                    else:
                        print(warning)

            if len(self.definitions):
                cursor = self.conn.cursor()
                cursor.executemany(self.insert_query, self.definitions)
                self.conn.commit()

        except IOError as e:
            print(f"I/O error  {e.errno}:  {str(e.strerror)}")

        except:
            print(label)
            print(sys.exc_info())

class ImportContextTable(object):
    """Import context DB for the dictionary."""
    """just here for safekeeping at the moment, don't really think we'll need this"""
    db_table = "context"
    tables = {}
    tables[db_table] = (
        f"CREATE TABLE IF NOT EXISTS `{db_table}` ("
        "   SELECT * FROM dictionary.contexts;CREATE TABLE `contexts` ("
        "       `name` char(25) NOT NULL,"
        "       `description` char(100) DEFAULT NULL,"
        "       `parent` char(25) DEFAULT NULL,"
        "       PRIMARY KEY (`name`),"
        "       UNIQUE KEY `contexts_name` (`name`),"
        "       UNIQUE KEY `name` (`description`)"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8")

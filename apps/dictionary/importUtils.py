import os, sys
sys.path.append('c:/seti/opus/pds-tools')
from datetime import datetime

import mysql.connector
import json
import pdsparser


class ImportDictionaryData(object):
    """Import utilities for the dictionary DB."""
    tables = {}
    tables['definitionsnew'] = (
        "CREATE TABLE `definitionsnew` ("
        "   `term` char(255) NOT NULL,"
        "   `context` char(25) NOT NULL,"
        "   `def` text NOT NULL,"
        "   `expanded` text COMMENT 'expanded definition; text will work w/the imageURL to create a more expanded definition of term',"
        "   `image_URL` char(255) DEFAULT NULL COMMENT 'URL of image to be used with the expanded definition',"
        "   `more_info_URL` char(255) DEFAULT NULL COMMENT 'URL of pdf or image to be used to create a full page fully expanded definition',"
        "   `modified` tinyint(3) unsigned zerofill NOT NULL COMMENT 'set if row has been edited',"
        "   `import_date` date DEFAULT NULL,"
        "  PRIMARY KEY (`term`,`context`)"
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8")

    def __init__(self, *args):
        print "connection established"
        self.cnx = mysql.connector.connect(user='debby', password='debby', host='127.0.0.1', database='dictionary')
        self.definitions = []
        self.insert_query = ("INSERT INTO `definitionsnew` "
                             "(term, context, def, modified, import_date) "
                             "VALUES (%s, %s, %s, %s, %s)")

    def __del__(self):
        self.cnx.close()
        print "connection closed"

    def create_dictionary(self, **kwargs):
        pds_file = "c:/seti/opus_dbs/pdsdd.full"
        json_list = {'obs_general.json',
                     'obs_instrument_COISS.json',
                     'obs_mission_cassini.json',
                    }
        cursor = self.cnx.cursor()
        for name, ddl in self.tables.iteritems():
            try:
                if 'drop' in kwargs:
                    cursor.execute("DROP TABLE `"+name+"`")
                    cursor.execute(ddl)
                    
            except mysql.connector.Error as err:
                if err.errno == errorcode.ER_TABLE_EXISTS_ERROR:
                    print err.msg

        if 'PDS' in kwargs:
            pds_file = kwargs['PDS']

        self.import_PDS(pds_file)

        if 'JSON' in kwargs: # If args is not empty.
            json_list = kwargs['JSON']

        for file_name in json_list:
            self.import_JSON(file_name)

        cursor.close()

    def update_dictionary(self, term, context, definition):
        """ update_dictionary fetches a row from the dictionary database; if it exists,
            checks to see if the data has been modified.  If not, overwrites the data
            in that row with the new terms.
            If the term+context does not exist, update_dictionary will insert a new row.
        """
        cursor = self.cnx.cursor(dictionary=True)
        query = ("SELECT * from definitionsnew "
                 "WHERE term like %s AND context like %s")

        cursor.execute(query, (term, context))
        row = cursor.fetchone()
        if row is not None:
            if row['modified'] is not 0:
                query = ("UPDATE definitionsnew "
                     "SET def=%s"
                     "WHERE term like %s AND context like %s")
                cursor.execute(query, (definition, term, context))
                self.cnx.commit()
        else:
            now = datetime.now().strftime('%Y-%m-%d')
            self.definitions.append((term, context, definition, 0, now))
            #self.cursor.execute(query, (term, context, def, 0))
            #self.cnx.commit()
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
                    print ' '+'item: '+ str(item)
                    print sys.exc_info()
            if len(self.definitions):
                cursor = self.cnx.cursor()
                cursor.executemany(self.insert_query, self.definitions)
                self.cnx.commit()

        except IOError as e:
            print "I/O error "+(e.errno)+": "+str(e.strerror)

        except:
            print term
            print sys.exc_info()

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
                        warning = "WARNING: missing term for " + definition

                    if "pi_dict_context" in label:
                        context = label['pi_dict_context']
                    else:
                        warning += "WARNING: missing context for " + term + " " + definition
                    if not warning:
                        self.update_dictionary(term, context, definition)
                    else:
                        print warning

            if len(self.definitions):
                cursor = self.cnx.cursor()
                cursor.executemany(self.insert_query, self.definitions)
                self.cnx.commit()

        except IOError as e:
            print "I/O error "+(e.errno)+": "+e.strerror

        except:
            print label
            print sys.exc_info()

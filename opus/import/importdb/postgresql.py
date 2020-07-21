# import csv
# import psycopg2 as pg

from importdb.super import ImportDBSuper

class ImportDBPostgreSQL(ImportDBSuper):
    def __init__(self, *args, **kwargs):
        super(ImportDBPostgreSQL, self).__init__(*args, **kwargs)

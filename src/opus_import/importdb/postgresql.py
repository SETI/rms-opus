# import csv
# import psycopg2 as pg

from opus_import.importdb.super import ImportDBSuper


class ImportDBPostgreSQL(ImportDBSuper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

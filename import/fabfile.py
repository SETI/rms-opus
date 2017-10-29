"""

    this is new and will generally run like:

        fab dump transfer build import_new_volumes

"""
import os, sys
from fabric.api import run, settings, env, cd, lcd, prompt, local
from fabric.contrib.console import confirm
from fabric.network import ssh
from secrets import DB_USER, DB_PASS, OPUS_PROD_DB_PW
from secrets import OPUS_CODE_STAGED_PRODUCTION as deploy_path
from config import DB_NEW_IMPORT as db_new_import
from config import DB_OPUS_PRODUCTION_NAME as db_opus

env.hosts = ['tools.pds-rings.seti.org']

def dump():
    """ dumps local new volumes database, trasnfers to production server """
    with lcd("~/dumps/"):
        local("mysqldump --opt {} > {}.sql -p{}".format(db_new_import, db_new_import, DB_PASS))
        local("gzip {}.sql".format(db_new_import))

def transfer():
    with lcd("~/dumps/"):
        local("scp {}.sql.gz lballard@tools.pds-rings.seti.org:~/dumps/.".format(db_new_import))

def build():
    """ builds new volumes database on production server """
    with cd("~/dumps/"):
        run("gunzip {}.sql.gz".format(db_new_import))
        run("mysqladmin drop {} -p{}".format(db_new_import, OPUS_PROD_DB_PW))
        run("mysqladmin create {} -p{}".format(db_new_import, OPUS_PROD_DB_PW))
        run("mysql {} < {}.sql -p{}".format(db_new_import, db_new_import, OPUS_PROD_DB_PW))

def import_new_volumes():
    with cd(deploy_path + '/import/'):
        run('sudo python import_new_volumes.py')

def drop_all_cache_tables():
    """ drops all opus cache tables in production db" """
    with cd(deploy_path + '/import/'):
        run('sudo python drop_cache_tables.py')

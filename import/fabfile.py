from fabric.api import run, settings, env, cd
import getpass

"""
This script creates the OPUS 2 database with the data from the OPUS 1 database.

First it creates the django models for the 'search' app at search/models.py, then uses some hacky
django hacking to generate the OPUS2 table schema. Then reads the OPUS1 database and makes it's own text
dump of it, and imports that data into the OPUS2 schema.

The Django models it creates at search/models.py should be deployed to production with the schema it spawned.

It should make a backup of current OPUS2 database before deleting it.

Currently assumes OPUS1 database is named 'Observations' and OPUS2 is called 'opus' heh heh.

----

fab -H lballard@pds-rings-tools.seti.org deploy_opus2:volumes=all

or

fab -H lballard@pds-rings-tools.seti.org deploy_opus2:volumes=COISS_2060,NHJULO_1001,COCIRS_5403

fab -H lballard@pds-rings-tools.seti.org deploy_opus2 -set volumes='COISS_2060,NHJULO_1001,COCIRS_5403'

aka

fab -H lballard@pds-rings-tools.seti.org deploy_opus2

"""

def host_type(**kwargs):
    run('uname -s')

# volumes like models COISS_2060,NHJULO_1001,COCIRS_5403 or 'all'
def deploy_opus2(volumes='COISS_2060,NHJULO_1001,COCIRS_5403'):

    # get server mysql username and pw
    mysql_pass = getpass.getpass('Enter mysql password: ')
    mysql_user = env.user

    # init
    with cd('/home/lballard/opus/'):

        # drop and create new opus
        run('mysql opus < import/drop_and_create_opus.sql -u%s -p%s' % (mysql_user, mysql_pass))

        # setup local env for development deploy at home/user/
        run('cp /home/django/djcode/opus/secrets.py .')
        run('cp /home/django/djcode/opus/settings_prod.py settings_local.py')

        # create the django models
        run('cp search/models.py import/models.py.bak')
        run('python import/build_obs.py models %s > search/models.py' % (volumes))


        # create the sql statements that will import the data:
        run('python import/build_obs.py sql  %s > import/import.sql' % (volumes))

        # generate the sql that will create the data tables, from the django models
        run('python manage.py sql search > import/search.sql')

        # now some alterations to the search.sql import,
        # removing any lines that start with "alter table observations' those are the ones where
        # django is adding extraneious keys for foreign key cols that make us exceed max 64 key limit
        # also want to add MyISAM check to the top:
        run("sed -i '1s/^/SET storage_engine=MYISAM;/' import/search.sql")
        run("perl -pi -e 's/^ALTER TABLE `observations`(.*)/\r\n/g' import/search.sql")

        # create the databsae tables in mysql
        run('mysql opus < import/search.sql -u%s -p%s' % (mysql_user, mysql_pass))

        # run syncdb to have django create the rest of the django tables:
        with settings(warn_only=True):
            run('python manage.py syncdb --noinput')

        # some extra fixes to the opus mysql tables
        # sorry to put a few random patches and sql here
        run('mysql opus < import/extra_sql_fixes.sql -u%s -p%s' % (mysql_user, mysql_pass))

        # now import the data
        run('mysql opus < import/import.sql -u%s -p%s -v' % (mysql_user, mysql_pass))

        print("\n Done!!! now go to the server and: \n ps aux | grep mysql")



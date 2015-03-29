from fabric.api import run, settings, env, cd, lcd, prompt, local
from fabric.contrib.console import confirm

root_path = '/Users/lballard/'
env.hosts = ['pds-rings-tools.seti.org']

prod_deploy_dir = 'opus'
# prod_deploy_dir = 'opus_dev'
git_branch = 'master'
memcached_port = '11211'
# memcached_port = '11212'

def tests_local():
    """
    runs all unit tests locally
    """
    with lcd(root_path + '/projects/opus/'):
        local("REUSE_DB=1 python manage.py test apps")

def push():
    """
    pushes code to repo and pushes repo to staging
    """

    # then checkout code from repo in another directory, and transfer that copy to server
    with lcd('/Users/lballard/'):
        # checks out git repo into local dir /users/lballard/opus
        # then rsyncs that copy to production

        # clean up old deploys
        local('rm -rf opus')

        # grab the local repo (this is all because couldn't grab remote from server)
        # local('git clone -b ' + git_branch + ' git@bitbucket.org:ringsnode/opus2.git')  # does not
        local('git clone -b ' + git_branch + ' file:////Users/lballard/projects/opus')

        if prod_deploy_dir != 'opus':
            local('rm -rf %s' % prod_deploy_dir)
            local('mv opus %s' % prod_deploy_dir) # rename it down here before rsyncing it

        # zip the javascript files, dunno why it commented out, broken?
        # local('python opus/deploy/deploy.py')
        # rsync that code to dev directory on production
        local('rsync -r -vc -e ssh --exclude .git %s lballard@pds-rings-tools.seti.org:~/.' % prod_deploy_dir)
        # local('rsync -r -vc -e ssh %s/static_media lballard@pds-rings.seti.org:~/sites/django_opus/.' % prod_deploy_dir)
        local('rsync -r -vc -e ssh %s/static_media lballard@pds-rings.seti.org:~/.' % prod_deploy_dir)

    # now go to pds-rings and move static_media into the right place
    with settings(host_string='pds-rings.seti.org'):
        run("sudo cp -r /Users/lballard/static_media /library/webserver/documents/opus2_resources/.")

def deploy():
    """
    take a backup of the currently deployed source on the server
    """
    with cd('/home/lballard/'):
        # first take a backup:
        run('sudo rsync -r -vc --exclude logs /home/django/djcode/' + prod_deploy_dir + ' backups/.')

        # go
        run('sudo rsync -r -vc --exclude logs ' + prod_deploy_dir + ' /home/django/djcode/.')
        run('sudo touch /home/django/djcode/' + prod_deploy_dir + '/*.wsgi')
        run('sudo touch /home/django/djcode/' + prod_deploy_dir + '/apache/*.wsgi')

        run('sudo python /home/django/djcode/opus/apps/tools/reset_deploy_datetime.py')


def cache_reboot():
        with cd('/home/lballard/'):
            # reset memcache
            """
            run('/usr/bin/memcached -l 127.0.0.1 -p %s restart' % memcached_port)
            run('/usr/bin/memcached -d -m 64 -l 127.0.0.1 -p %s -l -d' % memcached_port)
            """
            # reset django cache
            run('sudo python /home/django/djcode/' + prod_deploy_dir + '/deploy/cache_clear.py')


def tests_prod():
    # run all tests on production
    with cd('/home/django/djcode/%s/' % prod_deploy_dir):
        # this only runs a few app's test suites because the others have problems
        # where every Client() request.get returns a 404, unless you load it in a browser
        # first, then it runs ok, so something is awry in production testing.. todo
        run('sudo REUSE_DB=1 python manage.py test apps')
        # run('sudo REUSE_DB=1 python manage.py test search downloads paraminfo')




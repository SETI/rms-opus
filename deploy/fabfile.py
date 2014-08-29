from fabric.api import run, settings, env, cd, lcd, prompt, local
from fabric.contrib.console import confirm

root_path = '/Users/lballard/'
env.hosts = ['pds-rings-tools.seti.org']

deploy_dir = 'opus'

git_branch = 'master'

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
        # clean up old deploys
        local('rm -rf ~/opus')

        # grab the local repo (this is all because couldn't grab remote from server)
        # local('git clone -b ' + git_branch + ' git@bitbucket.org:ringsnode/opus2.git')
        local('git clone -b ' + git_branch + ' file:////Users/lballard/projects/opus')

        # zip the javascript files, dunno why it commented out, broken?
        # local('python opus/deploy/deploy.py')

        # rsync that code to dev directory on production
        local('rsync -r -vc -e ssh --exclude .git --exclude static_media opus lballard@pds-rings-tools.seti.org:~/.')

def deploy():
    """
    take a backup of the currently deployed source on the server
    """
    with cd('/home/lballard/'):
        run('sudo rsync -r -vc --exclude logs /home/django/djcode/' + deploy_dir + ' backups/.')
        run('sudo rsync -r -vc --exclude logs ' + deploy_dir + ' /home/django/djcode/.')
        run('sudo touch /home/django/djcode/' + deploy_dir + '/*.wsgi')
        run('sudo touch /home/django/djcode/' + deploy_dir + '/apache/*.wsgi')

        run('sudo python /home/django/djcode/opus/apps/tools/reset_deploy_datetime.py')


def cache_reboot():
        # reset memcache
        run('sudo killall memcached')
        run('/usr/bin/memcached -m 64 -p 11211 -l 127.0.0.1 -d')
        # reset django cache
        run('sudo python /home/django/djcode/' + deploy_dir + '/deploy/cache_clear.py')

def tests_prod():
    # run all tests on production
    with cd('/home/django/djcode/opus/'):
        run('REUSE_DB=1 python manage.py test apps')




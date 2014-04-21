from fabric.api import run, settings, env, cd, lcd, prompt, local
from fabric.contrib.console import confirm

root_path = '/Users/lballard/'
env.hosts = ['pds-rings-tools.seti.org']

def push():
    """
    pushes code to repo and pushes repo to staging
    """

    # then checkout code from repo in another directory, and transfer that copy to server
    with lcd('/Users/lballard/'):
        # clean up old deploys
        local('rm -rf ~/opus')

        # grab the remote repo (this is all because couldn't grab remote from server)
        local('git clone file:////Users/lballard/projects/opus')

        # zip the javascript files, dunno why it commented out, broken?
        # local('python opus/deploy/deploy.py')

        # rsync that code to dev directory on production
        local('rsync -r -vc -e ssh --exclude .git --exclude static_media opus lballard@pds-rings-tools.seti.org:~/.')

def deploy():
    """
    take a backup of the currently deployed source on the server
    """
    with cd('/home/lballard/'):
        run('rsync -r -vc /home/django/djcode/opus backups/.')
        run('sudo rsync -r -vc opus /home/django/djcode/.')
        run('sudo touch /home/django/djcode/opus/*.wsgi')

def memcache_reboot():
        run('killall memcached')
        run('/usr/bin/memcached -m 64 -p 11211 -l 127.0.0.1 -d')




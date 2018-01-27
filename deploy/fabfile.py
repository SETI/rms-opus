# -*- coding: utf-8 -*-
from fabric.api import run, settings, env, cd, lcd, prompt, local
from fabric.contrib.console import confirm
from slackclient import SlackClient
from secrets import SLACK_CHANNEL, SLACK_TOKEN, REMOTE_USERNAME
from fabric.network import ssh

"""
this is generally run like:

    fab tests_local push deploy cache_reboot tests

"""

local_root_path = '/Users/lballard/'
remote_root_path = '/home/lballard/'

# ssh.util.log_to_file("paramiko.log", 10)

env.use_ssh_config = True

host = prompt("production or dev server?", default='dev')

if 'prod' in host:
    env.hosts = ['tools.pds-rings.seti.org']
elif 'dev' in host:
    env.hosts = ['dev.pds-rings.seti.org']
else:
    sys.exit('please supply a host "prod" or "dev"')


prod_deploy_dir = 'opus'
static_assets_path = remote_root_path + 'rdsk/www/assets/' # static_media goes here
# git_branch = 'menu_bug'
git_branch = 'master'
git_revision = ''  # use this to roll back to a specific commit
memcached_port = '11211'
# memcached_port = '11212'

def tests_local():
    """
    runs all unit tests locally
    """
    with lcd(local_root_path + '/projects/opus/'):
        local("REUSE_DB=1 python manage.py test apps -x")


def push():
    """
    clones local repo into a temporary local directory,
    then pushes static assets to static server
    and code to app server staging area
    """

    # then checkout code from repo in another directory, and transfer that copy to server
    with lcd(local_root_path):
        # checks out git repo into local dir local_root_path/opus
        # then rsyncs that copy to production

        # clean up old deploys
        local('rm -rf opus')

        # grab the local repo (this is all because couldn't grab remote from server)
        # local('git clone -b ' + git_branch + ' git@bitbucket.org:ringsnode/opus2.git')  # does not
        local('git clone -b %s file:///%sprojects/opus' % (git_branch, local_root_path))

        # the repo gets named opus when you clone it, but you can name
        # that directory something else if you want, this handles that:
        if prod_deploy_dir != 'opus':
            local('rm -rf %s' % prod_deploy_dir)
            local('mv opus %s' % prod_deploy_dir) # rename it down here before rsyncing it

    with lcd('%sopus/' % local_root_path):
        if git_revision:
            local('git checkout %s' % git_revision)

    with lcd(local_root_path):
        # zip the javascript files,  why it commented out, broken?
        # local('python opus/deploy/deploy.py')
        # rsync that code to staging directory on production
        local('rsync -r -vc -e ssh --exclude .git %s %s@%s:~/.' % (prod_deploy_dir, REMOTE_USERNAME, env.hosts[0]))

    # move static_media into the right place
    with cd(remote_root_path):
        run("sudo cp -r %s/static_media %s." % (prod_deploy_dir, static_assets_path))


def deploy():
    """
    take a backup of the currently deployed source on the server
    then move staged copy to production location
    """
    with cd(remote_root_path):
        # first take a backup:
        run('sudo rsync -r -vc --exclude logs /home/django/djcode/' + prod_deploy_dir + ' backups/.')

        # copy the new code to production directory
        # exclude certain directories from deploying to production website
        exclude_str = "--exclude logs --exclude .git  --exclude import --exclude deploy"
        run('sudo rsync -r -vc {} {} /home/django/djcode/.'.format(exclude_str, prod_deploy_dir))


def cache_reboot():
    """
    refreshes python code wsgi, django caches, browser last modified, and memcached.
    """
    with cd(remote_root_path):

        # refresh the *.wsgi files (not sure which ones are actually doing job)
        run('sudo touch /home/django/djcode/' + prod_deploy_dir + '/*.wsgi')
        run('sudo touch /home/django/djcode/' + prod_deploy_dir + '/apache/*.wsgi')

        # tells browsers something has changed
        run('sudo python /home/django/djcode/opus/apps/tools/reset_deploy_datetime.py')

        # reset memcache
        try:
            run('sudo killall memcached')
        except:
            pass  # sometimes it's already killed
        run('/usr/bin/memcached -d -l 127.0.0.1 -m 1024 -p %s' % memcached_port)

        # reset django cache
        run('sudo python /home/django/djcode/' + prod_deploy_dir + '/deploy/cache_clear.py')


def tests():
    """ runs full unit tests on production """
    # run all tests on production and
    # if that flies notifies slack channel that opus has been deployed
    with cd('/home/django/djcode/%s/' % prod_deploy_dir):
        # this only runs a few app's test suites because the others have problems
        # where every Client() request.get returns a 404, unless you load it in a browser
        # first, then it runs ok, so something is awry in production testing.. todo
        run('sudo python manage.py test apps -x')

    if 'prod' in host:
        slack_notify()  # opus has deployed to production


def slack_notify():
    """ writes to opus slack that opus has been deployed """
    slack_msg = "OPUS has deployed to production. 💃🚀"
    slack_client = SlackClient(SLACK_TOKEN)
    slack_client.api_call(
        "chat.postMessage",
        channel=SLACK_CHANNEL,
        text=slack_msg
    )
    print slack_msg

# -*- coding: utf-8 -*-
from fabric.api import run, settings, env, cd, lcd, prompt, local
from fabric.contrib.console import confirm
from fabric.network import ssh
from slackclient import SlackClient
from secrets import REMOTE_USERNAME, REMOTE_USER_ROOT_PATH, REMOTE_WEB_ROOT_PATH, \
                    LOCAL_OPUS_PATH, LOCAL_GIT_CLONE_PATH, \
                    SLACK_CHANNEL, SLACK_TOKEN

"""
    # This is generally run like:

        fab tests_local push deploy cache_reboot tests

    # Background

    This script is for deploying to remote installs of opus.
    It will prompt you to specify prod/dev server.

    The push directive will clone the repo from your *local* git repo of opus
    and clone it into a separate directory (to avoid pushing any untracked content)
    Then it will push that repo to your home directory on the remote server.

    The deploy directive will create a copy of the previously deployed repo into backups/.
    and then copy the newly pushed github into the web root on that server.

    Run cache_reboot to refresh the web interface on the remote server.

    The tests directive will run the django tests on the remote install.

    # Initial Setup

    ## Edit the secrets.py file
    cp secrets.template.py secrets.py

    On the server you will need the following directory to exist
    in your remote home directory:

        backups/

"""
# ssh.util.log_to_file("paramiko.log", 10)

prod_deploy_dir_name = 'opus'  # NO trailing slash here.
                               # this is the name of the opus django directory
                               # in the dev/production web root

env.use_ssh_config = True  # untrue only on dev if no ssl cert

host = prompt("production or dev server?", default='dev')

if 'prod' in host:
    env.hosts = ['tools.pds-rings.seti.org']
elif 'dev' in host:
    env.hosts = ['dev.pds-rings.seti.org']
else:
    sys.exit('please supply a host "prod" or "dev"')

static_assets_path = REMOTE_USER_ROOT_PATH + 'rdsk/www/assets/' # static_media goes here
# git_branch = 'menu_bug'
git_branch = 'master'
git_revision = ''  # use this to roll back to a specific commit
memcached_port = '11211'
# memcached_port = '11212'

def tests_local():
    """
    runs all unit tests locally
    """
    with lcd(LOCAL_GIT_CLONE_PATH + '/projects/opus/'):
        local("REUSE_DB=1 python manage.py test apps -x")


def push():
    """
    clones local repo into a temporary local directory,
    then pushes static assets to static server
    and code to app server staging area
    """

    # then checkout code from repo in another directory, and transfer that copy to server
    with lcd(LOCAL_GIT_CLONE_PATH):
        # checks out git repo into local dir LOCAL_GIT_CLONE_PATH/opus
        # then rsyncs that copy to production

        # clean up old deploys
        local('rm -rf opus')

        # grab the local repo (this is all because couldn't grab remote from server)
        # local('git clone -b ' + git_branch + ' git@bitbucket.org:ringsnode/opus2.git')  # does not
        local('git clone -b {} file:///{}'.format(git_branch, LOCAL_OPUS_PATH))

    with lcd('%sopus/' % LOCAL_GIT_CLONE_PATH):
        if git_revision:
            local('git checkout %s' % git_revision)

    with lcd(LOCAL_GIT_CLONE_PATH):
        # zip the javascript files,  why it commented out, broken?
        # local('python opus/deploy/deploy.py')

        # rsync that code to staging directory on production
        local('rsync -r -vc -e ssh --exclude .git %s %s@%s:~/.' % (prod_deploy_dir_name, REMOTE_USERNAME, env.hosts[0]))

    # move static_media into the right place
    with cd(REMOTE_USER_ROOT_PATH):
        run("sudo cp -r %s/static_media %s." % (prod_deploy_dir_name, static_assets_path))


def deploy():
    """
    take a backup of the currently deployed source on the server
    then move staged copy to production location
    """
    with cd(REMOTE_USER_ROOT_PATH):
        # first take a backup:
        run('sudo rsync -r -vc --exclude logs {}{} backups/.'.format(REMOTE_WEB_ROOT_PATH,prod_deploy_dir_name))

        # copy the new code to production directory
        # exclude certain directories from deploying to production website
        exclude_str = "--exclude logs --exclude .git  --exclude import --exclude deploy"
        run('sudo rsync -r -vc {} {} /home/django/djcode/.'.format(exclude_str, prod_deploy_dir_name))


def cache_reboot():
    """
    refreshes python code wsgi, django caches, browser last modified, and memcached.
    """
    with cd(REMOTE_USER_ROOT_PATH):

        # refresh the *.wsgi files (not sure which ones are actually doing job)
        run('sudo touch {}{}/*.wsgi'.format(REMOTE_WEB_ROOT_PATH,prod_deploy_dir_name))
        run('sudo touch /home/django/djcode/{}{}/apache/*.wsgi'.format(REMOTE_WEB_ROOT_PATH,prod_deploy_dir_name))

        # tells browsers something has changed
        run('sudo python /home/django/djcode/opus/apps/tools/reset_deploy_datetime.py')

        # reset memcache
        try:
            run('sudo killall memcached')
        except:
            pass  # sometimes it's already killed
        run('/usr/bin/memcached -d -l 127.0.0.1 -m 1024 -p %s' % memcached_port)

        # reset django cache
        run('sudo python /home/django/djcode/{}{}/deploy/cache_clear.py'.format(REMOTE_WEB_ROOT_PATH, prod_deploy_dir_name))


def tests():
    """ runs full unit tests on production """
    # run all tests on production and
    # if that flies notifies slack channel that opus has been deployed
    with cd('{}{}'.format(REMOTE_WEB_ROOT_PATH, prod_deploy_dir_name)):
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

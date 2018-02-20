# -*- coding: utf-8 -*-
import sys
from fabric.api import run, settings, env, cd, lcd, prompt, local
from fabric.contrib.console import confirm
from fabric.network import ssh
from slackclient import SlackClient
from secrets import *
from config import PROD_URL, DEV_URL

"""
    # This is generally run like:

        fab tests_local push deploy cache_reboot tests

    # Background

    This script is for deploying to remote installs of OPUS.
    It will prompt you to specify prod/dev server.

    The push directive will clone the repo from your *local* git repo of OPUS
    and into a separate directory (to avoid pushing any untracked content).
    Then it will push that repo to REMOTE_USER_ROOT_PATH on the remote server.

    The deploy directive will create a copy of the previously deployed repo into backups/
    and then copy the newly pushed repo into the web root on that server.

    Run cache_reboot to refresh the web interface on the remote server.

    The tests directive will run the django tests on the remote install.

    # Initial Setup

    ## Edit the secrets.py file
    cp secrets.template.py secrets.py

    On the server you will need the following directory to exist
    in REMOTE_USER_ROOT_PATH:

        backups/

"""
# ssh.util.log_to_file("paramiko.log", 10)

env.use_ssh_config = True  # untrue only on dev if no ssl cert

host = prompt("production or dev server?", default='dev')

if 'prod' in host:
    env.hosts = [PROD_URL]
elif 'dev' in host:
    env.hosts = [DEV_URL]
else:
    sys.exit('please supply a host "prod" or "dev"')

git_branch = 'master'
git_revision = ''  # use this to roll back to a specific commit
memcached_port = '11211'

def tests_local():
    """
    runs all unit tests locally
    """
    with lcd(LOCAL_OPUS_PATH):
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
        local('rm -rf {}'.format(GIT_REPO_NAME))
        local('rm -rf {}'.format(REMOTE_OPUS_DIR_NAME))

        # grab the local repo (this is all because couldn't grab remote from server)
        local('git clone -b {} file:///{}'.format(git_branch, LOCAL_OPUS_PATH))

        # rename the repo to the directory name required on the server
        local('mv {} {}'.format(GIT_REPO_NAME, REMOTE_OPUS_DIR_NAME))

    with lcd('{}{}/'.format(LOCAL_GIT_CLONE_PATH, REMOTE_OPUS_DIR_NAME)):
        if git_revision:
            local('git checkout %s' % git_revision)

    with lcd(LOCAL_GIT_CLONE_PATH):
        # rsync that code to staging directory on production
        local('rsync -r -vc -e ssh --exclude .git {} {}@{}:{}/.'.format(REMOTE_OPUS_DIR_NAME, REMOTE_USERNAME, env.hosts[0], REMOTE_USER_ROOT_PATH))

    # move static_media into the right place
    with cd(REMOTE_USER_ROOT_PATH):
        run('sudo cp -r {}/static_media {}.'.format(REMOTE_OPUS_DIR_NAME, STATIC_ASSETS_PATH))


def deploy():
    """
    take a backup of the currently deployed source on the server
    then move staged copy to production location
    """
    with cd(REMOTE_USER_ROOT_PATH):
        # first take a backup:
        run('sudo rsync -r -vc --exclude logs {}{} backups/.'.format(REMOTE_WEB_ROOT_PATH, REMOTE_OPUS_DIR_NAME))

        # copy the new code to production directory
        # exclude certain directories from deploying to production website
        exclude_str = "--exclude logs --exclude .git  --exclude import --exclude deploy"
        run('sudo rsync -r -vc {} {} {}.'.format(exclude_str, REMOTE_OPUS_DIR_NAME, REMOTE_WEB_ROOT_PATH))


def cache_reboot():
    """
    refreshes python code wsgi, django caches, browser last modified, and memcached.
    """
    with cd(REMOTE_USER_ROOT_PATH):

        # refresh the *.wsgi files (not sure which ones are actually doing job)
        run('sudo touch {}{}/*.wsgi'.format(REMOTE_WEB_ROOT_PATH, REMOTE_OPUS_DIR_NAME))
        run('sudo touch {}{}/apache/*.wsgi'.format(REMOTE_WEB_ROOT_PATH, REMOTE_OPUS_DIR_NAME))

        # tells browsers something has changed
        run('sudo python {}{}/apps/tools/reset_deploy_datetime.py'.format(REMOTE_WEB_ROOT_PATH, REMOTE_OPUS_DIR_NAME))

        # reset memcache
        try:
            run('sudo killall memcached')
        except:
            pass  # sometimes it's already killed
        run('/usr/bin/memcached -d -l 127.0.0.1 -m 1024 -p %s' % memcached_port)

        # reset django cache
        run('sudo python {}{}/deploy/cache_clear.py'.format(REMOTE_WEB_ROOT_PATH, REMOTE_OPUS_DIR_NAME))


def tests():
    """ runs full unit tests on production """
    # run all tests on production and
    # if that flies notify slack channel that opus has been deployed
    with cd('{}{}'.format(REMOTE_WEB_ROOT_PATH, REMOTE_OPUS_DIR_NAME)):
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

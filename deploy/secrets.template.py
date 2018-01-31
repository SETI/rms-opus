# remote server settings
REMOTE_USERNAME = ''  # your remote user login name
REMOTE_WEB_ROOT_PATH = ''  # all _PATH vars require trailling slash

REMOTE_ROOT_PATH = ''  # This is your home directory on remote server
                       # You will end up with a clone copy of opus here.

# local settings
LOCAL_OPUS_PATH = ''  # your local clone of the opus repo, your working project root
LOCAL_GIT_CLONE_PATH = ''  # a clone of the opus repo will be created here
                           # make sure it's not the same directory as your
                           # project working directory, becuase this
                           # directory gets added/deleted by this script (see push())

SLACK_TOKEN = ''   # Empty is OK:
SLACK_CHANNEL = '' # this is for a final step in the deploy, a  slack bot that
                   # posts a msg to Rings Node slack channel
                   # If this fails it does not effect the deploy

#  *** ALL PATH VARIABLES MUST END IN / ***

### Remote server settings ###

# Your remote user login name
REMOTE_USERNAME = ''

# The staging directory on the remote server; a cloned copy of opus will be put here
REMOTE_USER_ROOT_PATH = ''

# The directory of the real web site
REMOTE_WEB_ROOT_PATH = ''

# The name of the opus directory to be placed inside REMOTE_WEB_ROOT_PATH
REMOTE_OPUS_DIR_NAME = ''

# static_media goes here on server
STATIC_ASSETS_PATH = ''

### Local settings ###

# The name of the GIT repo
GIT_REPO_NAME = ''

# Your local working project root
LOCAL_OPUS_PATH = '' + GIT_REPO_NAME + '/'

# A clone of the opus repo will be created here
# Make sure it's not the same directory as your
# project working directory, because this
# directory gets added/deleted by this script (see push())
LOCAL_GIT_CLONE_PATH = ''

### Slack ###

# These are used for announcing deployment; empty is OK
SLACK_TOKEN = ''
SLACK_CHANNEL = ''


import os
import sys
import json
import secrets
import datetime

# This file is a configuration file for CodeGra.de. You can edit all options in
# all CAPS not starting with a underscore without breaking anything.

# Statement for enabling the development environment
DEBUG = os.environ.get('DEBUG_ON', False) == 'True'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the database. If `CODEGRADE_DATABASE_URL` is found in the enviroment
# variables it is used. The string should be in this format for postgresql:
# `postgresql://dbusername:dbpassword@dbhost/dbname`
if 'CODEGRADE_DATABASE_URL' not in os.environ:
    SQLALCHEMY_DATABASE_URI = 'postgresql:///codegrade_dev'
else:
    SQLALCHEMY_DATABASE_URI = os.environ['CODEGRADE_DATABASE_URL']
DATABASE_CONNECT_OPTIONS = {}
_USING_SQLITE = SQLALCHEMY_DATABASE_URI.startswith('sqlite:///')

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# The amount of bytes that should be used for randomly generation JWT keys.
BYTES_RANDOM = 64

# Secret key for signing JWT tokens.
#
# If a enviroment variable `SECRET_KEY` is available this key is used, except
# when it is `GENERATE` which means it will geneate a random key. If the
# enviroment variable is not set the key will be set to `secret`
if os.environ.get('SECRET_KEY', False) == 'GENERATE':
    SECRET_KEY = secrets.token_hex(BYTES_RANDOM)
elif os.environ.get('SECRET_KEY', False):
    SECRET_KEY = os.environ.get('SECRET_KEY')
else:
    print('WARNING: No secret key given!', file=sys.stderr)
    if not DEBUG:
        print('You have to set SECRET_KEY in production mode', file=sys.stderr)
        sys.exit(1)
    SECRET_KEY = 'secret'

# This should be a strong random key that is not public. Generating random
# bytes works perfectly. It is probably useless to change this option.
LTI_SECRET_KEY = secrets.token_hex(BYTES_RANDOM)

JWT_ALGORITHM = 'HS512'
JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=30)

# Path for storage of uploaded files.
# WARNING: Make sure these directories exist.
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
MIRROR_UPLOAD_DIR = os.path.join(BASE_DIR, 'mirror_uploads')

# Maximum size in bytes for single upload request
MAX_UPLOAD_SIZE = 64 * 2 ** 20  # 64 megabytes

# All LTI consumer keys mapped to secret keys. Please add your own.
LTI_CONSUMER_KEY_SECRETS = {
    # 'my_lti': 'my_secret_key',
}

with open(os.path.join(BASE_DIR, 'seed_data', 'course_roles.json'), 'r') as f:
    _DEFAULT_COURSE_ROLES = json.load(f)

# The default site role a user should get. The name of this role should be
# present as a key in `seed_data/roles.json`.
DEFAULT_ROLE = 'Student'

# The external URL the server runs on.
EXTERNAL_URL = 'http://localhost:8080'

_enabled = True
# This variables contains all enables features, please do add, remove or edit
# any keys, the values however can and should be edited. A truth value (where
# `bool(value)` evaluates to `True`) enables the given feature. Please do not
# add or remove any keys.
FEATURES = {
    # Should any user be able to upload blackboard zips. If this is enabled
    # sometimes the username can collide with another user, meaning work is
    # uploaded for the wrong user. This option is UNSAFE to enable when working
    # on a multiple school instance.
    'BLACKBOARD_ZIP_UPLOAD': _enabled,
    # Should rubrics be enabled. This means rubrics can be created by teachers
    # and used for grading purposes.
    'RUBRICS': _enabled,
    # Should we automatically create a default role for LTI launches with roles
    # that are not known.
    'AUTOMATIC_LTI_ROLE': _enabled,
    # Should LTI be enabled.
    'LTI': _enabled,
}

with open(os.path.join(BASE_DIR, 'VERSION'), 'r') as f:
    _VERSION = f.read().strip()

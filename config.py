import os
import sys
import json
import secrets
import datetime

# Statement for enabling the development environment
DEBUG = os.environ.get('DEBUG_ON', False) == 'True'

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Define the database - we are working with
# SQLite for this example
if 'CODEGRADE_DATABASE_URL' not in os.environ:
    SQLALCHEMY_DATABASE_URI = 'postgresql:///codegrade_dev'
else:
    SQLALCHEMY_DATABASE_URI = os.environ['CODEGRADE_DATABASE_URL']
DATABASE_CONNECT_OPTIONS = {}

# Application threads. A common general assumption is
# using 2 per available processor cores - to handle
# incoming requests using one and performing background
# operations using the other.
THREADS_PER_PAGE = 2

# Enable protection agains *Cross-site Request Forgery (CSRF)*
CSRF_ENABLED = True

# Use a secure, unique and absolutely secret key for
# signing the data.
CSRF_SESSION_KEY = os.environ.get('CSRF_SECRET_KEY') or 'secret'

BYTES_RANDOM = 64

# Secret key for signing JWT tokens
if os.environ.get('SECRET_KEY', False) == 'GENERATE':
    SECRET_KEY = secrets.token_hex(BYTES_RANDOM)
elif os.environ.get('SECRET_KEY', False):
    SECRET_KEY = os.environ.get('SECRET_KEY')
else:
    print('WARNING: No secret key given!', file=sys.stderr)
    SECRET_KEY = 'secret'
LTI_SECRET_KEY = secrets.token_hex(BYTES_RANDOM)

JWT_ALGORITHM = 'HS512'
JWT_ACCESS_TOKEN_EXPIRES = datetime.timedelta(days=30)

# Path for storage of uploaded files
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
MIRROR_UPLOAD_DIR = os.path.join(BASE_DIR, 'mirror_uploads')

# Maximum size in bytes for single upload request
MAX_UPLOAD_SIZE = 64 * 2 ** 20  # 64 megabytes

LTI_CONSUMER_KEY_SECRETS = {
    'my_lti': '12345678',
}

with open(
    os.path.join(os.path.dirname(__file__), 'seed_data', 'course_roles.json'),
    'r'
) as f:
    DEFAULT_COURSE_ROLES = json.load(f)

DEFAULT_ROLE = 'Student'

EXTERNAL_URL = 'http://localhost:8080'

enabled = True
# This variables contains all enables features, please do add, remove or edit
# any keys, the values however can and should be edited. A truth value (where
# `bool(value)` evaluates to `True`) enables the given feature.
FEATURES = {
    # Should any user be able to upload blackboard zips. If this is enabled
    # sometimes the username can collide with another user, meaning work is
    # uploaded for the wrong user. This option is UNSAFE to enable when working
    # on a multiple school instance.
    'BLACKBOARD_ZIP_UPLOAD': enabled,
    # Should rubrics be enabled. This means rubrics can be created by teachers
    # and used for grading purposes.
    'RUBRICS': enabled,
    # Should LTI be enabled.
    'LTI': enabled,
}

with open(f'{os.path.dirname(__file__)}/VERSION', 'r') as f:
    VERSION = f.read().strip()

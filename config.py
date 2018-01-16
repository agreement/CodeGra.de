import os
import sys
import json
import typing as t
import secrets
import datetime
import subprocess
from configparser import SafeConfigParser

CONFIG: t.Dict[str, t.Any] = dict()
CONFIG['BASE_DIR'] = os.path.dirname(os.path.abspath(__file__))

os.environ['BASE_DIR'] = str(CONFIG['BASE_DIR'])

parser = SafeConfigParser(os.environ)
parser.read('config.ini')

if 'Back-end' not in parser:
    parser['Back-end'] = {}
if 'Features' not in parser:
    parser['Features'] = {}

backend_ops = parser['Back-end']
feature_ops = parser['Features']


def set_bool(
    out: t.MutableMapping[str, t.Any], parser: t.Any, item: str, default: bool
) -> None:
    val = parser.getboolean(item)
    out[item] = bool(default if val is None else val)


def set_float(
    out: t.MutableMapping[str, t.Any], parser: t.Any, item: str, default: float
) -> None:
    val = parser.getfloat(item)
    out[item] = float(default if val is None else val)


def set_int(
    out: t.MutableMapping[str, t.Any], parser: t.Any, item: str, default: int
) -> None:
    val = parser.getint(item)
    out[item] = int(default if val is None else val)


def set_str(
    out: t.MutableMapping[str, t.Any], parser: t.Any, item: str, default: str
) -> None:
    val = parser.get(item)
    out[item] = str(default if val is None else val)


set_bool(CONFIG, backend_ops, 'DEBUG', False)

# Define the database. If `CODEGRADE_DATABASE_URL` is found in the enviroment
# variables it is used. The string should be in this format for postgresql:
# `postgresql://dbusername:dbpassword@dbhost/dbname`
set_str(
    CONFIG, backend_ops, 'SQLALCHEMY_DATABASE_URI',
    os.getenv('SQLALCHEMY_DATABASE_URI', 'postgresql:///codegrade_dev')
)
CONFIG['_USING_SQLITE'] = CONFIG['SQLALCHEMY_DATABASE_URI'
                                 ].startswith('sqlite')
CONFIG['DATABASE_CONNECT_OPTIONS'] = {}

# The amount of bytes that should be used for randomly generation JWT keys.
set_int(CONFIG, backend_ops, 'BYTES_RANDOM', 64)

# Secret key for signing JWT tokens.
#
# If a enviroment variable `SECRET_KEY` is available this key is used, except
# when it is `GENERATE` which means it will geneate a random key. If the
# enviroment variable is not set the key will be set to `secret`
set_str(
    CONFIG, backend_ops, 'SECRET_KEY', 'secret'
    if CONFIG['DEBUG'] else secrets.token_hex(CONFIG['BYTES_RANDOM'])
)

# This should be a strong random key that is not public. Generating random
# bytes works perfectly. It is probably useless to change this option.
set_str(
    CONFIG, backend_ops, 'LTI_SECRET_KEY',
    secrets.token_hex(CONFIG['BYTES_RANDOM'])
)

CONFIG['JWT_ALGORITHM'] = 'HS512'

set_float(CONFIG, backend_ops, 'JWT_ACCESS_TOKEN_EXPIRES', 30)
CONFIG['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(
    days=CONFIG['JWT_ACCESS_TOKEN_EXPIRES']
)

# Path for storage of uploaded files.
# WARNING: Make sure these directories exist.
set_str(
    CONFIG, backend_ops, 'UPLOAD_DIR',
    os.path.join(CONFIG['BASE_DIR'], 'uploads')
)
if not os.path.isdir(CONFIG['UPLOAD_DIR']):
    print(
        f'The given uploads directory "{CONFIG["UPLOAD_DIR"]}" does not exist',
        file=sys.stderr
    )

set_str(
    CONFIG, backend_ops, 'MIRROR_UPLOAD_DIR',
    os.path.join(CONFIG['BASE_DIR'], 'mirror_uploads')
)
if not os.path.isdir(CONFIG['MIRROR_UPLOAD_DIR']):
    print(
        f'The given uploads directory "{CONFIG["MIRROR_UPLOAD_DIR"]}"'
        ' does not exist',
        file=sys.stderr
    )

# Maximum size in bytes for single upload request
set_float(
    CONFIG, backend_ops, 'MAX_UPLOAD_SIZE', 64 * 2 ** 20
)  # default: 64MB

with open(
    os.path.join(CONFIG['BASE_DIR'], 'seed_data', 'course_roles.json'), 'r'
) as f:
    CONFIG['_DEFAULT_COURSE_ROLES'] = json.load(f)

# The default site role a user should get. The name of this role should be
# present as a key in `seed_data/roles.json`.
set_str(CONFIG, backend_ops, 'DEFAULT_ROLE', 'Student')

# The external URL the server runs on.
set_str(CONFIG, backend_ops, 'EXTERNAL_URL', 'http://localhost:8080')

CONFIG['_VERSION'] = subprocess.check_output(
    ['git', 'describe', '--abbrev=0', '--tags']
).decode('utf-8').strip()

# Set email settings
set_str(CONFIG, backend_ops, 'MAIL_SERVER', 'localhost')
set_int(CONFIG, backend_ops, 'MAIL_PORT', 25)
set_bool(CONFIG, backend_ops, 'MAIL_USE_TLS', False)
set_bool(CONFIG, backend_ops, 'MAIL_USE_SSL', False)
set_str(CONFIG, backend_ops, 'MAIL_USERNAME', None)
set_str(CONFIG, backend_ops, 'MAIL_PASSWORD', None)
set_str(CONFIG, backend_ops, 'MAIL_DEFAULT_SENDER', None)
set_str(CONFIG, backend_ops, 'MAIL_MAX_EMAILS', None)
set_int(CONFIG, backend_ops, 'RESET_TOKEN_TIME', 86400)
set_str(
    CONFIG,
    backend_ops,
    'EMAIL_TEMPLATE',
    """
<p>Dear {user_name},

This email lets you reset your password on <a
href="{site_url}">{site_url}</a>. If you go to <a href="{url}">this page</a>
you can reset your password there. Please do not reply to this email.

If you have not triggered this action please ignore this email.</p>
    """.strip(),
)
set_str(
    CONFIG,
    backend_ops,
    'REMINDER_TEMPLATE',
    """
<p>Dear {user_name},

This email is a reminder that you have work left to grade on the assignment
"{assig_name}" on <a href="{site_url}">{site_url}</a>. If you go to <a
href="{site_url}/courses/{course_id}/assignments/{assig_id}/submissions">this
page</a> you can directly continue grading, which of course is joyful business
on CodeGra.de! Good luck with grading.

This email was automatically sent because of reminder that was set for this
assignment and you have not yet indicated you were done grading. You can
indicate this <a href="{site_url}/courses/{course_id}">here</a>.</p>
    """.strip(),
)
set_str(
    CONFIG,
    backend_ops,
    'GRADER_STATUS_TEMPLATE',
    """
<p>Dear {user_name},

This email is a reminder that your grade status has been reset to 'not done'
for "{assig_name}" on <a href="{site_url}">{site_url}</a>. If you go to <a
href="{site_url}/courses/{course_id}/assignments/{assig_id}/submissions">this
page</a> you can directly continue grading, which of course is joyful business
on CodeGra.de! Good luck with grading.

This email was automatically sent. The reason for this can be that a course
admin has reset your status or that you have been assigned new
submission(s).</p>
    """.strip(),
)

############
# FEATURES #
############
CONFIG['FEATURES'] = {}
# This section contains all features, please do not add, remove or edit any
# keys, the values however can and should be edited. A truth value enables the
# given feature. Please do not add or remove any keys.

# Should any user be able to upload blackboard zips. If this is enabled
# sometimes the username can collide with another user, meaning work is
# uploaded for the wrong user. This option is UNSAFE to enable when working
# on a multiple school instance.
set_bool(CONFIG['FEATURES'], feature_ops, 'BLACKBOARD_ZIP_UPLOAD', True)

# Should rubrics be enabled. This means rubrics can be created by teachers
# and used for grading purposes.
set_bool(CONFIG['FEATURES'], feature_ops, 'RUBRICS', True)

# Should we automatically create a default role for LTI launches with roles
# that are not known.
set_bool(CONFIG['FEATURES'], feature_ops, 'AUTOMATIC_LTI_ROLE', True)

# Should LTI be enabled.
set_bool(CONFIG['FEATURES'], feature_ops, 'LTI', True)

# Should incremental rubric submission be enabled.
set_bool(
    CONFIG['FEATURES'], feature_ops, 'INCREMENTAL_RUBRIC_SUBMISSION', True
)

# Should it be possible to register
set_bool(CONFIG['FEATURES'], feature_ops, 'REGISTER', True)

############
# LTI keys #
############
# All LTI consumer keys mapped to secret keys. Please add your own.
parser = SafeConfigParser()
parser.optionxform = str  # type: ignore
if parser.read('config.ini') and 'LTI Consumer keys' in parser:
    CONFIG['LTI_CONSUMER_KEY_SECRETS'] = dict(parser['LTI Consumer keys'])
else:
    CONFIG['LTI_CONSUMER_KEY_SECRETS'] = {}

##########
# CELERY #
##########
parser = SafeConfigParser()
parser.optionxform = str  # type: ignore
if parser.read('config.ini') and 'Celery' in parser:
    CONFIG['CELERY_CONFIG'] = dict(parser['Celery'])
else:
    CONFIG['CELERY_CONFIG'] = {}

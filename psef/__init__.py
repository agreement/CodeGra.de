# -*- py-isort-options: '("-sg *"); -*-
# Import flask and template operators
from flask import Flask, render_template, g
import typing as t
import os

import datetime
import json
import flask_login

from werkzeug.local import LocalProxy

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurations
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)


# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.before_request
def set_request_start_time():
    g.request_start_time = datetime.datetime.utcnow()


login_manager = flask_login.LoginManager()
login_manager.init_app(app)

LTI_ROLE_LOOKUPS = {
}  # type: t.Mapping[str, t.Mapping[str, t.Union[str, bool]]]
"""A LTI role to psef role lookup dictionary.

.. note::
    The roles are both course and user roles.
"""


def seed_lti_lookups():
    global LTI_ROLE_LOOKUPS  # NOQA
    _seed_data_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..', 'seed_data',
        'lti_lookups.json')
    with open(_seed_data_path, 'r') as f:
        LTI_ROLE_LOOKUPS = json.load(f)


seed_lti_lookups()

import psef.models  # NOQA

if t.TYPE_CHECKING:
    current_user: 'psef.models.User' = None
else:
    current_user = LocalProxy(lambda: flask_login.current_user)

import psef.auth  # NOQA
import psef.json  # NOQA
import psef.errors  # NOQA
import psef.files  # NOQA
import psef.lti  # NOQA
import psef.errors  # NOQA
import psef.helpers  # NOQA

# Register blueprint(s)
from .v1 import api as api_v1_blueprint  # NOQA
app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')


def create_app(config=None):
    if config is not None:
        app.config.update(config)
    return app


login_manager.init_app(app)

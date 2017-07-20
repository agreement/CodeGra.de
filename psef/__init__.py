# -*- py-isort-options: '("-sg *"); -*-
# Import flask and template operators
from flask import Flask, render_template, g
import typing as t
import os
import flask_jwt_extended as flask_jwt

import datetime
import json

from werkzeug.local import LocalProxy

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurations
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

jwt = flask_jwt.JWTManager(app)

# Define the database object which is imported
# by modules and controllers
_db = SQLAlchemy(
    app, session_options={'autocommit': False,
                          'autoflush': False}
)
db = LocalProxy(lambda: _db)


# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error: t.Type[Exception]) -> t.Tuple[t.Any, int]:
    return render_template('404.html'), 404


@app.before_request
def set_request_start_time() -> None:
    g.request_start_time = datetime.datetime.utcnow()


@app.before_request
@flask_jwt.jwt_optional
def set_current_user() -> None:
    pass


LTI_ROLE_LOOKUPS = {
}  # type: t.Mapping[str, t.Mapping[str, t.Union[str, bool]]]
"""A LTI role to psef role lookup dictionary.

.. note::
    The roles are both course and user roles.
"""


def seed_lti_lookups() -> None:
    global LTI_ROLE_LOOKUPS  # NOQA
    _seed_data_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..', 'seed_data',
        'lti_lookups.json'
    )
    with open(_seed_data_path, 'r') as f:
        LTI_ROLE_LOOKUPS = json.load(f)


seed_lti_lookups()

import psef.models  # NOQA

if t.TYPE_CHECKING:  # pragma: no cover
    current_user: 'psef.models.User' = None
else:
    current_user = flask_jwt.current_user

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


@app.teardown_request
def teardown_request(exception: t.Type[Exception]) -> None:
    db.session.expire_all()
    if exception:
        db.session.rollback()
    # db.session.remove()


def create_app(config: t.Mapping=None) -> t.Any:
    if config is not None:
        app.config.update(config)
    _db.init_app(app)
    return app

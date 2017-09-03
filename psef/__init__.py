# -*- py-isort-options: '("-sg *"); -*-
# Import flask and template operators
from flask import Flask, render_template, g
import typing as t
import os
import flask_jwt_extended as flask_jwt

import datetime
import json

import config

from werkzeug.local import LocalProxy

from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurations
app.config.update(config.CONFIG)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

jwt = flask_jwt.JWTManager(app)

# Define the database object which is imported
# by modules and controllers
_db = SQLAlchemy(
    app, session_options={'autocommit': False,
                          'autoflush': False}
)
db = LocalProxy(lambda: _db)


def _patch_sqlite() -> None:
    from sqlalchemy import event

    @event.listens_for(_db.engine, "connect")
    def do_connect(dbapi_connection: t.Any, connection_record: t.Any) -> None:
        # disable pysqlite's emitting of the BEGIN statement entirely.
        # also stops it from emitting COMMIT before any DDL.
        dbapi_connection.isolation_level = None

    @event.listens_for(_db.engine, "begin")
    def do_begin(conn: t.Any) -> None:
        # emit our own BEGIN
        conn.execute("BEGIN")


if app.config['_USING_SQLITE']:
    _patch_sqlite()


@app.before_request
def set_request_start_time() -> None:
    g.request_start_time = datetime.datetime.utcnow()


@app.before_request
@flask_jwt.jwt_optional
def set_current_user() -> None:
    # This code is necessary to make `flask_jwt_extended` understand that we
    # always want to try to load the given JWT token. The function body SHOULD
    # be empty here.
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
    if exception:  # pragma: no cover
        db.session.expire_all()
        db.session.rollback()


def create_app(config: t.Mapping=None) -> t.Any:
    # This code is only used for uwsgi
    if config is not None:  # pragma: no cover
        app.config.update(config)
    _db.init_app(app)
    return app

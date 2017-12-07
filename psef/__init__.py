# -*- py-isort-options: '("-sg *"); -*-
# Import flask and template operators
import sys
from flask import Flask, render_template, g, current_app
from celery import Celery
import typing as t
import os
import flask_jwt_extended as flask_jwt
from flask_mail import Mail

import datetime
from json import load as json_load

import config as global_config

from werkzeug.local import LocalProxy

app = current_app

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
        LTI_ROLE_LOOKUPS = json_load(f)


seed_lti_lookups()

if t.TYPE_CHECKING:  # pragma: no cover
    import psef.models
    current_user: 'psef.models.User' = None
else:
    current_user = flask_jwt.current_user


def create_app(config: t.Mapping = None, skip_celery: bool = False) -> t.Any:
    app = Flask(__name__)

    @app.before_request
    def set_request_start_time() -> None:
        g.request_start_time = datetime.datetime.utcnow()

    @app.before_request
    @flask_jwt.jwt_optional
    def set_current_user() -> None:
        # This code is necessary to make `flask_jwt_extended` understand that
        # we always want to try to load the given JWT token. The function body
        # SHOULD be empty here.
        pass

    @app.teardown_request
    def teardown_request(exception: t.Type[Exception]) -> None:
        if exception:  # pragma: no cover
            psef.models.db.session.expire_all()
            psef.models.db.session.rollback()

    # Configurations
    app.config.update(global_config.CONFIG)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config is not None:  # pragma: no cover
        app.config.update(config)

    import psef.models  # NOQA
    psef.models.init_app(app)

    import psef.mail  # NOQA
    psef.mail.init_app(app)

    import psef.auth  # NOQA
    psef.auth.init_app(app)

    import psef.errors  # NOQA
    psef.errors.init_app(app)

    import psef.tasks
    psef.tasks.init_app(app)

    import psef.json  # NOQA
    psef.json.init_app(app)

    import psef.errors  # NOQA
    import psef.files  # NOQA
    import psef.lti  # NOQA
    import psef.helpers  # NOQA
    import psef.linters  # NOQA

    import psef.tasks  # NOQA

    # Register blueprint(s)
    from .v1 import api as api_v1_blueprint  # NOQA
    app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')

    # Make sure celery is working
    if not skip_celery:  # pragma: no cover
        try:
            psef.tasks.add(2, 3)
        except Exception:  # pragma: no cover
            print(
                'Celery is not responding! Please check your config',
                file=sys.stderr
            )
            raise

    return app

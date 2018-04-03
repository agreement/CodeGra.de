"""
This package implements the backend for codegrade. Because of historic reasons
this backend is named ``psef``.

:license: AGPLv3, see LICENSE for details.
"""
import os
import sys
import json as system_json
import types
import typing as t
import datetime

import flask  # pylint: disable=unused-import
import flask_jwt_extended as flask_jwt
from flask import Flask, g, jsonify, current_app
from flask_limiter import Limiter, RateLimitExceeded

import config as global_config

app = current_app  # pylint: disable=invalid-name

LTI_ROLE_LOOKUPS = {
}  # type: t.Mapping[str, t.Mapping[str, t.Union[str, bool]]]
"""A LTI role to psef role lookup dictionary.

.. note::
    The roles are both course and user roles.
"""


def _seed_lti_lookups() -> None:
    """Seed the lti lookups.

    This is done by reading the ``lti_lookups.json`` file and setting its
    result in ``LTI_ROLE_LOOKUPS``. You should not call this function from
    application code, this code is only for the first initialization.
    """
    # Global is necessary here as we cannot set the variable otherwise
    global LTI_ROLE_LOOKUPS  # pylint: disable=global-statement
    _seed_data_path = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..', 'seed_data',
        'lti_lookups.json'
    )
    with open(_seed_data_path, 'r') as f:
        # We freeze this map as changing it is probably never correct.
        LTI_ROLE_LOOKUPS = types.MappingProxyType(system_json.load(f))


_seed_lti_lookups()

if t.TYPE_CHECKING:  # pragma: no cover
    import psef.models  # pylint: disable=unused-import
    current_user: 'psef.models.User' = None
else:
    current_user = flask_jwt.current_user  # pylint: disable=invalid-name


def limiter_key_func() -> None:  # pragma: no cover
    """This is the default key function for the limiter.

    The key function should be set locally at every place the limiter is used
    so this function always raises a :py:exc:`ValueError`.
    """
    raise ValueError('Key function should be overridden')


limiter = Limiter(key_func=limiter_key_func)  # pylint: disable=invalid-name


def create_app(config: t.Mapping = None, skip_celery: bool = False) -> t.Any:
    """Create a new psef app.

    :param config: The config mapping that can be used to override config.
    :param skip_celery: Set to true to disable sanity checks for celery.
    :returns: A new psef app object.
    """
    resulting_app = Flask(__name__)

    @resulting_app.before_request
    def __set_request_start_time() -> None:  # pylint: disable=unused-variable
        g.request_start_time = datetime.datetime.utcnow()

    @resulting_app.before_request
    @flask_jwt.jwt_optional
    def __set_current_user() -> None:  # pylint: disable=unused-variable
        # This code is necessary to make `flask_jwt_extended` understand that
        # we always want to try to load the given JWT token. The function body
        # SHOULD be empty here.
        pass

    @resulting_app.teardown_request
    def __teardown_request(exception: t.Type[Exception]) -> None:  # pylint: disable=unused-variable
        if exception:  # pragma: no cover
            models.db.session.expire_all()
            models.db.session.rollback()

    # Configurations
    resulting_app.config.update(global_config.CONFIG)
    resulting_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config is not None:  # pragma: no cover
        resulting_app.config.update(config)

    @resulting_app.errorhandler(RateLimitExceeded)
    def __handle_error(_: RateLimitExceeded) -> 'flask.Response':  # pylint: disable=unused-variable
        res = jsonify(
            errors.APIException(
                'Rate limit exceeded, slow down!',
                'Rate limit is exceeded',
                errors.APICodes.RATE_LIMIT_EXCEEDED,
                429,
            )
        )
        res.status_code = 429
        return res

    limiter.init_app(resulting_app)

    from . import auth
    auth.init_app(resulting_app)

    from . import parsers
    parsers.init_app(resulting_app)

    from . import models
    models.init_app(resulting_app)

    from . import mail
    mail.init_app(resulting_app)

    from . import errors
    errors.init_app(resulting_app)

    from . import tasks
    tasks.init_app(resulting_app)

    from . import json  # pylint: disable=reimported
    json.init_app(resulting_app)

    from . import files
    files.init_app(resulting_app)

    from . import lti
    lti.init_app(resulting_app)

    from . import helpers
    helpers.init_app(resulting_app)

    from . import linters
    linters.init_app(resulting_app)

    # Register blueprint(s)
    from . import v1 as api_v1
    api_v1.init_app(resulting_app)

    # Make sure celery is working
    if not skip_celery:  # pragma: no cover
        try:
            tasks.add(2, 3)
        except Exception:  # pragma: no cover
            print(  # pylint: disable=bad-builtin
                'Celery is not responding! Please check your config',
                file=sys.stderr
            )
            raise

    if hasattr(
        resulting_app, 'debug'
    ) and resulting_app.debug:  # pragma: no cover
        import flask_sqlalchemy
        typ = t.TypeVar('typ')

        @resulting_app.after_request
        def __print_queries(res: typ) -> typ:  # pylint: disable=unused-variable
            queries = flask_sqlalchemy.get_debug_queries()
            print(  # pylint: disable=bad-builtin
                (
                    '\n{} - - made {} amount of queries totaling '
                    '{:.4f} seconds. The longest took {:.4f} seconds.'
                ).format(
                    flask.request.path,
                    len(queries),
                    sum(q.duration for q in queries) if queries else 0,
                    max(q.duration for q in queries) if queries else 0,
                )
            )
            return res

    return resulting_app

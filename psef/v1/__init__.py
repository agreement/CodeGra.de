"""The module implementing version one of the codegra.de API.

.. warning:: This API is not yet stable, please proceed with caution!

:license: AGPLv3, see LICENSE for details.
"""
import typing as t

from flask import Blueprint

api = Blueprint('api', __name__)  # pylint: disable=invalid-name


def init_app(app: t.Any) -> None:
    """Initialize app by registering this blueprint.

    :param app: The flask app to register.
    :returns: Nothing
    """
    # These imports are done for the side effect of registering routes, so they
    # are NOT unused.
    from . import (  # pylint: disable=unused-variable
        code, login, courses, linters, snippets, assignments, permissions,
        submissions, files, about, roles, lti, users
    )
    app.register_blueprint(api, url_prefix='/api/v1')

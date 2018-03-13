"""
This module defines all API routes with the main directory "users". Thus the
APIs in this module are mostly used to manipulate :class:`.models.User` objects
and their relations. However to manipulate the current logged in user the main
directory "login" should be used.

:license: AGPLv3, see LICENSE for details.
"""
import typing as t

import flask_jwt_extended as flask_jwt
from flask import request, current_app
from validate_email import validate_email
from flask_limiter.util import get_remote_address
from sqlalchemy.sql.expression import or_

import psef.auth as auth
import psef.models as models
import psef.helpers as helpers
from psef import limiter, current_user
from psef.errors import APICodes, APIException
from psef.models import db
from psef.helpers import (
    JSONResponse, jsonify, escape_like, ensure_json_dict, ensure_keys_in_dict
)

from . import api


@api.route('/users/', methods=['GET'])
@auth.permission_required('can_search_users')
@limiter.limit('1 per second', key_func=lambda: str(current_user.id))
def search_users() -> JSONResponse[t.Sequence[models.User]]:
    """Search for a user by name and username.

    .. :quickref: User; Fuzzy search for a user by name and username.

    :param str q: The string to search for, all SQL wildcard are escaped and
        spaces are replaced by wildcards.

    :returns: A list of :py:class:`.models.User` objects that match the given
        query string.

    :raises APIException: If the query string less than 3 characters
        long. (INVALID_PARAM)
    :raises PermissionException: If the currently logged in user does not have
        the permission ``can_search_users``. (INCORRECT_PERMISSION)
    :raises RateLimitExceeded: If you hit this end point more than once per
        second. (RATE_LIMIT_EXCEEDED)
    """
    ensure_keys_in_dict(request.args, [('q', str)])
    query = t.cast(str, request.args.get('q'))

    if len(query) < 3:
        raise APIException(
            'The search string should be at least 3 chars',
            f'The search string "{query}" is not 3 chars or longer.',
            APICodes.INVALID_PARAM, 400
        )

    likes = [
        t.cast(t.Any, col).ilike(
            '%{}%'.format(
                escape_like(query).replace(' ', '%'),
            )
        ) for col in [models.User.name, models.User.username]
    ]
    return jsonify(models.User.query.filter(or_(*likes)).all())


@api.route('/user', methods=['POST'])
@helpers.feature_required('REGISTER')
@limiter.limit('1 per second', key_func=get_remote_address)
def register_user() -> JSONResponse[t.Mapping[str, str]]:
    """Create a new :class:`.models.User`.

    .. :quickref: User; Create a new user by registering it.

    :<json str username: The username of the new user.
    :<json str password: The password of the new user.
    :<json str email: The email of the new user.
    :<json str name: The full name of the new user.

    :>json str access_token: The JWT token that can be used to log in the newly
        created user.

    :raises APIException: If the not all given strings are at least 1
        char. (INVALID_PARAM)
    :raises APIException: If there is already a user with the given
        username. (OBJECT_ALREADY_EXISTS)
    :raises APIException: If the given email is not a valid
        email. (INVALID_PARAM)
    """
    content = ensure_json_dict(request.get_json())
    ensure_keys_in_dict(
        content,
        [('username', str),
         ('password', str),
         ('email', str),
         ('name', str)]
    )
    username = t.cast(str, content['username'])
    password = t.cast(str, content['password'])
    email = t.cast(str, content['email'])
    name = t.cast(str, content['name'])

    if not all([username, password, email, name]):
        raise APIException(
            'All fields should contain at least one character',
            (
                'The lengths of the given password, username and '
                'email were not all larger than 1'
            ),
            APICodes.INVALID_PARAM,
            400,
        )

    if db.session.query(
        models.User.query.filter_by(username=username).exists()
    ).scalar():
        raise APIException(
            'The given username is already in use',
            f'The username "{username}" is taken',
            APICodes.OBJECT_ALREADY_EXISTS,
            400,
        )

    if not validate_email(email):
        raise APIException(
            'The given email is not valid',
            f'The email "{email}"',
            APICodes.INVALID_PARAM,
            400,
        )

    role = models.Role.query.filter_by(
        name=current_app.config['DEFAULT_ROLE']
    ).one()
    user = models.User(
        username=username,
        password=password,
        email=email,
        name=name,
        role=role,
        active=True
    )
    db.session.add(user)
    db.session.commit()

    token: str = flask_jwt.create_access_token(
        identity=user.id,
        fresh=True,
    )
    return jsonify({'access_token': token})

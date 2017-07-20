"""
This module defines all API routes with the main directory "login". This APIs
are used to handle starting and closing the user session and update the :class:
User object of the logged in user.
"""
import typing as t

from flask import request

import psef.auth as auth
import psef.models as models
from psef import db, jwt, current_user
from psef.errors import APICodes, APIException
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api


@api.route("/login", methods=["POST"])
def login() -> JSONResponse[t.Mapping[str, t.Union[models.User, str]]]:
    """Login a :class:`.models.User` if the request is valid.

    .. :quickref: User; Login a given user.

    :returns: A response containing the JSON serialized user

    :<json str email: The email of the user to log in.
    :<json str password: The password of the user to log in.

    :raises APIException: If the request does not contain email and/or password
                          parameter. (MISSING_REQUIRED_PARAM)
    :raises APIException: If no user with email exists or the password is
                          wrong. (LOGIN_FAILURE)
    :raises APIException: If the user with the given email and password is
                          inactive. (INACTIVE_USER)
    """
    data = ensure_json_dict(request.get_json())
    ensure_keys_in_dict(data, [('email', str), ('password', str)])
    email = t.cast(str, data['email'])
    password = t.cast(str, data['password'])

    # WARNING: Do not use the `helpers.filter_single_or_404` function here as
    # we have to return the same error for a wrong email as for a wrong
    # password!
    user: t.Optional[models.User]
    user = db.session.query(models.User).filter(models.User.email == email
                                                ).first()

    if user is None or user.password != password:
        raise APIException(
            'The supplied email or password is wrong.', (
                'The user with email {} does not exist ' +
                'or has a different password'
            ).format(email), APICodes.LOGIN_FAILURE, 400
        )

    if not user.is_active:
        raise APIException(
            'User is not active',
            ('The user with id "{}" is not active any more').format(user.id),
            APICodes.INACTIVE_USER, 403
        )

    return jsonify(
        {
            'user':
                user,
            'access_token':
                jwt.create_access_token(
                    identity=user.id,
                    fresh=True,
                )
        }
    )


@api.route("/login", methods=["GET"])
@auth.login_required
def me() -> JSONResponse[t.Union[models.User, t.Mapping[int, str],
                                 t.Mapping[str, t.Any]]]:
    """Get the info of the currently logged in :class:`.models.User`.

    .. :quickref: User; Get information about the currently logged in user.

    :query type: If this is ``roles`` a mapping between course_id and role name
        will be returned, if this is ``extended`` the result of
        :py:meth:`models.User.__extended_to_json__()` will be returned. If this
        is something else or not present the result of
        :py:meth:`models.User.__to_json__()` will be returned.
    :returns: A response containing the JSON serialized user

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    if request.args.get('type') == 'roles':
        return jsonify(
            {
                role.course_id: role.name
                for role in current_user.courses.values()
            }
        )
    elif request.args.get('type') == 'extended':
        return jsonify(current_user.__extended_to_json__())
    return jsonify(current_user.__to_json__())


@api.route('/login', methods=['PATCH'])
@auth.login_required
def get_user_update() -> EmptyResponse:
    """Change data of the current :class:`.models.User`.

    .. :quickref: User; Update the currently logged users information.

    :returns: An empty response with return code 204

    :<json str email: The new email of the user.
    :<json str username: The new full name of the user.
    :<json str o_password: The old password of the user.
    :<json str n_password: The new password of the user.

    .. todo:: Refactor this code so it doesn't always require an old password.

    :raises APIException: If not all required parameters ('email',
                          'o_password', 'username', 'n_password') were in the
                          request. (MISSING_REQUIRED_PARAM)
    :raises APIException: If the old password was not correct.
                          (INVALID_CREDENTIALS)
    :raises APIException: If the new password or username is not valid.
                          (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not edit his own info.
                                 (INCORRECT_PERMISSION)
    """
    data = ensure_json_dict(request.get_json())

    ensure_keys_in_dict(
        data, [
            ('email', str),
            ('o_password', str),
            ('username', str),
            ('n_password', str)
        ]
    )
    email = t.cast(str, data['email'])
    o_password = t.cast(str, data['o_password'])
    n_password = t.cast(str, data['n_password'])
    username = t.cast(str, data['username'])

    user = current_user

    if user.password != o_password:
        raise APIException(
            'Incorrect password.', 'The supplied old password was incorrect',
            APICodes.INVALID_CREDENTIALS, 422
        )

    auth.ensure_permission('can_edit_own_info')

    invalid_input = {'password': '', 'username': ''}
    if n_password:
        invalid_input['password'] = user.validate_password(n_password)
    invalid_input['username'] = user.validate_username(username)

    if invalid_input['password'] != '' or invalid_input['username'] != '':
        raise APIException(
            'Invalid password or username.',
            'The supplied username or password did not meet the requirements',
            APICodes.INVALID_PARAM,
            422,
            rest=invalid_input
        )

    user.name = username
    user.email = email if email else user.email
    if n_password:
        user.password = n_password

    db.session.commit()
    return make_empty_response()

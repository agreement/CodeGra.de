"""
This module defines all API routes with the main directory "login". This APIs
are used to handle starting and closing the user session and update the :class:
User object of the logged in user.
"""
import typing as t

from flask import request
from validate_email import validate_email

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

    :>json user: The user that was logged in.
    :>jsonobj user: :py:class:`~.models.User`
    :>json str access_token: A JWT token that can be used to send requests to
        the server logged in as the given user.

    :raises APIException: If the request does not contain email and/or password
                          parameter. (MISSING_REQUIRED_PARAM)
    :raises APIException: If no user with email exists or the password is
                          wrong. (LOGIN_FAILURE)
    :raises APIException: If the user with the given email and password is
                          inactive. (INACTIVE_USER)
    """
    data = ensure_json_dict(request.get_json())
    ensure_keys_in_dict(data, [('username', str), ('password', str)])
    username = t.cast(str, data['username'])
    password = t.cast(str, data['password'])

    # WARNING: Do not use the `helpers.filter_single_or_404` function here as
    # we have to return the same error for a wrong email as for a wrong
    # password!
    user: t.Optional[models.User]
    user = db.session.query(models.User).filter(
        models.User.username == username
    ).first()

    if user is None or user.password != password:
        raise APIException(
            'The supplied email or password is wrong.', (
                'The user with email {} does not exist ' +
                'or has a different password'
            ).format(username), APICodes.LOGIN_FAILURE, 400
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
    :<json str name: The new full name of the user.
    :<json str old_password: The old password of the user.
    :<json str new_password: The new password of the user.

    :raises APIException: If not all required parameters ('email',
                          'o_password', 'name', 'n_password') were in the
                          request. (MISSING_REQUIRED_PARAM)
    :raises APIException: If the old password was not correct.
                          (INVALID_CREDENTIALS)
    :raises APIException: If the new password or name is not valid.
                          (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not edit his own info.
                                 (INCORRECT_PERMISSION)
    """
    data = ensure_json_dict(request.get_json())

    ensure_keys_in_dict(
        data, [
            ('email', str),
            ('old_password', str),
            ('name', str),
            ('new_password', str)
        ]
    )
    email = t.cast(str, data['email'])
    old_password = t.cast(str, data['old_password'])
    new_password = t.cast(str, data['new_password'])
    name = t.cast(str, data['name'])

    def _ensure_password(
        changed: str,
        msg: str='To change your {} you need a correct old password.'
    ) -> None:
        if current_user.password != old_password:
            raise APIException(
                msg.format(changed), 'The given old password was not correct',
                APICodes.INVALID_CREDENTIALS, 403
            )

    if old_password != '':
        _ensure_password('', 'The given old password is wrong')

    if current_user.name != name:
        if name == '':
            raise APIException(
                'Your new name cannot be empty',
                'The given new name was empty', APICodes.INVALID_PARAM, 400
            )
        current_user.name = name

    if current_user.email != email:
        if not validate_email(email):
            raise APIException(
                'The given email is not valid.',
                'The email "{email}" is not valid.',
                APICodes.INVALID_PARAM,
                400,
            )
        _ensure_password('email')
        current_user.email = email

    if new_password != '':
        _ensure_password('password')
        current_user.password = new_password

    db.session.commit()
    return make_empty_response()

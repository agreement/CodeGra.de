"""
This module defines all API routes with the main directory "login". This APIs
are used to handle starting and closing the user session and update the :class:
User object of the logged in user.
"""
import typing as t

import html2text
from flask import request
from flask_mail import Message
from validate_email import validate_email

import psef
import psef.auth as auth
import psef.models as models
import psef.helpers as helpers
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
                'The user with username "{}" does not exist ' +
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
    return jsonify(current_user)


def send_reset_password_email(user: models.User) -> None:
    token = user.get_reset_token()
    html_body = psef.app.config['EMAIL_TEMPLATE'].replace(
        '\n\n', '<br><br>'
    ).format(
        site_url=psef.app.config["EXTERNAL_URL"],
        url=f'{psef.app.config["EXTERNAL_URL"]}/reset_'
        f'password/?user={user.id}&token={token}',
        user_id=user.id,
        token=token,
        user_name=user.name,
        user_email=user.email,
    )
    text_maker = html2text.HTML2Text(bodywidth=78)
    text_maker.inline_links = False
    text_maker.wrap_links = False

    message = Message(
        subject=f'Reset password on {psef.app.config["EXTERNAL_URL"]}',
        body=text_maker.handle(html_body),
        html=html_body,
        recipients=[user.email],
    )
    try:
        psef.mail.send(message)
    except:
        raise APIException(
            'Something went wrong sending the email, '
            'please contact your site admin',
            f'Sending email to {user.id} went wrong.',
            APICodes.UNKOWN_ERROR,
            500,
        )
    db.session.commit()


@api.route('/login', methods=['PATCH'])
def get_user_update(
) -> t.Union[EmptyResponse, JSONResponse[t.Mapping[str, str]]]:
    """Change data of the current :class:`.models.User` and handle passsword
        resets.

    .. :quickref: User; Update the currently logged users information or reset
        a password.

    - If ``type`` is ``reset_password`` reset the password of the user with the
        given user_id with the given token to the given ``new_password``.
    - If ``type`` is ``reset_email`` send a email to the user with the given
      username that enables this user to reset its password.
    - Otherwise change user info of the currently logged in user.

    :returns: An empty response with return code 204 unless ``type`` is
        ``reset_password``, in this case a mapping between ``access_token`` and
        a jwt token is returned.

    :<json int user_id: The id of the user, only when type is reset_password.
    :<json str username: The username of the user, only when type is
        reset_email.
    :<json str token : The reset password token. Only if type is
        reset_password.
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

    if request.args.get('type', None) == 'reset_email':
        ensure_keys_in_dict(data, [('username', str)])
        send_reset_password_email(
            helpers.filter_single_or_404(
                models.User, models.User.username == data['username']
            )
        )
        return make_empty_response()
    elif request.args.get('type', None) == 'reset_password':
        ensure_keys_in_dict(
            data, [('new_password', str),
                   ('token', str),
                   ('user_id', int)]
        )

        password = t.cast(str, data['new_password'])
        user_id = t.cast(int, data['user_id'])
        token = t.cast(str, data['token'])

        if password == '':
            raise APIException(
                'Password should at least be 1 char',
                f'The password is {len(password)} chars long',
                APICodes.INVALID_PARAM, 400
            )
        user = helpers.get_or_404(models.User, user_id)
        user.reset_password(token, password)
        db.session.commit()
        return jsonify(
            {
                'access_token':
                    jwt.create_access_token(
                        identity=user.id,
                        fresh=True,
                    )
            }
        )

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
        auth.ensure_permission('can_edit_own_info')
        if name == '':
            raise APIException(
                'Your new name cannot be empty',
                'The given new name was empty', APICodes.INVALID_PARAM, 400
            )
        current_user.name = name

    if current_user.email != email:
        auth.ensure_permission('can_edit_own_info')
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
        auth.ensure_permission('can_edit_own_password')
        current_user.password = new_password

    db.session.commit()
    return make_empty_response()

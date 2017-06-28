from flask import jsonify, request
from sqlalchemy import func
from flask_login import login_user, logout_user, current_user, login_required

import psef.auth as auth
import psef.models as models
from psef import db
from psef.errors import APICodes, APIException

from . import api


@api.route("/login", methods=["POST"])
def login():
    """
    Login a user if the request is valid.

    Raises APIException:
        - request file does not contain email and/or password
        - request file contains invalid login credentials
        - request file contains inactive login credentials

    :returns: A response containing the JSON serialized user
    :rtype: Response
    """
    data = request.get_json()

    if 'email' not in data or 'password' not in data:
        raise APIException('Email and passwords are required fields',
                           'Email or password was missing from the request',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    user = db.session.query(models.User).filter(
        func.lower(models.User.email) == func.lower(data['email'])).first()

    # TODO: Use bcrypt password validation (as soon as we got that)
    # TODO: Return error whether user or password is wrong
    if user is None or user.password != data['password']:
        raise APIException('The supplied email or password is wrong.', (
            'The user with email {} does not exist ' +
            'or has a different password').format(data['email']),
                           APICodes.LOGIN_FAILURE, 400)

    if not login_user(user, remember=True):
        raise APIException('User is not active', (
            'The user with id "{}" is not active any more').format(user.id),
                           APICodes.INACTIVE_USER, 403)

    return me()


@api.route("/login", methods=["GET"])
@login_required
def me():
    """
    Get the info of the currently logged in user.

    :returns: A response containing the JSON serialized user
    :rtype: Response
    """
    if request.args.get('type') == 'roles':
        return jsonify({
            role.course_id: role.name for role in current_user.courses.values()
        })
    return jsonify(current_user)


@api.route('/login', methods=['PATCH'])
@login_required
def get_user_update():
    """
    Change data of the current user.

    :returns: An empty response with return code 204
    :rtype: (str, int)
    """
    data = request.get_json()

    required_keys = ['email', 'o_password', 'username', 'n_password']
    if not all(k in data for k in required_keys):
        raise APIException(
            'Email, username, n_password and o_password are required fields',
            ('Email, username, n_password or ' +
             'o_password was missing from the request'),
            APICodes.MISSING_REQUIRED_PARAM, 400)

    user = current_user

    if user.password != data['o_password']:
        raise APIException('Incorrect password.',
                           'The supplied old password was incorrect',
                           APICodes.INVALID_CREDENTIALS, 422)

    auth.ensure_permission('can_edit_own_info')

    invalid_input = {'password': '', 'username': ''}
    if data['n_password'] != '':
        invalid_input['password'] = user.validate_password(data['n_password'])
    invalid_input['username'] = user.validate_username(data['username'])

    if invalid_input['password'] != '' or invalid_input['username'] != '':
        raise APIException(
            'Invalid password or username.',
            'The supplied username or password did not meet the requirements',
            APICodes.INVALID_PARAM,
            422,
            rest=invalid_input)

    user.name = data['username']
    user.email = data['email']
    if data['n_password'] != '':
        user.password = data['n_password']

    db.session.commit()
    return '', 204


@api.route("/login", methods=["DELETE"])
def logout():
    """
    Logout the currently logged in user.

    :returns: An empty response with return code 204
    :rtype: (str, int)
    """
    logout_user()
    return '', 204

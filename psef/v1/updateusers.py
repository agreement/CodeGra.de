from flask import request
from flask_login import current_user, login_required
import psef.auth as auth
from psef import db
from psef.errors import APICodes, APIException
from . import api


@api.route('/update_user', methods=['PATCH'])
@login_required
def get_user_update():
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
    return ('', 204)

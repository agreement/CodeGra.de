"""
This module defines all API routes with the main directory "permissions". These
APIs are used communicate the permissions users.
"""

import functools

from flask import jsonify, request
from flask_login import current_user, login_required

from psef.errors import APICodes, APIException

from . import api


@api.route('/permissions/', methods=['GET'])
@login_required
def get_permissions():
    """Get the permissions (:class:`.models.Permission`) of the currently
    logged in :class:`.models.User`.

    :returns: A response containing the JSON serialized permissions and return
              code 200
    :rtype: (flask.Response, int)

    :raises APIException: If the supplied course id was not a number.
                          (INVALID_PARAM)
    :raises APIException: If specified permission does not exist.
                          (OBJECT_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    course_id = request.args.get('course_id')
    if course_id:
        try:
            course_id = int(course_id)
            fun = functools.partial(
                current_user.has_permission, course_id=course_id)
        except ValueError:
            raise APIException(
                'The specified course id was invalid',
                'The course id should be a number or but '
                '{} is not a number'.format(request.args['course_id']),
                APICodes.INVALID_PARAM, 400)
    elif request.args.get('type') == 'all':
        fun = current_user.get_permission_in_courses
    else:
        fun = current_user.has_permission

    if 'permission' in request.args:
        perm = request.args['permission']
        try:
            return jsonify(fun(perm)), 200
        except KeyError:
            raise APIException('The specified permission does not exist',
                               'The permission '
                               '"{}" is not real permission'.format(perm),
                               APICodes.OBJECT_NOT_FOUND, 404)
    else:
        return (jsonify(current_user.get_all_permissions(course_id=course_id)),
                200)

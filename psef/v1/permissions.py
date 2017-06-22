import functools

from flask import jsonify, request
from flask_login import current_user, login_required

from psef.errors import APICodes, APIException

from . import api


@api.route('/permissions/', methods=['GET'])
@login_required
def get_permissions():
    course_id = request.args.get('course_id')
    if course_id:
        try:
            course_id = int(course_id)
            fun = functools.partial(
                current_user.has_permission, course_id=course_id)
        except ValueError:
            raise APIException(
                'The specified course id was invalid',
                'The course id should be a number or "all" but '
                '{} is neither'.format(request.args['course_id']),
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

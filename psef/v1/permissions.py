"""
This module defines all API routes with the main directory "permissions". These
APIs are used communicate the permissions users.
"""

import typing as t

from flask import request
from flask_login import login_required

from psef import current_user
from psef.errors import APICodes, APIException
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api

if t.TYPE_CHECKING:
    import psef.models as models  # NOQA


@api.route('/permissions/', methods=['GET'])
@login_required
def get_permissions(
) -> JSONResponse[t.Union[t.Mapping[int, bool], t.Mapping[str, bool], bool]]:
    """Get the permissions (:class:`.models.Permission`) of the currently
    logged in :class:`.models.User`.

    .. :quickref: Permission; Get permissions for the currently logged in user.

    :returns: A response containing the JSON serialized permissions. For the
        exact format see (in this order):

        - If ``course_id`` is ``all``:
          :py:meth:`.User.get_permission_in_courses()`
        - If ``permission`` is not passed:
          :py:meth:`.User.get_all_permissions()`
        - Otherwise: :py:meth:`.User.has_permission()`

    :param int course_id: The id of the course to get the permissions for. If
        it is ``all`` the permissions for all courses will be requested. If it
        is not given global permissions will be given.
    :param str permission: The permission to request, if this is not passed all
        permissions for the given ``course_id`` will be given. If ``course_id``
        was not passed all global permissions will be returned. It is invalid
        to not pass ``permission`` if ``course_id`` is ``all``.

    .. todo:: Split this API call into multiple smaller calls.

    :raises APIException: If the supplied course id was not a number.
                          (INVALID_PARAM)
    :raises APIException: If specified permission does not exist.
                          (OBJECT_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    # fun: t.Union[t.Callable[[t.Union[str, 'models.Permission']], t.Mapping[
    #     int, bool]], t.Callable[[str], bool]]
    fun: t.Callable[[str], t.Union[t.Mapping[int, bool], bool]]

    course_id = request.args.get('course_id', default=None)
    if course_id == 'all':
        fun = current_user.get_permission_in_courses
    elif course_id:
        try:
            course_id = int(course_id)
        except ValueError:
            raise APIException(
                'The specified course id was invalid',
                'The course id should be a number or but '
                f'{course_id} is not a number', APICodes.INVALID_PARAM, 400
            )
        else:
            fun = lambda perm: current_user.has_permission(perm, course_id)  # NOQA
    else:
        fun = current_user.has_permission

    if 'permission' in request.args:
        perm = request.args['permission']
        try:
            return jsonify(fun(perm))
        except KeyError:
            raise APIException(
                'The specified permission does not exist',
                f'The permission "{perm}" is not real permission',
                APICodes.OBJECT_NOT_FOUND, 404
            )
    elif course_id == 'all':
        raise APIException(
            'You cannot query all permissions for all coursed',
            'Invalid combination of `course_id` and `permission` found',
            APICodes.INVALID_PARAM, 400
        )
    else:
        return jsonify(current_user.get_all_permissions(course_id=course_id))

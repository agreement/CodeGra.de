"""
This module defines all API routes with the main directory "permissions". These
APIs are used communicate the permissions users.
"""

import typing as t

from flask import request

import psef.auth as auth
from psef import current_user
from psef.errors import APICodes, APIException
from psef.helpers import (
    JSONResponse, jsonify, ensure_json_dict, ensure_keys_in_dict
)

from . import api

_PermMap = t.Mapping[str, bool]


@api.route('/permissions/', methods=['GET'])
@auth.login_required
def get_course_permissions(
) -> JSONResponse[t.Union[_PermMap, t.Mapping[int, _PermMap]]]:
    """Get all the global :class:`.psef.models.Permission` or the value of a
    permission in all courses of the currently logged in
    :class:`.psef.models.User`

    .. :quickref: Permission; Get global permissions or all the course
        permissions for the current user.

    :qparam str type: The type of permissions to get. This can be ``global`` or
        ``course``.
    :qparam str permission: The permissions to get when getting course
        permissions. You can pass this parameter multiple times to get multiple
        permissions.

    :returns: The returning object depends on the given ``type``. If it was
        ``global`` a mapping between permissions name and a boolean indicating
        if the currently logged in user has this permissions is returned.

        If it was ``course`` such a mapping is returned for every course the
        user is enrolled in. So it is a mapping between course ids and
        permission mapping. The permissions given as ``permission`` query
        parameter are the only ones that are present in the permission map.
    """
    ensure_keys_in_dict(request.args, [('type', str)])
    permission_type = t.cast(str, request.args['type']).lower()

    if permission_type == 'global':
        return jsonify(current_user.get_all_permissions())
    elif permission_type == 'course':
        # Make sure at least one permission is present
        ensure_keys_in_dict(request.args, [('permission', str)])
        perms = t.cast(t.List[str], request.args.getlist('permission'))
        return jsonify(current_user.get_permissions_in_courses(perms))
    else:
        raise APIException(
            'Invalid permission type given',
            f'The given type "{permission_type}" is not "global" or "course"',
            APICodes.INVALID_PARAM,
            400,
        )

"""
This module defines all API routes with the main directory "courses". The APIs
are used to create courses and return information about courses.

:license: AGPLv3, see LICENSE for details.
"""

import typing as t
import datetime

import sqlalchemy
from flask import request
from mypy_extensions import TypedDict

import psef.auth as auth
import psef.models as models
import psef.helpers as helpers
from psef import LTI_ROLE_LOOKUPS, current_user
from psef.errors import APICodes, APIException
from psef.models import db
from psef.helpers import (
    JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api

_UserCourse = TypedDict(  # pylint: disable=invalid-name
    '_UserCourse', {
        'User': models.User,
        'CourseRole': models.CourseRole
    }
)


@api.route('/courses/<int:course_id>/roles/<int:role_id>', methods=['DELETE'])
def delete_role(course_id: int, role_id: int) -> EmptyResponse:
    """Remove a :class:`.models.CourseRole` from the given
    :class:`.models.Course`.

    .. :quickref: Course; Delete a course role from a course.

    :param int course_id: The id of the course
    :returns: An empty response with return code 204

    :raises APIException: If the role with the given ids does not exist.
        (OBJECT_NOT_FOUND)
    :raises APIException: If there are still users with this role.
        (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not manage the course with the
        given id. (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_edit_course_roles', course_id)

    course = helpers.get_or_404(models.Course, course_id)
    role = helpers.filter_single_or_404(
        models.CourseRole, models.CourseRole.course_id == course_id,
        models.CourseRole.id == role_id
    )

    if course.lti_provider is not None:
        if any(r['role'] == role.name for r in LTI_ROLE_LOOKUPS.values()):
            raise APIException(
                'You cannot delete default LTI roles for a LTI course', (
                    'The course "{}" is an LTI course '
                    'so it is impossible to delete role {}'
                ).format(course.id, role.id), APICodes.INCORRECT_PERMISSION,
                403
            )

    sql = db.session.query(
        models.user_course
    ).filter(models.user_course.c.course_id == role_id).exists()
    if db.session.query(sql).scalar():
        raise APIException(
            'There are still users with this role',
            'There are still users with role {}'.format(role_id),
            APICodes.INVALID_PARAM, 400
        )

    db.session.delete(role)
    db.session.commit()

    return make_empty_response()


@api.route('/courses/<int:course_id>/roles/', methods=['POST'])
def add_role(course_id: int) -> EmptyResponse:
    """Add a new :class:`.models.CourseRole` to the given
    :class:`.models.Course`.

    .. :quickref: Course; Add a new course role to a course.

    :param int course_id: The id of the course
    :returns: An empty response with return code 204.

    :<json str name: The name of the new course role.

    :raises APIException: If the name parameter was not in the request.
                          (MISSING_REQUIRED_PARAM)
    :raises APIException: If the course with the given id was not found.
                          (OBJECT_NOT_FOUND)
    :raises APIException: If the course already has a role with the submitted
                          name. (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not manage the course with the
                                 given id. (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_edit_course_roles', course_id)

    content = ensure_json_dict(request.get_json())

    ensure_keys_in_dict(content, [('name', str)])
    name = t.cast(str, content['name'])

    course = helpers.get_or_404(models.Course, course_id)

    if models.CourseRole.query.filter_by(
        name=name, course_id=course_id
    ).first() is not None:
        raise APIException(
            'This course already has a role with this name',
            'The course "{}" already has a role named "{}"'.format(
                course_id, name
            ), APICodes.INVALID_PARAM, 400
        )

    role = models.CourseRole(name=name, course=course)
    db.session.add(role)
    db.session.commit()

    return make_empty_response()


@api.route('/courses/<int:course_id>/roles/<int:role_id>', methods=['PATCH'])
def update_role(course_id: int, role_id: int) -> EmptyResponse:
    """Update the :class:`.models.Permission` of a given
    :class:`.models.CourseRole` in the given :class:`.models.Course`.

    .. :quickref: Course; Update a permission for a certain role.

    :param int course_id: The id of the course.
    :param int role_id: The id of the course role.
    :returns: An empty response with return code 204.

    :<json str permission: The name of the permission to change.
    :<json bool value: The value to set the permission to (``True`` means the
        specified role has the specified permission).

    :raises APIException: If the value or permission parameter are not in the
                          request. (MISSING_REQUIRED_PARAM)
    :raises APIException: If the role with the given id does not exist or the
                          permission with the given name does not exist.
                          (OBJECT_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not manage the course with the
                                 given id. (INCORRECT_PERMISSION)
    """
    content = ensure_json_dict(request.get_json())

    auth.ensure_permission('can_edit_course_roles', course_id)

    ensure_keys_in_dict(content, [('value', bool), ('permission', str)])
    value = t.cast(bool, content['value'])
    permission = t.cast(str, content['permission'])

    role = helpers.filter_single_or_404(
        models.CourseRole,
        models.CourseRole.course_id == course_id,
        models.CourseRole.id == role_id,
    )
    perm = helpers.filter_single_or_404(
        models.Permission,
        models.Permission.name == permission,
        models.Permission.course_permission == True,  # pylint: disable=singleton-comparison
    )

    if (
        current_user.courses[course_id].id == role.id and
        perm.name == 'can_edit_course_roles'
    ):
        raise APIException(
            'You cannot remove this permission from your own role', (
                'The current user is in role {} which'
                ' cannot remove "can_edit_course_roles"'
            ).format(role.id), APICodes.INCORRECT_PERMISSION, 403
        )

    role.set_permission(perm, value)

    db.session.commit()

    return make_empty_response()


@api.route('/courses/<int:course_id>/roles/', methods=['GET'])
def get_all_course_roles(course_id: int) -> JSONResponse[t.Union[t.Sequence[
    models.CourseRole
], t.Sequence[t.MutableMapping[str, t.Union[t.Mapping[str, bool], bool]]]]]:
    """Get a list of all :class:`.models.CourseRole` objects of a given
    :class:`.models.Course`.

    .. :quickref: Course; Get all course roles for a single course.

    :param int course_id: The id of the course to get the roles for.
    :returns: An array of all course roles for the given course.

    :>jsonarr perms: All permissions this role has as returned
        by :py:meth:`.models.CourseRole.get_all_permissions`.
    :>jsonarrtype perms: :py:class:`t.Mapping[str, bool]`
    :>jsonarr bool own: True if the current course role is the current users
        course role.
    :>jsonarr ``**rest``: The course role as returned by
        :py:meth:`.models.CourseRole.__to_json__`

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not manage the course with the
                                 given id. (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_edit_course_roles', course_id)

    course_roles: t.Sequence[models.CourseRole]
    course_roles = models.CourseRole.query.filter_by(course_id=course_id
                                                     ).order_by(
                                                         models.CourseRole.name
                                                     ).all()

    if request.args.get('with_roles') == 'true':
        res = []
        for course_role in course_roles:
            json_course = course_role.__to_json__()
            json_course['perms'] = course_role.get_all_permissions()
            json_course['own'] = current_user.courses[course_role.course_id
                                                      ] == course_role
            res.append(json_course)
        return jsonify(res)
    return jsonify(course_roles)


@api.route('/courses/<int:course_id>/users/', methods=['PUT'])
def set_course_permission_user(
    course_id: int
) -> t.Union[EmptyResponse, JSONResponse[_UserCourse]]:
    """Set the :class:`.models.CourseRole` of a :class:`.models.User` in the
    given :class:`.models.Course`.

    .. :quickref: Course; Change the course role for a user.

    :param int course_id: The id of the course
    :returns: If the user_id parameter is set in the request the response will
              be empty with return code 204. Otherwise the response will
              contain the JSON serialized user and course role with return code
              201

    :raises APIException: If the parameter role_id or not at least one of
                          user_id and user_email are in the request.
                          (MISSING_REQUIRED_PARAM)
    :raises APIException: If no role with the given role_id or no user
                          with the supplied parameters exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIException: If the user was selected by email and the user is
                          already in the course. (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not manage the course with the
                                 given id. (INCORRECT_PERMISSION)

    .. todo::
        This function should probability be splitted.
    """
    auth.ensure_permission('can_edit_course_users', course_id)

    content = ensure_json_dict(request.get_json())
    ensure_keys_in_dict(content, [('role_id', int)])
    role_id = t.cast(int, content['role_id'])

    role = helpers.filter_single_or_404(
        models.CourseRole, models.CourseRole.id == role_id,
        models.CourseRole.course_id == course_id
    )

    res: t.Union[EmptyResponse, JSONResponse[_UserCourse]]

    if 'user_id' in content:
        ensure_keys_in_dict(content, [('user_id', int)])
        user_id = t.cast(int, content['user_id'])

        user = helpers.get_or_404(models.User, user_id)

        if user.id == current_user.id:
            raise APIException(
                'You cannot change your own role',
                'The user requested and the current user are the same',
                APICodes.INCORRECT_PERMISSION, 403
            )

        res = make_empty_response()
    elif 'username' in content:
        ensure_keys_in_dict(content, [('username', str)])

        user = helpers.filter_single_or_404(
            models.User, models.User.username == content['username']
        )

        if course_id in user.courses:
            raise APIException(
                'The specified user is already in this course',
                'The user {} is in course {}'.format(user.id, course_id),
                APICodes.INVALID_PARAM, 400
            )

        res = jsonify(
            {
                'User': user,
                'CourseRole': role,
            }, status_code=201
        )
    else:
        raise APIException(
            'None of the keys "user_id" or "role_id" were found', (
                'The given content ({})'
                ' does  not contain "user_id" or "user_email"'
            ).format(content), APICodes.MISSING_REQUIRED_PARAM, 400
        )

    user.courses[role.course_id] = role
    db.session.commit()
    return res


@api.route('/courses/<int:course_id>/users/', methods=['GET'])
def get_all_course_users(course_id: int
                         ) -> JSONResponse[t.Sequence[_UserCourse]]:
    """Return a list of all :class:`.models.User` objects and their
    :class:`.models.CourseRole` in the given :class:`.models.Course`.

    .. :quickref: Course; Get all users for a single course.

    :param int course_id: The id of the course
    :returns: A response containing the JSON serialized users and course roles

    :>jsonarr User:  A member of the given course.
    :>jsonarrtype User: :py:class:`~.models.User`
    :>jsonarr CourseRole: The role that this user has.
    :>jsonarrtype CourseRole: :py:class:`~.models.CourseRole`

    :raises APIException: If there is no course with the given id.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not manage the course with the
                                 given id. (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_edit_course_users', course_id)

    users: t.Sequence[sqlalchemy.util.KeyedTuple]
    users = db.session.query(models.User, models.CourseRole).join(
        models.user_course,
        models.user_course.c.user_id == models.User.id,
    ).join(
        models.CourseRole,
        models.CourseRole.id == models.user_course.c.course_id
    ).filter(models.CourseRole.course_id == course_id).all()

    user_course: t.List[_UserCourse]
    user_course = [
        {
            'User': user,
            'CourseRole': crole
        } for user, crole in users
    ]
    return jsonify(sorted(user_course, key=lambda item: item['User'].name))


@api.route('/courses/<int:course_id>/assignments/', methods=['GET'])
def get_all_course_assignments(
    course_id: int
) -> JSONResponse[t.Sequence[models.Assignment]]:
    """Get all :class:`.models.Assignment` objects of the given
    :class:`.models.Course`.

    .. :quickref: Course; Get all assignments for single course.

    The returned assignments are sorted by deadline.

    :param int course_id: The id of the course
    :returns: A response containing the JSON serialized assignments sorted by
        deadline of the assignment. See
        :py:func:`.models.Assignment.__to_json__` for the way assignments are
        given.

    :raises APIException: If there is no course with the given id.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not see assignments in the
                                 given course. (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_see_assignments', course_id)

    course = helpers.get_or_404(models.Course, course_id)

    return jsonify(course.get_all_visible_assignments())


@api.route('/courses/<int:course_id>/assignments/', methods=['POST'])
def create_new_assignment(course_id: int) -> JSONResponse[models.Assignment]:
    """Create a new course for the given assignment.

    .. :quickref: Course; Create a new assignment in a course.

    :param int course_id: The course to create an assignment in.

    :<json str name: The name of the new assignment.

    :returns: The newly created assignment.

    :raises PermissionException: If the current user does not have the
        ``can_create_assignment`` permission (INCORRECT_PERMISSION).
    """
    auth.ensure_permission('can_create_assignment', course_id)

    content = ensure_json_dict(request.get_json())
    ensure_keys_in_dict(content, [('name', str)])
    name = t.cast(str, content['name'])

    course = helpers.get_or_404(models.Course, course_id)

    if course.lti_course_id is not None:
        raise APIException(
            'You cannot add assignments to a LTI course',
            f'The course "{course_id}" is a LTI course',
            APICodes.INVALID_STATE, 400
        )

    assig = models.Assignment(
        name=name, course=course, deadline=datetime.datetime.utcnow()
    )
    db.session.add(assig)
    db.session.commit()

    return jsonify(assig)


@api.route('/courses/', methods=['POST'])
@auth.permission_required('can_create_courses')
def add_course() -> JSONResponse[models.Course]:
    """Add a new :class:`.models.Course`.

    .. :quickref: Course; Add a new course.

    :returns: A response containing the JSON serialization of the new course

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not create courses.
                                 (INCORRECT_PERMISSION)
    :raises APIException: If the parameter "name" is not in the request.
        (MISSING_REQUIRED_PARAM)
    """
    content = ensure_json_dict(request.get_json())
    ensure_keys_in_dict(content, [('name', str)])
    name = t.cast(str, content['name'])

    new_course = models.Course(name)
    db.session.add(new_course)
    db.session.commit()

    role = models.CourseRole.get_initial_course_role(new_course)
    current_user.courses[new_course.id] = role
    db.session.commit()

    return jsonify(new_course)


@api.route('/courses/', methods=['GET'])
@auth.login_required
def get_courses() -> JSONResponse[t.Sequence[t.Mapping[str, t.Any]]]:
    """Return all :class:`.models.Course` objects the current user is a member
    of.

    .. :quickref: Course; Get all courses the current user is enrolled in.

    :returns: A response containing the JSON serialized courses

    :param str extended: If set to `true` all the assignments for each course
        are also included under the key `assignments`.

    :>jsonarr str role: The name of the role the current user has in this
        course.
    :>jsonarr ``**rest``: JSON serialization of :py:class:`psef.models.Course`.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """

    def _get_rest(course: models.Course) -> t.Mapping[str, t.Any]:
        if request.args.get('extended') == 'true':
            return {
                'assignments': course.get_all_visible_assignments(),
                **course.__to_json__(),
            }
        return course.__to_json__()

    return jsonify(
        [
            {
                'role': c.name,
                **_get_rest(c.course),
            } for c in current_user.courses.values()
        ]
    )


@api.route('/courses/<int:course_id>', methods=['GET'])
@auth.login_required
def get_course_data(course_id: int) -> JSONResponse[t.Mapping[str, t.Any]]:
    """Return course data for a given :class:`.models.Course`.

    .. :quickref: Course; Get data for a given course.

    :param int course_id: The id of the course

    :returns: A response containing the JSON serialized course

    :>json str role: The name of the role the current user has in this
        course.
    :>json ``**rest``: JSON serialization of :py:class:`psef.models.Course`.

    :raises APIException: If there is no course with the given id.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    # TODO: Optimize this loop to a single query
    for course_role in current_user.courses.values():
        if course_role.course.id == course_id:
            return jsonify(
                {
                    'role': course_role.name,
                    **course_role.course.__to_json__(),
                }
            )

    raise APIException(
        'Course not found',
        'The course with id {} was not found'.format(course_id),
        APICodes.OBJECT_ID_NOT_FOUND, 404
    )


@api.route('/courses/<int:course_id>/permissions/', methods=['GET'])
@auth.login_required
def get_permissions_for_course(
    course_id: int,
) -> JSONResponse[t.Mapping[str, bool]]:
    """Get all the course :class:`.models.Permission` of the currently logged
    in :class:`.models.User`

    .. :quickref: Course; Get all the course permissions for the current user.

    :param int course_id: The id of the course of which the permissions should
        be retrieved.
    :returns: A mapping between the permission name and a boolean indicating if
        the currently logged in user has this permission.
    """
    course = helpers.get_or_404(models.Course, course_id)
    return jsonify(current_user.get_all_permissions(course))

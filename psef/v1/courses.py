"""
This module defines all API routes with the main directory "courses". The APIs
are used to create courses and return information about courses.
"""

from flask import jsonify, request
from flask_login import current_user, login_required

import psef.auth as auth
import psef.models as models
from psef import LTI_ROLE_LOOKUPS, db
from psef.errors import APICodes, APIException

from . import api


@api.route('/courses/<int:course_id>/roles/<int:role_id>', methods=['DELETE'])
def delete_role(course_id, role_id):
    """
    Add a new role to the given course.

    :param course_id: The id of the course
    :type course_id: int

    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: if the role with the given ids does not exist
        (OBJECT_NOT_FOUND)
    :raises APIException: if there are still users with this role
        (INVALID_PARAM)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not manage the course with the
        given id (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_manage_course', course_id)

    course = models.Course.query.get(course_id)

    role = models.CourseRole.query.filter_by(
        course_id=course_id, id=role_id).first()
    if role is None:
        raise APIException(
            'The specified role was not found',
            'The fole with name "{role_id}" was not found'.format(role_id),
            APICodes.OBJECT_NOT_FOUND, 404)

    if course.lti_provider is not None:
        if any(r['role'] == role.name for r in LTI_ROLE_LOOKUPS.values()):
            raise APIException(
                'You cannot delete default LTI roles for a LTI course',
                ('The course "{}" is an LTI course '
                 'so it is impossible to delete role {}').format(
                     course.id, role.id), APICodes.INCORRECT_PERMISSION, 403)

    sql = db.session.query(models.user_course).filter(
        models.user_course.c.course_id == role_id).exists()
    if db.session.query(sql).scalar():
        raise APIException(
            'There are still users with this role',
            'There are still users with role {}'.format(role_id),
            APICodes.INVALID_PARAM, 400)

    db.session.delete(role)
    db.session.commit()
    return '', 204


@api.route('/courses/<int:course_id>/roles/', methods=['POST'])
def add_role(course_id):
    """
    Add a new role to the given course.

    :param course_id: The id of the course
    :type course_id: int

    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: if the name parameter was not in the request
        (MISSING_REQUIRED_PARAM)
    :raises APIException: if the course with the given id was not found
        (OBJECT_NOT_FOUND)
    :raises APIException: if the course already has a role with the submitted
        name (INVALID_PARAM)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not manage the course with the
        given id (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_manage_course', course_id)

    content = request.get_json()

    if 'name' not in content:
        raise APIException('Some required keys were not found',
                           '"name" was not found in {}'.format(content),
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    course = models.Course.query.get(course_id)
    if course is None:
        raise APIException(
            'The specified course was not found',
            'The course with id "{}" was not found'.format(course_id),
            APICodes.OBJECT_NOT_FOUND, 404)

    name = content['name']
    if models.CourseRole.query.filter_by(
            name=name, course_id=course_id).first() is not None:
        raise APIException(
            'This course already has a role with this name',
            'The course "{}" already has a role named "{}"'.format(
                course_id, name), APICodes.INVALID_PARAM, 400)

    role = models.CourseRole(name=name, course=course)
    db.session.add(role)
    db.session.commit()

    return '', 204


@api.route('/courses/<int:course_id>/roles/<int:role_id>', methods=['PATCH'])
def update_role(course_id, role_id):
    """
    Update a permission of a specific course role in the given course.

    :param course_id: The id of the course
    :type course_id: int
    :param role_id: The id of the role
    :type role_id: int

    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: if the value or permission parameter are not in the
        request (MISSING_REQUIRED_PARAM)
    :raises APIException: if the role with the given id does not exist or the
        permission with the given name does not exist (OBJECT_NOT_FOUND)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not manage the course with the
        given id (INCORRECT_PERMISSION)
    """
    content = request.get_json()

    auth.ensure_permission('can_manage_course', course_id)

    if ('value' not in content or 'permission' not in content):
        raise APIException(
            'Some required keys were not found',
            '"permission" or "value" were not found in {}'.format(content),
            APICodes.MISSING_REQUIRED_PARAM, 400)

    role = models.CourseRole.query.filter_by(
        course_id=course_id, id=role_id).first()
    if role is None:
        raise APIException(
            'The specified role was not found',
            'The fole with name "{role_id}" was not found'.format(role_id),
            APICodes.OBJECT_NOT_FOUND, 404)

    perm = models.Permission.query.filter_by(
        name=content['permission']).first()
    if perm is None:
        raise APIException(
            'The specified permission was not found',
            'The fole with name "{permission}" was not found'.format(
                **content), APICodes.OBJECT_NOT_FOUND, 404)

    if (current_user.courses[course_id].id == role.id and
            role.name == 'can_manage_course'):
        raise APIException('You remove this permission from your own role', (
            'The current user is in role {} which'
            ' cannot remove "can_manage_course"').format(role.id),
                           APICodes.INCORRECT_PERMISSION, 403)

    role.set_permission(perm, content['value'])

    db.session.commit()

    return '', 204


@api.route('/courses/<int:course_id>/roles/', methods=['GET'])
def get_all_course_roles(course_id):
    """
    Get a list of all course roles of a given course.

    :param course_id: The id of the course
    :type course_id: int

    :returns: A response containing the JSON serialized course roles.
    :rtype: Response

    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not manage the course with the
        given id (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_manage_course', course_id)

    courses = sorted(
        models.CourseRole.query.filter_by(course_id=course_id).all(),
        key=lambda item: item.name)
    if request.args.get('with_roles') == 'true':
        res = []
        for course in courses:
            json_course = course.__to_json__()
            json_course['perms'] = course.get_all_permissions()
            json_course['own'] = current_user.courses[
                course.course_id] == course
            res.append(json_course)
        courses = res
    return jsonify(courses)


@api.route('/courses/<int:course_id>/users/', methods=['PUT'])
def set_course_permission_user(course_id):
    """
    Set the course role of a specific user.

    :param course_id: The id of the course
    :type course_id: int

    :returns: If the user_id parameter is set in the request the response will
        be empty with return code 204. Otherwise the response will contain the
        JSON serialized user and course role with return code 201
    :rtype: (Response, int) or (str, int)

    :raises APIException: if the parameter role_id or not at least one of
        user_id and user_email are in the request (MISSING_REQUIRED_PARAM)
    :raises APIException: if no role with the given role_id or no user
        with the supplied parameters exists (OBJECT_ID_NOT_FOUND)
    :raises APIException: if the user was selected by email and the user is
        already in the course (INVALID_PARAM)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not manage the course with the
        given id (INCORRECT_PERMISSION)
    """
    content = request.get_json()

    auth.ensure_permission('can_manage_course', course_id)

    if 'role_id' not in content:
        raise APIException(
            'Required parameter "role_id" is missing',
            'The given content ({}) does  not contain "role_id"'.format(
                content), APICodes.MISSING_REQUIRED_PARAM, 400)

    if 'user_id' not in content and 'user_email' not in content:
        raise APIException(
            'None of the keys "user_id" or "role_id" were found',
            ('The given content ({})'
             ' does  not contain "user_id" or "user_email"').format(content),
            APICodes.MISSING_REQUIRED_PARAM, 400)

    role = models.CourseRole.query.get(content['role_id'])
    if role is None:
        raise APIException('Specified role was not found',
                           'The role {role_id} was not found'.format(
                               **content), APICodes.OBJECT_ID_NOT_FOUND, 404)

    if 'user_id' in content:
        user = models.User.query.get(content['user_id'])

        if user is None:
            raise APIException('The specified user was not found',
                               'The user {user_id} was not found'.format(
                                   **content), APICodes.OBJECT_ID_NOT_FOUND,
                               404)

        if user.id == current_user.id:
            raise APIException(
                'You cannot change your own role',
                'The user requested and the current user are the same',
                APICodes.INCORRECT_PERMISSION, 403)

        res = '', 204
    else:
        user = models.User.query.filter_by(email=content['user_email']).first()

        if user is None:
            raise APIException(
                'The specified user email was not found',
                'The user with email "{user_email}" was not found'.format(
                    **content), APICodes.OBJECT_ID_NOT_FOUND, 404)

        if role.course_id in user.courses:
            raise APIException('The specified user is already in this course',
                               'The user {} is in course {}'.format(
                                   user.id, role.course_id),
                               APICodes.INVALID_PARAM, 400)

        res = jsonify({
            'User': user,
            "CourseRole": role,
        }), 201

    user.courses[role.course_id] = role
    db.session.commit()
    return res


@api.route('/courses/<int:course_id>/users/', methods=['GET'])
def get_all_course_users(course_id):
    """
    Return a list of all user and their course role in the given course.

    :param course_id: The id of the course
    :type course_id: int

    :returns: A response containing the JSON serialized users and course roles
    :rtype: Response

    :raises APIException: if there is no course with the given id
        (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not manage the course with the
        given id (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_manage_course', course_id)

    users = db.session.query(models.User, models.CourseRole).join(
        models.user_course,
        models.user_course.c.user_id == models.User.id).join(
            models.CourseRole,
            models.CourseRole.id == models.user_course.c.course_id).filter(
                models.CourseRole.course_id == course_id).all()

    users = [dict(zip(row.keys(), row)) for row in users]
    return jsonify(sorted(users, key=lambda item: item['User'].name))


@api.route('/courses/<int:course_id>/assignments/', methods=['GET'])
def get_all_course_assignments(course_id):
    """
    Get all assignments of the course with the given id sorted by deadline.

    :param course_id: The id of the course
    :type course_id: int
    :returns: A response containing the JSON serialized assignments
    :rtype: Response

    :raises APIException: if there is no course with the given id
        (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not see assignments in the
        course with the given id (INCORRECT_PERMISSION)
    """
    auth.ensure_permission('can_see_assignments', course_id)

    course = models.Course.query.get(course_id)
    if course is None:
        raise APIException('Specified course not found',
                           'The course {} was not found'.format(course_id),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)

    return jsonify(sorted(course.assignments, key=lambda item: item.deadline))


@api.route('/courses/', methods=['POST'])
@auth.permission_required('can_create_courses')
def add_course():
    """
    Add a new course.

    :returns: A response containing the JSON serialization of the new course
    :rtype: Response

    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not create courses
        (INCORRECT_PERMISSION)
    :raises APIException: if the parameter "name" is not in the request
        (MISSING_REQUIRED_PARAM)
    """
    content = request.get_json()

    if 'name' not in content:
        raise APIException(
            'Required parameter "name" is missing',
            'The given content ({}) does  not contain "name"'.format(content),
            APICodes.MISSING_REQUIRED_PARAM, 400)
    new_course = models.Course(name=content['name'])
    db.session.add(new_course)
    db.session.commit()

    return jsonify(new_course)


@api.route('/courses/', methods=['GET'])
@login_required
def get_courses():
    """
    Return all courses of the current user.

    :returns: A response containing the JSON serialized courses
    :rtype: Response

    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    """
    return jsonify([{
        'name': c.course.name,
        'id': c.course.id,
        'role': c.name
    } for c in current_user.courses.values()])


@api.route('/courses/<int:course_id>', methods=['GET'])
@login_required
def get_course_data(course_id):
    """
    Return course data for a given course id

    :param course_id: The id of the course
    :type course_id: int

    :returns: A response containing the JSON serialized course
    :rtype: Response

    :raises APIException: if there is no course with the given id
        (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    """
    for c in current_user.courses.values():
        if c.course.id == course_id:
            return jsonify({
                'name': c.course.name,
                'id': c.course.id,
                'role': c.name
            })

    raise APIException('Course not found',
                       'The course with id {} was not found'.format(course_id),
                       APICodes.OBJECT_ID_NOT_FOUND, 404)

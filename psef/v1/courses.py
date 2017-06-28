from flask import jsonify, request
from flask_login import current_user, login_required

import psef.auth as auth
import psef.models as models
from psef import db
from psef.errors import APICodes, APIException

from . import api


@api.route('/courses/<int:course_id>/roles/', methods=['GET'])
def get_all_course_roles(course_id):
    auth.ensure_permission('can_manage_course', course_id)

    return jsonify(
        sorted(
            models.CourseRole.query.filter_by(course_id=course_id).all(),
            key=lambda item: item.name))


@api.route('/courses/<int:course_id>/users/', methods=['PUT'])
def set_course_permission_user(course_id):
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
    """
    return jsonify([{
        'name': c.course.name,
        'id': c.course.id,
        'role': c.name
    } for c in current_user.courses.values()])

from flask import jsonify, request
from flask_login import current_user, login_required

import psef.auth as auth
import psef.models as models
from psef import db
from psef.errors import APICodes, APIException

from . import api


@api.route('/courses/<int:course_id>/roles/<int:role_id>', methods=['DELETE'])
def delete_role(course_id, role_id):
    auth.ensure_permission('can_manage_course', course_id)

    role = models.CourseRole.query.filter_by(
        course_id=course_id, id=role_id).first()
    if role is None:
        raise APIException(
            'The specified role was not found',
            'The fole with name "{role_id}" was not found'.format(role_id),
            APICodes.OBJECT_NOT_FOUND, 404)

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

    role.set_permission(perm, content['value'])

    db.session.commit()

    return '', 204


@api.route('/courses/<int:course_id>/roles/', methods=['GET'])
def get_all_course_roles(course_id):
    auth.ensure_permission('can_manage_course', course_id)

    courses = sorted(
        models.CourseRole.query.filter_by(course_id=course_id).all(),
        key=lambda item: item.name)
    if request.args.get('with_roles') == 'true':
        res = []
        for course in courses:
            json_course = course.__to_json__()
            json_course['perms'] = course.get_all_permissions()
            json_course['own'] = current_user.courses[course.course_id] == course
            res.append(json_course)
        courses = res
    return jsonify(courses)


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
    """
    return jsonify([{
        'name': c.course.name,
        'id': c.course.id,
        'role': c.name
    } for c in current_user.courses.values()])

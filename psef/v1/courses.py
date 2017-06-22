from flask import jsonify, request

import psef.auth as auth
import psef.models as models
from psef import db
from psef.errors import APICodes, APIException

from . import api


@api.route('/courses/<int:course_id>/assignments/', methods=['GET'])
def get_all_course_assignments(course_id):
    auth.ensure_permission('can_see_assignments', course_id)

    course = models.Course.query.get(course_id)
    if course is None:
        return APIException('Specified course not found',
                            'The course {} was not found'.format(course_id),
                            APICodes.OBJECT_ID_NOT_FOUND, 404)

    return jsonify(sorted(course.assignments, key=lambda item: item.deadline))

@api.route('/courses/', methods=['POST'])
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

    return jsonify(new_course.to_dict())

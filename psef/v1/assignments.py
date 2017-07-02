"""
This module defines all API routes with the main directory "assignments". Thus
the APIs in this module are mostly used to manipulate
:class:`.models.Assignment` objects and their relations.
"""

import os
import threading
from random import shuffle
from itertools import cycle

import dateutil
from flask import jsonify, request, send_file, after_this_request
from flask_login import current_user, login_required

import psef.auth as auth
import psef.files
import psef.models as models
import psef.linters as linters
from psef import db, app
from psef.errors import APICodes, APIException

from . import linters as linters_routes
from . import api


@api.route("/assignments/", methods=['GET'])
@login_required
def get_student_assignments():
    """Get all the :class:`.models.Assignment` objects that the current user can
    see.

    :returns: A response containing the JSON serialized assignments
    :rtype: flask.Response

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    perm_can_see = models.Permission.query.filter_by(
        name='can_see_assignments').first()
    perm_can_grade = models.Permission.query.filter_by(
        name='can_grade_work').first()
    courses = []

    for course_role in current_user.courses.values():
        if course_role.has_permission(perm_can_see):
            courses.append(course_role.course_id)

    res = []

    if courses:
        for assignment in models.Assignment.query.filter(
                models.Assignment.course_id.in_(courses)).all():
            if ((not assignment.is_hidden) or current_user.has_permission(
                    'can_see_hidden_assignments', assignment.course_id)):
                res.append(assignment)
    return jsonify(res)


@api.route("/assignments/<int:assignment_id>", methods=['GET'])
def get_assignment(assignment_id):
    """Return the given :class:`.models.Assignment`.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized assignment
    :rtype: flask.Response

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to view this
                                 assignment. (INCORRECT_PERMISSION)
    """
    assignment = models.Assignment.query.get(assignment_id)
    auth.ensure_permission('can_see_assignments', assignment.course_id)
    if assignment.is_hidden:
        auth.ensure_permission('can_see_hidden_assignments',
                               assignment.course_id)
    if assignment is None:
        raise APIException(
            'Assignment not found',
            'The assignment with id {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)
    else:
        return jsonify(assignment)


@api.route('/assignments/<int:assignment_id>', methods=['PATCH'])
def update_assignment(assignment_id):
    """Update the given :class:`.models.Assignment` with new values.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIException: If an invalid value is submitted. (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to edit this is
                                 assignment. (INCORRECT_PERMISSION)
    """
    assig = models.Assignment.query.get(assignment_id)
    if assig is None:
        raise APIException(
            'Assignment not found',
            'The assignment with id "{}" was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_manage_course', assig.course_id)

    content = request.get_json()

    if 'state' in content:
        if content['state'] not in ['hidden', 'open', 'done']:
            raise APIException(
                'The selected state is not valid',
                'The state {} is not a valid state'.format(content['state']),
                APICodes.INVALID_PARAM, 400)
        assig.set_state(content['state'])

    if 'name' in content:
        if not isinstance(content['name'], str):
            raise APIException(
                'The name of an assignment should be a a string',
                '{} is not a string'.format(content['name']),
                APICodes.INVALID_PARAM, 400)
        if len(content['name']) < 3:
            raise APIException(
                'The name of an assignment should be longer than 3',
                'len({}) < 3'.format(content['name']), APICodes.INVALID_PARAM,
                400)
        assig.name = content['name']

    if 'deadline' in content:
        try:
            assig.deadline = dateutil.parser.parse(content['deadline'])
        except ValueError:
            raise APIException(
                'The given deadline is not valid!',
                '{} cannot be parsed by dateutil'.format(content['deadline']),
                APICodes.INVALID_PARAM, 400)

    db.session.commit()

    return '', 204


@api.route('/assignments/<int:assignment_id>/rubrics/', methods=['GET'])
def get_assignment_rubric(assignment_id):
    """Return the rubric corresponding to the given `assignment_id`.

    :param int assignment_id: The id of the assignment
    :returns: A list of JSON of :class:`models.RubricRows` items
    :rtype: flask.Response

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIException: If the assignment has no rubric.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to see this is
                                 assignment. (INCORRECT_PERMISSION)
    """
    assig = models.Assignment.query.get(assignment_id)
    if assig is None:
        raise APIException(
            'Assignment not found',
            'The assignment with id "{}" was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_see_assignments', assig.course_id)
    if not assig.rubric_rows:
        raise APIException(
            'Assignment has no rubric',
            'The assignment with id "{}" has no rubric'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    return jsonify(assig.rubric_rows)


@api.route('/assignments/<int:assignment_id>/rubrics/', methods=['PUT'])
def add_assignment_rubric(assignment_id):
    """Add or update rubric of an assignment.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIException: If there is no `rows` (list) item in the provided
                          content. (INVALID_PARAM)
    :raises APIException: If a `row` does not contain `header`, `description`
                          or `items` (list).(INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to manage rubrics.
                                 (INCORRECT_PERMISSION)
    """
    assig = models.Assignment.query.get(assignment_id)
    if assig is None:
        raise APIException(
            'Assignment not found',
            'The assignment with id "{}" was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('manage_rubrics', assig.course_id)
    content = request.get_json()

    if 'rows' not in content or not isinstance(content['rows'], list):
        raise APIException('The rows are invalid',
                           'The rows provied are not valid',
                           APICodes.INVALID_PARAM, 400)

    for row in content['rows']:
        if ('header' not in row or 'description' not in row or
                'items' not in row or not isinstance(row['items'], list)):
            raise APIException('The provided row is invalid',
                               'The provided row "{}" is invalid'.format(row),
                               APICodes.INVALID_PARAM, 400)
        if 'id' in row:
            patch_rubric_row(assig, row)
        else:
            add_new_rubric_row(assig, row)

    db.session.commit()
    return ('', 204)


def add_new_rubric_row(assig, row):
    """Add new rubric row to the assignment.

    :param models.Assignment assig: The assignment to add the rubric row to
    :param dict row: The row from content containing items and row information
    :returns: None

    :raises APIException: If `description` or `points` fields are not in
                          `item`. (INVALID_PARAM)
    """
    rubric_row = models.RubricRow(
        assignment_id=assig.id,
        header=row['header'],
        description=row['description'])
    db.session.add(rubric_row)
    for item in row['items']:
        if 'description' not in item or 'points' not in item:
            raise APIException(
                'The provided item is invalid',
                'The provided item "{}" is invalid'.format(item),
                APICodes.INVALID_PARAM, 400)
        rubric_row.items.append(
            models.RubricItem(
                rubricrow_id=rubric_row.id,
                description=item['description'],
                points=item['points']))


def patch_rubric_row(assig, row):
    """Update a rubric row of the assignment.

    :param models.Assignment assig: The assignment to add the rubric row to
    :param dict row: The row from content containing items and row information
    :returns: None

    :raises APIException: If no rubric row with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIException: If `description` or `points` fields are not in
                          `item`. (INVALID_PARAM)
    :raises APIException: If no rubric item with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    """
    rubric_row = models.RubricRow.query.get(row['id'])
    if rubric_row is None:
        raise APIException(
            'Rubric row not found',
            'The Rubric row with id "{}" was not found'.format(row['id']),
            APICodes.OBJECT_ID_NOT_FOUND, 404)
    for item in row['items']:
        if 'description' not in item or 'points' not in item:
            raise APIException(
                'The provided item is invalid',
                'The provided item "{}" is invalid'.format(item),
                APICodes.INVALID_PARAM, 400)
        if 'id' not in item:
            rubric_row.items.append(
                models.RubricItem(
                    rubricrow_id=rubric_row.id,
                    description=item['description'],
                    points=item['points']))
        else:
            rubric_item = models.RubricItem.query.get(item['id'])
            if rubric_item is None:
                raise APIException(
                    'Rubric item not found',
                    'The Rubric item with id "{}" was not found'.format(item[
                        'id']), APICodes.OBJECT_ID_NOT_FOUND, 404)
            rubric_item.description = item['description']
            rubric_item.points = item['points']


@api.route(
    '/assignments/<int:assignment_id>/rubrics/<int:rubric_row>',
    methods=['DELETE'])
def delete_rubricrow(assignment_id, rubric_row):
    """Delete rubric row of the assignment.

    :param int assignment_id: The id of the assignment
    :param int rubric_row: The id of the rubric row
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: If no rubric row with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to manage rubrics.
                                 (INCORRECT_PERMISSION)
    """
    row = models.RubricRow.query.get(rubric_row)
    if row is None or row.assignment_id != assignment_id:
        raise APIException(
            'The requested rubric row was not found',
            'There is now rubric row for assignment {} with id {}'.format(
                assignment_id, rubric_row), APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('manage_rubrics', row.assignment.course_id)

    db.session.delete(row)
    db.session.commit()

    return '', 204


@api.route("/assignments/<int:assignment_id>/submission", methods=['POST'])
def upload_work(assignment_id):
    """Upload one or more files as :class:`.models.Work` to the given
    :class:`.models.Assignment`

    :param int assignment_id: The id of the assignment
    :returns: A the JSON serialized submission and return code 201.
    :rtype: (flask.Response, int)

    :raises APIException: If the request is bigger than the maximum upload
                          size. (REQUEST_TOO_LARGE)
    :raises APIException: If there was no file in the request.
                          (MISSING_REQUIRED_PARAM)
    :raises APIException: If some file was under the wrong key or some filename
                          is empty. (INVALID_PARAM)
    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to upload for this
                                 assignment. (INCORRECT_PERMISSION)
    """

    files = []

    if (request.content_length and
            request.content_length > app.config['MAX_UPLOAD_SIZE']):
        raise APIException('Uploaded files are too big.', (
            'Request is bigger than maximum ' + 'upload size of {}.'
        ).format(app.config['MAX_UPLOAD_SIZE']), APICodes.REQUEST_TOO_LARGE,
                           400)

    if len(request.files) == 0:
        raise APIException("No file in HTTP request.",
                           "There was no file in the HTTP request.",
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    for key, file in request.files.items():
        if not key.startswith('file'):
            raise APIException('The parameter name should start with "file".',
                               'Expected ^file.*$ got {}.'.format(key),
                               APICodes.INVALID_PARAM, 400)

        if file.filename == '':
            raise APIException('The filename should not be empty.',
                               'Got an empty filename for key {}'.format(key),
                               APICodes.INVALID_PARAM, 400)

        files.append(file)

    assignment = models.Assignment.query.get(assignment_id)
    if assignment is None:
        raise APIException(
            'Assignment not found',
            'The assignment with code {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_submit_own_work', assignment.course_id)
    if not assignment.is_open:
        auth.ensure_permission('can_upload_after_deadline',
                               assignment.course_id)

    work = models.Work(assignment_id=assignment_id, user_id=current_user.id)
    db.session.add(work)

    tree = psef.files.process_files(files)
    work.add_file_tree(db.session, tree)

    db.session.commit()

    return jsonify(work), 201


@api.route('/assignments/<int:assignment_id>/divide', methods=['PATCH'])
def divide_assignments(assignment_id):
    """Assign graders to all the latest :class:`.models.Work` objects of
    the given :class:`.models.Assignment`.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: If no assignment with given id exists or the
                          assignment has no submissions. (OBJECT_ID_NOT_FOUND)
    :raises APIException: If there was no grader in the request.
                          (MISSING_REQUIRED_PARAM)
    :raises APIException: If some grader id is invalid or some grader does not
                          have the permission to grade the assignment.
                          (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to divide
                                 submissions for this assignment.
                                 (INCORRECT_PERMISSION)
    """
    assignment = models.Assignment.query.get(assignment_id)
    auth.ensure_permission('can_manage_course', assignment.course_id)
    if not assignment:
        raise APIException(
            'Assignment not found',
            'The assignment with code {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    content = request.get_json()

    if 'graders' not in content or not isinstance(
            content['graders'], list) or len(content['graders']) == 0:
        raise APIException('List of assigned graders is required',
                           'List of assigned graders is required',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    submissions = assignment.get_all_latest_submissions()

    if not submissions:
        raise APIException(
            'No submissions found',
            'No submissions found for assignment {}'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    users = models.User.query.filter(models.User.id.in_(content[
        'graders'])).all()
    if len(users) != len(content['graders']):
        raise APIException('Invalid grader id given',
                           'Invalid grader (=user) id given',
                           APICodes.INVALID_PARAM, 400)

    for grader in users:
        if not grader.has_permission('can_grade_work', assignment.course_id):
            raise APIException('Selected grader has no permission to grade',
                               'Selected grader has no permission to grade',
                               APICodes.INVALID_PARAM, 400)

    shuffle(submissions)
    shuffle(content['graders'])
    for submission, grader in zip(submissions, cycle(content['graders'])):
        submission.assigned_to = grader

    db.session.commit()
    return ('', 204)


@api.route('/assignments/<int:assignment_id>/graders', methods=['GET'])
def get_all_graders(assignment_id):
    """Gets a list of all :class:`.models.User` objects who can grade the given
    :class:`.models.Assignment`.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized graders.
    :rtype: flask.Response

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to view graders of
                                 this assignment. (INCORRECT_PERMISSION)
    """
    assignment = models.Assignment.query.get(assignment_id)
    auth.ensure_permission('can_manage_course', assignment.course_id)

    if not assignment:
        raise APIException(
            'Assignment not found',
            'The assignment with code {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    permission = db.session.query(models.Permission.id).filter(
        models.Permission.name == 'can_grade_work').as_scalar()

    us = db.session.query(
        models.User.id, models.User.name, models.user_course.c.course_id).join(
            models.user_course,
            models.User.id == models.user_course.c.user_id).subquery('us')
    per = db.session.query(models.course_permissions.c.course_role_id).join(
        models.CourseRole, models.CourseRole.id ==
        models.course_permissions.c.course_role_id).filter(
            models.course_permissions.c.permission_id == permission,
            models.CourseRole.course_id ==
            assignment.course_id).subquery('per')
    result = db.session.query(us.c.name, us.c.id).join(
        per, us.c.course_id == per.c.course_role_id).order_by(us.c.name).all()

    divided = set(r[0]
                  for r in db.session.query(models.Work.assigned_to).filter(
                      models.Work.assignment_id == assignment_id).group_by(
                          models.Work.assigned_to).all())

    return jsonify([{
        'id': res[1],
        'name': res[0],
        'divided': res[1] in divided
    } for res in result])


@api.route('/assignments/<int:assignment_id>/submissions/', methods=['GET'])
def get_all_works_for_assignment(assignment_id):
    """Return all :class:`.models.Work` objects for the given
    :class:`.models.Assignment`.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized submissions.
    :rtype: flask.Response

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the assignment is hidden and the user is
                                 not allowed to view it. (INCORRECT_PERMISSION)
    """
    assignment = models.Assignment.query.get(assignment_id)
    if current_user.has_permission(
            'can_see_others_work', course_id=assignment.course_id):
        obj = models.Work.query.filter_by(assignment_id=assignment_id)
    else:
        obj = models.Work.query.filter_by(
            assignment_id=assignment_id, user_id=current_user.id)

    if assignment.is_hidden:
        auth.ensure_permission('can_see_hidden_assignments',
                               assignment.course_id)

    res = obj.order_by(models.Work.created_at.desc()).all()

    return jsonify(res)


@api.route("/assignments/<int:assignment_id>/submissions/", methods=['POST'])
def post_submissions(assignment_id):
    """Add submissions to the  given:class:`.models.Assignment` from a
    blackboard zip file as :class:`.models.Work` objects.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIException: If there was no file in the request.
                          (MISSING_REQUIRED_PARAM)
    :raises APIException: If the file parameter name is incorrect.
                          (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to manage the
                                 course attached to the assignment.
                                 (INCORRECT_PERMISSION)
    """
    assignment = models.Assignment.query.get(assignment_id)

    if not assignment:
        raise APIException(
            'Assignment not found',
            'The assignment with code {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)
    auth.ensure_permission('can_manage_course', assignment.course_id)

    if len(request.files) == 0:
        raise APIException("No file in HTTP request.",
                           "There was no file in the HTTP request.",
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    if 'file' not in request.files:
        key_string = ", ".join(request.files.keys())
        raise APIException('The parameter name should be "file".',
                           'Expected ^file$ got [{}].'.format(key_string),
                           APICodes.INVALID_PARAM, 400)

    file = request.files['file']
    try:
        submissions = psef.files.process_blackboard_zip(file)
    except:
        raise APIException("The blackboard zip could not imported.",
                           "The blackboard zip could not be parsed.",
                           APICodes.INVALID_PARAM, 400)
    try:
        for submission_info, submission_tree in submissions:
            user = models.User.query.filter_by(
                name=submission_info.student_name).first()

            if user is None:
                perms = {
                    assignment.course_id:
                    models.CourseRole.query.filter_by(
                        name='Student', course_id=assignment.course_id).first()
                }
                user = models.User(
                    name=submission_info.student_name,
                    courses=perms,
                    email=submission_info.student_name + '@example.com',
                    password='password',
                    role=models.Role.query.filter_by(name='Student').first())

                db.session.add(user)
            work = models.Work(
                assignment_id=assignment.id,
                user=user,
                created_at=submission_info.created_at,
                grade=submission_info.grade)
            db.session.add(work)
            work.add_file_tree(db.session, submission_tree)
    except:
        for _, tree in submissions:
            psef.files.remove_tree(tree)
        raise

    db.session.commit()

    return '', 204


@api.route('/assignments/<int:assignment_id>/linters/', methods=['GET'])
def get_linters(assignment_id):
    """Get all possible linters for the given :class:`.models.Assignment`.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized linters
    :rtype: flask.Response

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not user linters in this
                                 course. (INCORRECT_PERMISSION)
    """
    assignment = models.Assignment.query.get(assignment_id)

    if assignment is None:
        raise APIException(
            'The specified assignment could not be found',
            'Assignment {} does not exist'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_use_linter', assignment.course_id)

    res = []
    for name, opts in linters.get_all_linters().items():
        linter = models.AssignmentLinter.query.filter_by(
            assignment_id=assignment_id, name=name).first()

        if linter:
            running = db.session.query(
                models.LinterInstance.query.filter(
                    models.LinterInstance.tester_id == linter.id,
                    models.LinterInstance.state == models.LinterState.running)
                .exists()).scalar()
            crashed = db.session.query(
                models.LinterInstance.query.filter(
                    models.LinterInstance.tester_id == linter.id,
                    models.LinterInstance.state == models.LinterState.crashed)
                .exists()).scalar()
            if running:
                state = models.LinterState.running.name
            elif crashed:
                state = models.LinterState.crashed.name
            else:
                state = models.LinterState.done.name
            opts['id'] = linter.id
        else:
            state = 'new'
        opts['state'] = state
        opts['name'] = name
        res.append(opts)

    return jsonify(sorted(res, key=lambda item: item['name']))


@api.route('/assignments/<int:assignment_id>/linter', methods=['POST'])
def start_linting(assignment_id):
    """Starts running a specific linter on all the latest submissions
    (:class:`.models.Work`) of the given :class:`.models.Assignment`.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the serialized linter that is started by
              the request
    :rtype: flask.Response

    :raises APIException: If a required parameter is missing.
                          (MISSING_REQUIRED_PARAM)
    :raises APIException: If a linter of the same name is already running on
                          the assignment. (INVALID_STATE)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not user linters in this
                                 course. (INCORRECT_PERMISSION)
    """
    content = request.get_json()

    if not ('cfg' in content and 'name' in content):
        raise APIException('Missing required params.',
                           ('Missing one ore more of children, cfg'
                            ' or name in the payload "{}"').format(content),
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    if db.session.query(
            models.LinterInstance.query.filter(
                models.AssignmentLinter.assignment_id == assignment_id,
                models.AssignmentLinter.name == content['name'])
            .exists()).scalar():
        raise APIException(
            'There is still a linter instance running',
            'There is a linter named "{}" running for assignment {}'.format(
                content['name'], assignment_id), APICodes.INVALID_STATE, 409)

    perm = models.Assignment.query.get(assignment_id)
    auth.ensure_permission('can_use_linter', perm.course_id)
    res = models.AssignmentLinter.create_tester(assignment_id, content['name'])
    db.session.add(res)
    db.session.commit()

    try:
        runner = linters.LinterRunner(
            linters.get_linter_by_name(content['name']), content['cfg'])

        thread = threading.Thread(
            target=runner.run,
            args=([t.work_id for t in res.tests], [t.id for t in res.tests],
                  ('{}api/v1/linter' + '_comments/{}').format(request.url_root,
                                                              '{}')))

        thread.start()
    except:
        for test in res.tests:
            test.state = models.LinterState.crashed
        db.session.commit()
    finally:
        return linters_routes.get_linter_state(res.id)

"""
This module defines all API routes with the main directory "assignments". Thus
the APIs in this module are mostly used to manipulate
:class:`.models.Assignment` objects and their relations.

:license: AGPLv3, see LICENSE for details.
"""
import os
import typing as t
import numbers
import threading
from random import shuffle

import flask
import dateutil
import sqlalchemy.sql.expression as expression
from flask import request, send_file, after_this_request

import psef
import psef.auth as auth
import psef.files
import psef.models as models
import psef.helpers as helpers
import psef.linters as linters
from collections import defaultdict
from psef import db, app, current_user
from psef.errors import APICodes, APIException
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import linters as linters_routes
from . import api


@api.route("/assignments/", methods=['GET'])
@auth.login_required
def get_all_assignments() -> JSONResponse[t.Sequence[models.Assignment]]:
    """Get all the :class:`.models.Assignment` objects that the current user
    can see.

    .. :quickref: Assignment; Get all assignments.

    :returns: An array of :py:class:`Assignment` items encoded in JSON.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    perm_can_see: models.Permission = models.Permission.query.filter_by(
        name='can_see_assignments'
    ).first()
    courses = []

    for course_role in current_user.courses.values():
        if course_role.has_permission(perm_can_see):
            courses.append(course_role.course_id)

    res = []

    if courses:
        assignment: models.Assignment
        for assignment in models.Assignment.query.filter(
            models.Assignment.course_id.in_(courses)  # type: ignore
        ).all():
            has_perm = current_user.has_permission(
                'can_see_hidden_assignments', assignment.course_id
            )
            if ((not assignment.is_hidden) or has_perm):
                res.append(assignment)
    return jsonify(res)


@api.route("/assignments/<int:assignment_id>", methods=['GET'])
def get_assignment(assignment_id: int) -> JSONResponse[models.Assignment]:
    """Return the given :class:`.models.Assignment`.

    .. :quickref: Assignment; Get a single assignment by id.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized assignment

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to view this
                                 assignment. (INCORRECT_PERMISSION)
    """
    assignment = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('can_see_assignments', assignment.course_id)

    if assignment.is_hidden:
        auth.ensure_permission(
            'can_see_hidden_assignments', assignment.course_id
        )

    return jsonify(assignment)


@api.route("/assignments/<int:assignment_id>/feedbacks/", methods=['GET'])
@auth.login_required
def get_assignments_feedback(
    assignment_id: int
) -> JSONResponse[t.Mapping[str, t.Mapping[str, t.Union[t.Sequence[str], str]]]
                  ]:
    """Get all feedbacks for all latest submissions for a given assignment.

    .. :quickref: Assignment; Get feedback for all submissions in a assignment.

    :param int assignment_id: The assignment to query for.
    :returns: A mapping between the id of the submission and a object contain
        three keys: ``general`` for general feedback as a string, ``user`` for
        user feedback as a list of strings and ``linter`` for linter feedback
        as a list of strings. If a user cannot see others work only submissions
        by the current users are returned.
    """
    assignment = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_enrolled(assignment.course_id)

    latest_subs = assignment.get_all_latest_submissions()
    try:
        auth.ensure_permission('can_see_others_work', assignment.course_id)
    except auth.PermissionException:
        latest_subs = latest_subs.filter_by(user_id=current_user.id)

    res = {}
    for sub in latest_subs:
        try:
            # This call should be cached in auth.py
            auth.ensure_can_see_grade(sub)

            users, linters = sub.get_all_feedback()
            item = {
                'general': sub.comment or '',
                'user': list(users),
                'linter': list(linters),
            }
        except auth.PermissionException:
            item = {'user': [], 'linter': [], 'general': ''}

        res[str(sub.id)] = item

    return jsonify(res)


@api.route('/assignments/<int:assignment_id>', methods=['PATCH'])
def update_assignment(assignment_id: int) -> EmptyResponse:
    """Update the given :class:`.models.Assignment` with new values.

    :py:func:`psef.helpers.JSONResponse`

    .. :quickref: Assignment; Update assignment information.

    :<json str state: The new state of the assignment, can be `hidden`, `open`
        or `done`. (OPTIONAL)
    :<json str name: The new name of the assignment, this string should not be
        empty. (OPTIONAL)
    :<json str deadline: The new deadline of the assignment. This should be a
        ISO 8061 date without timezone information. (OPTIONAL)

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIException: If an invalid value is submitted. (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to edit this is
                                 assignment. (INCORRECT_PERMISSION)
    """
    assig = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('can_manage_course', assig.course_id)

    content = ensure_json_dict(request.get_json())

    if 'state' in content:
        ensure_keys_in_dict(content, [('state', str)])
        state = t.cast(str, content['state'])

        if state in ['hidden', 'open', 'done']:
            assig.set_state(state)
        else:
            raise APIException(
                'The selected state is not valid',
                'The state {} is not a valid state'.format(content['state']),
                APICodes.INVALID_PARAM, 400
            )

    if 'name' in content:
        ensure_keys_in_dict(content, [('name', str)])
        name = t.cast(str, content['name'])

        if not name:
            raise APIException(
                'The name of an assignment should be at least 1 char',
                'len({}) == 0'.format(content['name']),
                APICodes.INVALID_PARAM,
                400,
            )

        assig.name = name

    if 'deadline' in content:
        ensure_keys_in_dict(content, [('deadline', str)])
        deadline = t.cast(str, content['deadline'])

        try:
            assig.deadline = dateutil.parser.parse(deadline)
        except ValueError:
            raise APIException(
                'The given deadline is not valid!',
                '{} cannot be parsed by dateutil'.format(deadline),
                APICodes.INVALID_PARAM, 400
            )

    db.session.commit()

    return make_empty_response()


@api.route('/assignments/<int:assignment_id>/rubrics/', methods=['GET'])
@helpers.feature_required('RUBRICS')
def get_assignment_rubric(assignment_id: int
                          ) -> JSONResponse[t.Sequence[models.RubricRow]]:
    """Return the rubric corresponding to the given `assignment_id`.

    .. :quickref: Assignment; Get the rubric of an assignment.

    :param int assignment_id: The id of the assignment
    :returns: A list of JSON of :class:`models.RubricRows` items

    :raises APIException: If no assignment with given id exists.
        (OBJECT_ID_NOT_FOUND)
    :raises APIException: If the assignment has no rubric.
        (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to see this is
                                 assignment. (INCORRECT_PERMISSION)
    """
    assig = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('can_see_assignments', assig.course_id)
    if not assig.rubric_rows:
        raise APIException(
            'Assignment has no rubric',
            'The assignment with id "{}" has no rubric'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404
        )

    return jsonify(assig.rubric_rows)


@api.route('/assignments/<int:assignment_id>/rubrics/', methods=['DELETE'])
@helpers.feature_required('RUBRICS')
def delete_rubric(assignment_id: int) -> EmptyResponse:
    """Delete the rubric for the given assignment.

    .. :quickref: Assignment; Delete the rubric of an assignment.

    :param assignment_id: The id of the :class:`models.Assignment` whose rubric
        should be deleted.
    :returns: Nothing.

    :raises PermissionException: If the user does not have the
        ``manage_rubrics`` permission (INCORRECT_PERMISSION).
    :raises APIException: If the assignment has no rubric.
        (OBJECT_ID_NOT_FOUND)
    """
    assig = helpers.get_or_404(models.Assignment, assignment_id)
    auth.ensure_permission('manage_rubrics', assig.course_id)

    if not assig.rubric_rows:
        raise APIException(
            'Assignment has no rubric',
            'The assignment with id "{}" has no rubric'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404
        )

    assig.rubric_rows = []

    db.session.commit()

    return make_empty_response()


@api.route('/assignments/<int:assignment_id>/rubrics/', methods=['PUT'])
@helpers.feature_required('RUBRICS')
def add_assignment_rubric(assignment_id: int
                          ) -> JSONResponse[t.Sequence[models.RubricRow]]:
    """Add or update rubric of an assignment.

    .. :quickref: Assignment; Add a rubric to an assignment.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204

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
    assig = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('manage_rubrics', assig.course_id)
    content = ensure_json_dict(request.get_json())

    helpers.ensure_keys_in_dict(content, [('rows', list)])
    rows = t.cast(list, content['rows'])

    row: JSONType
    with db.session.begin_nested():
        seen = set()
        wrong_rows = []
        for row in rows:
            # Check for object of form:
            # {
            #   'description': str,
            #   'header': str,
            #   'items': list
            # }
            row = ensure_json_dict(row)
            ensure_keys_in_dict(
                row, [('description', str),
                      ('header', str),
                      ('items', list)]
            )
            header = t.cast(str, row['header'])
            description = t.cast(str, row['description'])
            items = t.cast(list, row['items'])

            if 'id' in row:
                seen.add(row['id'])
                n = patch_rubric_row(
                    assig, header, description, row['id'], items
                )
            else:
                n = add_new_rubric_row(assig, header, description, items)

            if n == 0:
                wrong_rows.append(header)

        if wrong_rows:
            single = len(wrong_rows) == 1
            raise APIException(
                'The row{s} {rows} do{es} not contain at least one item.'.
                format(
                    rows=', and '.join(wrong_rows),
                    s='' if single else 's',
                    es='es' if single else '',
                ), 'Not all rows contain at least one '
                'item after updating the rubric.', APICodes.INVALID_STATE, 400
            )

        assig.rubric_rows = list(
            filter(
                lambda row: row is None or row.id in seen,
                assig.rubric_rows,
            )
        )

        db.session.flush()
        max_points = assig.max_rubric_points

        if max_points is None or max_points <= 0:
            raise APIException(
                'The max amount of points you can '
                'score should be higher than 0',
                f'The max amount of points was {max_points} which is <= 0',
                APICodes.INVALID_STATE, 400
            )

    db.session.commit()
    return jsonify(assig.rubric_rows)


def add_new_rubric_row(
    assig: models.Assignment,
    header: str,
    description: str,
    items: t.Sequence[JSONType]
) -> int:
    """Add new rubric row to the assignment.

    :param assig: The assignment to add the rubric row to
    :param header: The name of the new rubric row.
    :param description: The description of the new rubric row.
    :param items: The items (:py:class:`models.RubricItem`) that should be
        added to the new rubric row, the JSONType should be a dictionary with
        the keys ``description`` (:py:class:`str`), ``header``
        (:py:class:`str`) and ``points`` (:py:class:`float`).
    :returns: The amount of items in this row.

    :raises APIException: If `description` or `points` fields are not in
        `item`. (INVALID_PARAM)
    """
    rubric_row = models.RubricRow(
        assignment_id=assig.id, header=header, description=description
    )
    for item in items:
        item = ensure_json_dict(item)
        ensure_keys_in_dict(
            item,
            [('description', str),
             ('header', str),
             ('points', numbers.Real)]
        )
        description = t.cast(str, item['description'])
        header = t.cast(str, item['header'])
        points = t.cast(numbers.Real, item['points'])
        rubric_item = models.RubricItem(
            rubricrow_id=rubric_row.id,
            header=header,
            description=description,
            points=points
        )
        db.session.add(rubric_item)
        rubric_row.items.append(rubric_item)
    db.session.add(rubric_row)

    return len(items)


def patch_rubric_row(
    assig: models.Assignment,
    header: str,
    description: str,
    rubric_row_id: t.Any,
    items: t.Sequence[JSONType]
) -> int:
    """Update a rubric row of the assignment.

    .. note::

      All items not present in the given ``items`` array will be deleted from
      the rubric row.

    :param models.Assignment assig: The assignment to add the rubric row to
    :param rubric_row_id: The id of the rubric row that should be updated.
    :param items: The items (:py:class:`models.RubricItem`) that should be
        added or updated. The format should be the same as in
        :py:func:`add_new_rubric_row` with the addition that if ``id`` is in
        the item the item will be updated instead of added.
    :returns: The amount of items in the resulting row.

    :raises APIException: If `description` or `points` fields are not in
        `item`. (INVALID_PARAM)
    :raises APIException: If no rubric item with given id exists.
        (OBJECT_ID_NOT_FOUND)
    """
    rubric_row = helpers.get_or_404(models.RubricRow, rubric_row_id)

    rubric_row.header = header
    rubric_row.description = description

    seen = set()

    for item in items:
        item = ensure_json_dict(item)
        ensure_keys_in_dict(
            item,
            [('description', str),
             ('points', numbers.Real),
             ('header', str)]
        )
        description = t.cast(str, item['description'])
        header = t.cast(str, item['header'])
        points = t.cast(numbers.Real, item['points'])

        if 'id' in item:
            seen.add(item['id'])
            rubric_item = helpers.get_or_404(models.RubricItem, item['id'])

            rubric_item.header = header
            rubric_item.description = description
            rubric_item.points = float(points)
        else:
            rubric_item = models.RubricItem(
                rubricrow_id=rubric_row.id,
                description=description,
                header=header,
                points=points
            )
            db.session.add(rubric_item)
            rubric_row.items.append(rubric_item)

    rubric_row.items = [
        item for item in rubric_row.items if item.id is None or item.id in seen
    ]

    return len(rubric_row.items)


@api.route("/assignments/<int:assignment_id>/submission", methods=['POST'])
def upload_work(assignment_id: int) -> JSONResponse[models.Work]:
    """Upload one or more files as :class:`.models.Work` to the given
    :class:`.models.Assignment`

    .. :quickref: Assignment; Create work by uploading a file.

    :param int assignment_id: The id of the assignment
    :returns: A JSON serialized work and with the status code 201.

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
        raise APIException(
            'Uploaded files are too big.', 'Request is bigger than maximum '
            f'upload size of {app.config["MAX_UPLOAD_SIZE"]}.',
            APICodes.REQUEST_TOO_LARGE, 400
        )

    if len(request.files) == 0:
        raise APIException(
            "No file in HTTP request.",
            "There was no file in the HTTP request.",
            APICodes.MISSING_REQUIRED_PARAM, 400
        )

    for key, file in request.files.items():
        if not key.startswith('file'):
            raise APIException(
                'The parameter name should start with "file".',
                'Expected ^file.*$ got {}.'.format(key),
                APICodes.INVALID_PARAM, 400
            )

        if not file.filename:
            raise APIException(
                'The filename should not be empty.',
                'Got an empty filename for key {}'.format(key),
                APICodes.INVALID_PARAM, 400
            )

        files.append(file)

    assignment = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('can_submit_own_work', assignment.course_id)
    if not assignment.is_open:
        auth.ensure_permission(
            'can_upload_after_deadline', assignment.course_id
        )

    work = models.Work(assignment=assignment, user_id=current_user.id)
    work.assigned_to = assignment.get_from_latest_submissions(  # type: ignore
        models.Work.assigned_to
    ).filter(models.Work.user_id == current_user.id).limit(1).scalar()
    if work.assigned_to is None:
        missing, _ = assignment.get_divided_amount_missing()
        if missing:
            work.assigned_to = max(missing.keys(), key=lambda k: missing[k])
    db.session.add(work)

    tree = psef.files.process_files(files)
    work.add_file_tree(db.session, tree)
    db.session.flush()

    if assignment.is_lti:
        work.passback_grade(initial=True)
    db.session.commit()

    work.run_linter()

    return jsonify(work, status_code=201)


@api.route('/assignments/<int:assignment_id>/divide', methods=['PATCH'])
def divide_assignments(assignment_id: int) -> EmptyResponse:
    """Assign graders to all the latest :class:`.models.Work` objects of
    the given :class:`.models.Assignment`.

    .. :quickref: Assignment; Divide a submission among given TA's.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204

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
    assignment = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('can_manage_course', assignment.course_id)

    content = ensure_json_dict(request.get_json())
    ensure_keys_in_dict(content, [('graders', dict)])
    graders = {}

    for user_id, weight in t.cast(dict, content['graders']).items():
        if not (isinstance(user_id, str) and isinstance(weight, (float, int))):
            raise APIException(
                'Given graders weight or id is invalid',
                'Both key and value in graders object should be integers',
                APICodes.INVALID_PARAM, 400
            )
        graders[int(user_id)] = weight

    if graders:
        users = helpers.filter_all_or_404(
            models.User,
            models.User.id.in_(graders.keys())  # type: ignore
        )
    else:
        models.Work.query.filter_by(assignment_id=assignment.id).update(
            {
                'assigned_to': None
            }
        )
        assignment.assigned_graders = {}
        db.session.commit()
        return make_empty_response()

    if len(users) != len(graders):
        raise APIException(
            'Invalid grader id given', 'Invalid grader (=user) id given',
            APICodes.INVALID_PARAM, 400
        )

    can_grade_work = helpers.filter_single_or_404(
        models.Permission, models.Permission.name == 'can_grade_work'
    )
    for user in users:
        if not user.has_permission(can_grade_work, assignment.course_id):
            raise APIException(
                'Selected grader has no permission to grade',
                f'The grader {user.id} has no permission to grade',
                APICodes.INVALID_PARAM, 400
            )

    assignment.divide_submissions([(user, graders[user.id]) for user in users])
    db.session.commit()

    return make_empty_response()


@api.route('/assignments/<int:assignment_id>/graders/', methods=['GET'])
def get_all_graders(
    assignment_id: int
) -> JSONResponse[t.Sequence[t.Mapping[str, t.Union[float, str, bool]]]]:
    """Gets a list of all :class:`.models.User` objects who can grade the given
    :class:`.models.Assignment`.

    .. :quickref: Assignment; Get all graders for an assignment.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized graders.

    :>jsonarr string name: The name of the grader.
    :>jsonarr int id: The user id of this grader.
    :>jsonarr bool divided: Is this user assigned to any submission for this
        assignment.

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to view graders of
                                 this assignment. (INCORRECT_PERMISSION)
    """
    assignment = helpers.get_or_404(models.Assignment, assignment_id)
    auth.ensure_permission('can_manage_course', assignment.course_id)

    permission = db.session.query(models.Permission.id).filter(
        models.Permission.name == 'can_grade_work'
    ).as_scalar()

    us = db.session.query(
        models.User.id, models.User.name, models.user_course.c.course_id
    ).join(models.user_course,
           models.User.id == models.user_course.c.user_id).subquery('us')
    per = db.session.query(models.course_permissions.c.course_role_id).join(
        models.CourseRole,
        models.CourseRole.id == models.course_permissions.c.course_role_id
    ).filter(
        models.course_permissions.c.permission_id == permission,
        models.CourseRole.course_id == assignment.course_id
    ).subquery('per')

    result: t.Sequence[t.Tuple[str, int]] = db.session.query(
        us.c.name, us.c.id
    ).join(per, us.c.course_id == per.c.course_role_id
           ).order_by(expression.func.lower(us.c.name)).all()

    divided: t.MutableMapping[int, float] = defaultdict(lambda: 0)
    for u in models.AssignmentAssignedGrader.query.filter_by(
        assignment_id=assignment_id
    ):
        divided[u.user_id] = u.weight

    return jsonify(
        [
            {
                'id': res[1],
                'name': res[0],
                'weight': divided[res[1]],
            } for res in result
        ]
    )


@api.route('/assignments/<int:assignment_id>/submissions/', methods=['GET'])
def get_all_works_for_assignment(assignment_id: int
                                 ) -> JSONResponse[t.Sequence[models.Work]]:
    """Return all :class:`.models.Work` objects for the given
    :class:`.models.Assignment`.

    .. :quickref: Assignment; Get all works for an assignment.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized submissions.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the assignment is hidden and the user is
                                 not allowed to view it. (INCORRECT_PERMISSION)
    """
    assignment = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('can_see_assignments', assignment.course_id)

    if assignment.is_hidden:
        auth.ensure_permission(
            'can_see_hidden_assignments', assignment.course_id
        )

    obj = models.Work.query.filter_by(assignment_id=assignment_id)
    if not current_user.has_permission(
        'can_see_others_work', course_id=assignment.course_id
    ):
        obj = obj.filter_by(user_id=current_user.id)

    res: t.Sequence[models.Work] = (
        obj.order_by(models.Work.created_at.desc()).all()  # type: ignore
    )

    return jsonify(res)


@api.route("/assignments/<int:assignment_id>/submissions/", methods=['POST'])
@helpers.feature_required('BLACKBOARD_ZIP_UPLOAD')
def post_submissions(assignment_id: int) -> EmptyResponse:
    """Add submissions to the  given:class:`.models.Assignment` from a
    blackboard zip file as :class:`.models.Work` objects.

    .. :quickref: Assignment; Create works from a blackboard zip.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204

    .. todo:: Merge this endpoint and ``upload_work`` together.

    :raises APIException: If no assignment with given id exists.
        (OBJECT_ID_NOT_FOUND)
    :raises APIException: If there was no file in the request.
        (MISSING_REQUIRED_PARAM)
    :raises APIException: If the file parameter name is incorrect or if the
        given file does not contain any valid submissions. (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to manage the
        course attached to the assignment. (INCORRECT_PERMISSION)
    """
    assignment = helpers.get_or_404(models.Assignment, assignment_id)
    auth.ensure_permission('can_manage_course', assignment.course_id)

    if len(request.files) == 0:
        raise APIException(
            "No file in HTTP request.",
            "There was no file in the HTTP request.",
            APICodes.MISSING_REQUIRED_PARAM, 400
        )

    if 'file' not in request.files:
        key_string = ", ".join(request.files.keys())
        raise APIException(
            'The parameter name should be "file".',
            'Expected ^file$ got [{}].'.format(key_string),
            APICodes.INVALID_PARAM, 400
        )

    file: 'FileStorage' = request.files['file']
    try:
        submissions = psef.files.process_blackboard_zip(file)
    except:
        submissions = []
    if not submissions:
        raise APIException(
            "The blackboard zip could not imported or it was empty.",
            'The blackboard zip could not'
            ' be parsed or it did not contain any valid submissions.',
            APICodes.INVALID_PARAM, 400
        )

    missing, recalc_missing = assignment.get_divided_amount_missing()
    sub_lookup = {}
    for sub in assignment.get_all_latest_submissions():
        sub_lookup[sub.user_id] = sub

    for submission_info, submission_tree in submissions:
        user = models.User.query.filter_by(
            username=submission_info.student_id
        ).first()

        if user is None:
            # TODO: Check if this role still exists
            perms = {
                assignment.course_id:
                    models.CourseRole.query.filter_by(
                        name='Student', course_id=assignment.course_id
                    ).first()
            }
            user = models.User(
                name=submission_info.student_name,
                username=submission_info.student_id,
                courses=perms,
                email='',
                password=submission_info.student_id,
                role=models.Role.query.filter_by(name='Student').first()
            )

            db.session.add(user)
        work = models.Work(
            assignment_id=assignment.id,
            user=user,
            created_at=submission_info.created_at,
        )

        db.session.add(work)

        if user.id is not None and user.id in sub_lookup:
            work.assigned_to = sub_lookup[user.id].assigned_to
        if work.assigned_to is None:
            if missing:
                work.assigned_to = max(
                    missing.keys(), key=lambda k: missing[k]
                )
                missing = recalc_missing(work.assigned_to)
                sub_lookup[user.id] = work

        db.session.flush()
        work.set_grade(submission_info.grade, current_user)
        work.add_file_tree(db.session, submission_tree)

    db.session.commit()

    return make_empty_response()


@api.route('/assignments/<int:assignment_id>/linters/', methods=['GET'])
def get_linters(assignment_id: int
                ) -> JSONResponse[t.Sequence[t.Mapping[str, t.Any]]]:
    """Get all linters for the given :class:`.models.Assignment`.

    .. :quickref: Assignment; Get all linters for a assignment.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized linters which is sorted
        by the name of the linter.
    :rtype: flask.Response

    :>jsonarr str state: The state of the linter, which can be ``new``, or any
        state from :py:class:`models.LinterState`.
    :>jsonarr str name: The name of this linter.
    :>jsonarr str id: The id of the linter, this will only be present when
        ``state`` is not ``new``.
    :>jsonarr ``*rest``: All items as described in
        :py:func:`linters.get_all_linters`

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not user linters in this
                                 course. (INCORRECT_PERMISSION)
    """
    assignment = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('can_use_linter', assignment.course_id)

    res = []
    for name, opts in linters.get_all_linters().items():
        linter = models.AssignmentLinter.query.filter_by(
            assignment_id=assignment_id, name=name
        ).first()

        if linter:
            running = db.session.query(
                models.LinterInstance.query.filter(
                    models.LinterInstance.tester_id == linter.id,
                    models.LinterInstance.state == models.LinterState.running
                ).exists()
            ).scalar()
            crashed = db.session.query(
                models.LinterInstance.query.filter(
                    models.LinterInstance.tester_id == linter.id,
                    models.LinterInstance.state == models.LinterState.crashed
                ).exists()
            ).scalar()
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
def start_linting(assignment_id: int) -> JSONResponse[models.AssignmentLinter]:
    """Starts running a specific linter on all the latest submissions
    (:class:`.models.Work`) of the given :class:`.models.Assignment`.

    .. :quickref: Assignment; Start linting an assignment with a given linter.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the serialized linter that is started by
              the request

    :raises APIException: If a required parameter is missing.
                          (MISSING_REQUIRED_PARAM)
    :raises APIException: If a linter of the same name is already running on
                          the assignment. (INVALID_STATE)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not user linters in this
                                 course. (INCORRECT_PERMISSION)
    """
    content = ensure_json_dict(request.get_json())

    assig = helpers.get_or_404(models.Assignment, assignment_id)
    auth.ensure_permission('can_use_linter', assig.course_id)

    ensure_keys_in_dict(content, [('cfg', str), ('name', str)])
    cfg = t.cast(str, content['cfg'])
    name = t.cast(str, content['name'])

    if db.session.query(
        models.LinterInstance.query.filter(
            models.AssignmentLinter.assignment_id == assignment_id,
            models.AssignmentLinter.name == content['name']
        ).exists()
    ).scalar():
        raise APIException(
            'There is still a linter instance running',
            'There is a linter named "{}" running for assignment {}'.format(
                content['name'], assignment_id
            ), APICodes.INVALID_STATE, 409
        )

    res = models.AssignmentLinter.create_linter(assignment_id, name, cfg)

    db.session.add(res)
    db.session.commit()

    try:
        linter_cls = linters.get_linter_by_name(name)
    except:
        raise APIException(
            f'No linter named "{name}" was found',
            (
                f'There is no subclass of the "Linter"'
                f'class with the name "{name}"'
            ),
            APICodes.OBJECT_NOT_FOUND,
            404,
        )
    if linter_cls.RUN_LINTER:
        try:
            runner = linters.LinterRunner(linter_cls, cfg)
            thread = threading.Thread(
                target=runner.run,
                args=([t.id for t in res.tests], ),
            )

            thread.start()
        except:  # pragma: no cover
            # This code only runs in the case of bug in the `LinterRunner`
            # class.
            for test in res.tests:
                test.state = models.LinterState.crashed
            db.session.commit()
    else:
        for linter_inst in res.tests:
            linter_inst.state = models.LinterState.done
        db.session.commit()

    return jsonify(res)


if t.TYPE_CHECKING:  # pragma: no cover
    from werkzeug.datastructures import FileStorage  # noqa

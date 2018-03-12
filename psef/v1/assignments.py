"""
This module defines all API routes with the main directory "assignments". Thus
the APIs in this module are mostly used to manipulate
:class:`.models.Assignment` objects and their relations.

:license: AGPLv3, see LICENSE for details.
"""
import os
import typing as t
import numbers
import datetime
import threading
from random import shuffle
from collections import defaultdict

import flask
import dateutil
import sqlalchemy.sql as sql
from flask import request, send_file, after_this_request
from sqlalchemy.orm import undefer, joinedload
from werkzeug.datastructures import FileStorage

import psef
import psef.auth as auth
import psef.files
import psef.models as models
import psef.helpers as helpers
import psef.linters as linters
import psef.parsers as parsers
from psef import app, current_user
from psef.errors import APICodes, APIWarnings, APIException, make_warning
from psef.ignore import IgnoreFilterManager
from psef.models import db
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, ExtendedJSONResponse, jsonify,
    ensure_json_dict, extended_jsonify, ensure_keys_in_dict,
    make_empty_response
)

from . import linters as linters_routes
from . import api


@api.route('/assignments/', methods=['GET'])
@auth.login_required
def get_all_assignments() -> JSONResponse[t.Sequence[models.Assignment]]:
    """Get all the :class:`.models.Assignment` objects that the current user
    can see.

    .. :quickref: Assignment; Get all assignments.

    :returns: An array of :py:class:`.models.Assignment` items encoded in JSON.

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
        for assignment, has_linter in db.session.query(
            models.Assignment,
            t.cast(models.DbColumn[str],
                   models.AssignmentLinter.id).isnot(None)
        ).filter(
            t.cast(
                models.DbColumn[int],
                models.Assignment.course_id,
            ).in_(courses)
        ).join(
            models.AssignmentLinter,
            sql.expression.and_(
                models.Assignment.id == models.AssignmentLinter.assignment_id,
                models.AssignmentLinter.name == 'MixedWhitespace'
            ),
            isouter=True
        ).all():
            has_perm = current_user.has_permission(
                'can_see_hidden_assignments', assignment.course_id
            )
            assignment.whitespace_linter_exists = has_linter
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


def set_reminder(
    assig: models.Assignment,
    content: t.Dict[str, helpers.JSONType],
) -> t.Optional[psef.errors.HttpWarning]:
    """Set the reminder of an assignment from a JSON dict.

    :param assig: The assignment to set the reminder for.
    :param content: The json input.
    :returns: A warning if it should be returned to the user.
    """
    ensure_keys_in_dict(content, [
        ('done_type', (type(None), str)),
        ('done_email', (type(None), str)),
        ('reminder_time', (type(None), str)),
    ])  # yapf: disable

    done_type = parsers.parse_enum(
        content.get('done_type', None),
        models.AssignmentDoneType,
        allow_none=True,
        option_name='done type'
    )
    reminder_time = parsers.parse_datetime(
        content.get('reminder_time', None),
        allow_none=True,
    )
    done_email = parsers.try_parse_email_list(
        content.get('done_email', None),
        allow_none=True,
    )

    if reminder_time and (reminder_time -
                          datetime.datetime.utcnow()).total_seconds() < 60:
        raise APIException(
            (
                'The given date is not far enough from the current time, '
                'it should be at least 60 seconds in the future.'
            ), f'{reminder_time} is not atleast 60 seconds in the future',
            APICodes.INVALID_PARAM, 400
        )

    assig.change_notifications(done_type, reminder_time, done_email)
    if done_email is not None and assig.graders_are_done():
        return make_warning(
            'Grading is already done, no email will be sent!',
            APIWarnings.CONDITION_ALREADY_MET
        )

    return None


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
    :<json str done_type: The type to determine if a assignment is done. This
        can be any value of :class:`.models.AssignmentDoneType` or
        ``null``. (OPTIONAL)
    :<json str done_email: The emails to send an email to if the assignment is
        done. Can be ``null`` to disable these emails. (OPTIONAL)
    :<json str reminder_time: The time on which graders which are causing the
        grading to be not should be reminded they have to grade. Can be
        ``null`` to disable these emails. (OPTIONAL)

    If any of ``done_type``, ``done_email`` or ``reminder_time`` is given all
    the other values should be given too.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204
    :raises APIException: If an invalid value is submitted. (INVALID_PARAM)
    """
    warning = None
    assig = helpers.get_or_404(models.Assignment, assignment_id)
    content = ensure_json_dict(request.get_json())

    if 'state' in content:
        auth.ensure_permission('can_edit_assignment_info', assig.course_id)
        ensure_keys_in_dict(content, [('state', str)])
        state = t.cast(str, content['state'])

        try:
            assig.set_state(state)
        except TypeError:
            raise APIException(
                'The selected state is not valid',
                'The state {} is not a valid state'.format(state),
                APICodes.INVALID_PARAM, 400
            )

    if 'name' in content:
        auth.ensure_permission('can_edit_assignment_info', assig.course_id)
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
        auth.ensure_permission('can_edit_assignment_info', assig.course_id)
        ensure_keys_in_dict(content, [('deadline', str)])
        deadline = t.cast(str, content['deadline'])
        assig.deadline = parsers.parse_datetime(deadline)

    if 'ignore' in content:
        auth.ensure_permission('can_edit_cgignore', assig.course_id)
        ensure_keys_in_dict(content, [('ignore', str)])
        assig.cgignore = t.cast(str, content['ignore'])

    if any(t in content for t in ['done_type', 'reminder_time', 'done_email']):
        auth.ensure_permission(
            'can_update_course_notifications',
            assig.course_id,
        )
        warning = set_reminder(assig, content) or warning

    db.session.commit()

    return make_empty_response(warning=warning)


@api.route('/assignments/<int:assignment_id>/rubrics/', methods=['GET'])
@helpers.feature_required('RUBRICS')
def get_assignment_rubric(assignment_id: int
                          ) -> JSONResponse[t.Sequence[models.RubricRow]]:
    """Return the rubric corresponding to the given `assignment_id`.

    .. :quickref: Assignment; Get the rubric of an assignment.

    :param int assignment_id: The id of the assignment
    :returns: A list of JSON of :class:`.models.RubricRows` items

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

    :param assignment_id: The id of the :class:`.models.Assignment` whose
        rubric should be deleted.
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

    :>json array rows: An array of rows. Each row should be an object that
        should contain a ``header`` mapping to a string, a ``description`` key
        mapping to a string, an ``items`` key mapping to an array and it may
        contain an ``id`` key mapping to the current id of this row. The items
        array should contain objects with a ``description`` (string),
        ``header`` (string) and ``points`` (number) and optionally an ``id`` if
        you are modifying an existing item in an existing row.
    :>json number max_points: Optionally override the maximum amount of points
        you can get for this rubric. By passing ``null`` you reset this value,
        by not passing it you keep its current value. (OPTIONAL)

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to manage rubrics.
                                (INCORRECT_PERMISSION)
    """
    assig = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('manage_rubrics', assig.course_id)
    content = ensure_json_dict(request.get_json())

    if 'max_points' in content:
        helpers.ensure_keys_in_dict(
            content, [('max_points',
                       (type(None), int, float))]
        )
        max_points = t.cast(t.Optional[float], content['max_points'])
        if max_points is not None and max_points <= 0:
            raise APIException(
                'The max amount of points you can '
                'score should be higher than 0',
                f'The max amount of points was {max_points} which is <= 0',
                APICodes.INVALID_STATE, 400
            )
        assig.fixed_max_rubric_points = max_points

    if 'rows' in content:
        with db.session.begin_nested():
            helpers.ensure_keys_in_dict(content, [('rows', list)])
            rows = t.cast(list, content['rows'])

            id_wrong = [process_rubric_row(assig, row) for row in rows]
            seen = set(
                item_id for item_id, _ in id_wrong if item_id is not None
            )
            wrong_rows = set(err for _, err in id_wrong if err is not None)

            if wrong_rows:
                single = len(wrong_rows) == 1
                raise APIException(
                    'The row{s} {rows} do{es} not contain at least one item.'.
                    format(
                        rows=', and '.join(wrong_rows),
                        s='' if single else 's',
                        es='es' if single else '',
                    ), 'Not all rows contain at least one '
                    'item after updating the rubric.', APICodes.INVALID_STATE,
                    400
                )

            assig.rubric_rows = [
                row for row in assig.rubric_rows
                if row is None or row.id in seen
            ]

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


def process_rubric_row(
    assig: models.Assignment,
    row: JSONType,
) -> t.Tuple[t.Optional[int], t.Optional[str]]:
    """Process a single rubric row updating or adding it.

    This function works on the input json data. It makes sure that the input
    has the correct format and dispatches it to the necessary functions.

    :param assig: The assignment this rubric row should be added to.
    :returns: A tuple with as the first element the id of the rubric row that
        has been processed (this is ``None`` for a new row) and as second item
        a string that describes were an error occurred if such an error did
        occur.
    """
    row = ensure_json_dict(row)
    ensure_keys_in_dict(
        row, [('description', str),
              ('header', str),
              ('items', list)]
    )
    header = t.cast(str, row['header'])
    description = t.cast(str, row['description'])
    items = t.cast(list, row['items'])
    row_id = None

    if 'id' in row:
        ensure_keys_in_dict(row, [('id', int)])
        row_id = t.cast(int, row['id'])
        n = patch_rubric_row(assig, header, description, row_id, items)
    else:
        n = add_new_rubric_row(assig, header, description, items)

    err = header if n == 0 else None  # No items were added which is wrong
    return row_id, err


def add_new_rubric_row(
    assig: models.Assignment, header: str, description: str,
    items: t.Sequence[JSONType]
) -> int:
    """Add new rubric row to the assignment.

    :param assig: The assignment to add the rubric row to
    :param header: The name of the new rubric row.
    :param description: The description of the new rubric row.
    :param items: The items (:py:class:`.models.RubricItem`) that should be
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
    assig: models.Assignment, header: str, description: str,
    rubric_row_id: int, items: t.Sequence[JSONType]
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


def get_submission_files_from_request(
    check_size: bool,
) -> t.MutableSequence[FileStorage]:
    """Get all the submitted files in the current request.

    This function also checks if the files are in the correct format and are
    lot too large.

    :returns: The files in the current request. The length of this list is
        always at least one.
    :raises APIException: When a given files is not correct.
    """
    res = []

    if (
        check_size and
        request.content_length and
        request.content_length > app.config['MAX_UPLOAD_SIZE']
    ):
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

        res.append(file)

    return res


@api.route("/assignments/<int:assignment_id>/submission", methods=['POST'])
def upload_work(assignment_id: int) -> JSONResponse[models.Work]:
    """Upload one or more files as :class:`.models.Work` to the given
    :class:`.models.Assignment`.

    .. :quickref: Assignment; Create work by uploading a file.

    An extra get parameter ``ignored_files`` can be given to determine how to
    handle ignored files. The options are:

    - ``ignore``, this the default, sipmly do nothing about ignored files.
    - ``delete``, delete the ignored files.
    - ``error``, raise an :py:class:`.APIException` when there are ignored
      files in the archive.

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
    files = get_submission_files_from_request(check_size=True)
    assignment = helpers.get_or_404(models.Assignment, assignment_id)

    auth.ensure_permission('can_submit_own_work', assignment.course_id)
    if not assignment.is_open:
        auth.ensure_permission(
            'can_upload_after_deadline', assignment.course_id
        )

    work = models.Work(assignment=assignment, user_id=current_user.id)
    work.assigned_to = assignment.get_from_latest_submissions(
        models.Work.assigned_to
    ).filter(models.Work.user_id == current_user.id).limit(1).scalar()

    if work.assigned_to is None:
        missing, _ = assignment.get_divided_amount_missing()
        if missing:
            work.assigned_to = max(missing.keys(), key=lambda k: missing[k])
            assignment.set_graders_to_not_done(
                [work.assigned_to],
                send_mail=True,
                ignore_errors=True,
            )

    db.session.add(work)

    raise_or_delete = psef.files.IgnoreHandling.keep
    if request.args.get('ignored_files') == 'delete':
        raise_or_delete = psef.files.IgnoreHandling.delete
    if request.args.get('ignored_files') == 'error':
        raise_or_delete = psef.files.IgnoreHandling.error

    ignoretxt = assignment.cgignore or ''

    tree = psef.files.process_files(
        files,
        force_txt=False,
        ignore_filter=IgnoreFilterManager(ignoretxt.split('\n')),
        handle_ignore=raise_or_delete,
    )
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

    The redivide tries to minimize shuffles. This means that calling it twice
    with the same data is effectively a noop. If the relative weight (so the
    percentage of work) of a user doesn't change it will not lose or gain any
    submissions.

    .. warning::

        If a user was marked as done grading and gets assigned new submissions
        this user is marked as not done and gets a notification email!

    :<json dict graders: A mapping that maps user ids (strings) and the new
        weight they should get (numbers).
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

    auth.ensure_permission('can_assign_graders', assignment.course_id)

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
    :>jsonarr bool done: Is this user done grading?

    :raises APIException: If no assignment with given id exists.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not allowed to view graders of
                                 this assignment. (INCORRECT_PERMISSION)
    """
    assignment = helpers.get_or_404(models.Assignment, assignment_id)
    auth.ensure_permission('can_see_assignee', assignment.course_id)

    result = assignment.get_all_graders(sort=True)

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
                'weight': float(divided[res[1]]),
                'done': res[2],
            } for res in result
        ]
    )


@api.route(
    '/assignments/<int:assignment_id>/graders/<int:grader_id>/done',
    methods=['DELETE']
)
@auth.login_required
def set_grader_to_not_done(
    assignment_id: int, grader_id: int
) -> EmptyResponse:
    """Indicate that the given grader is not yet done grading the given
    `:class:.models.Assignment`.

    .. :quickref: Assignment; Set the grader status to 'not done'.

    :param assignment_id: The id of the assignment the grader is not yet done
        grading.
    :param grader_id: The id of the `:class:.models.User` that is not yet done
        grading.
    :returns: An empty response with return code 204

    :raises APIException: If the given grader was not indicated as done before
        calling this endpoint. (INVALID_STATE)
    :raises PermissionException: If the current user wants to change a status
        of somebody else but the user does not have the
        `can_update_grader_status` permission. (INCORRECT_PERMISSION)
    :raises PermissionException: If the current user wants to change its own
        status but does not have the `can_update_grader_status` or the
        `can_grade_work` permission. (INCORRECT_PERMISSION)
    """
    assig = helpers.get_or_404(models.Assignment, assignment_id)

    if current_user.id == grader_id:
        auth.ensure_permission('can_grade_work', assig.course_id)
    else:
        auth.ensure_permission('can_update_grader_status', assig.course_id)

    try:
        send_mail = grader_id != current_user.id
        assig.set_graders_to_not_done([grader_id], send_mail=send_mail)
        db.session.commit()
    except ValueError:
        raise APIException(
            'The grader is not finished!',
            f'The grader {grader_id} is not done.',
            APICodes.INVALID_STATE,
            400,
        )
    else:
        return make_empty_response()


@api.route(
    '/assignments/<int:assignment_id>/graders/<int:grader_id>/done',
    methods=['POST']
)
@auth.login_required
def set_grader_to_done(assignment_id: int, grader_id: int) -> EmptyResponse:
    """Indicate that the given grader is done grading the given
    `:class:.models.Assignment`.

    .. :quickref: Assignment; Set the grader status to 'done'.

    :param assignment_id: The id of the assignment the grader is done grading.
    :param grader_id: The id of the `:class:.models.User` that is done grading.
    :returns: An empty response with return code 204

    :raises APIException: If the given grader was indicated as done before
        calling this endpoint. (INVALID_STATE)
    :raises PermissionException: If the current user wants to change a status
        of somebody else but the user does not have the
        `can_update_grader_status` permission. (INCORRECT_PERMISSION)
    :raises PermissionException: If the current user wants to change its own
        status but does not have the `can_update_grader_status` or the
        `can_grade_work` permission. (INCORRECT_PERMISSION)
    """
    assig = helpers.get_or_404(
        models.Assignment,
        assignment_id,
        options=[joinedload(models.Assignment.finished_graders)],
    )

    if current_user.id == grader_id:
        auth.ensure_permission('can_grade_work', assig.course_id)
    else:
        auth.ensure_permission('can_update_grader_status', assig.course_id)

    grader = helpers.get_or_404(models.User, grader_id)
    if not grader.has_permission('can_grade_work', assig.course_id):
        raise APIException(
            'The given user is not a grader in this course',
            (
                f'The user with id "{grader_id}" is not a grader '
                f'in the course "{assig.course_id}"'
            ),
            APICodes.INVALID_PARAM,
            400,
        )

    if any(g.user_id == grader_id for g in assig.finished_graders):
        raise APIException(
            'The grader is already finished!',
            f'The grader {grader_id} is already done.',
            APICodes.INVALID_STATE,
            400,
        )
    done_before = assig.graders_are_done()

    grader_done = models.AssignmentGraderDone(
        user_id=grader_id,
        assignment=assig,
    )
    db.session.add(grader_done)
    db.session.commit()

    if not done_before and assig.graders_are_done():
        psef.tasks.send_done_mail(assig.id)

    if assig.has_non_graded_submissions(grader_id):
        return make_empty_response(
            make_warning(
                'You have non graded work!',
                APIWarnings.GRADER_NOT_DONE,
            )
        )

    return make_empty_response()


WorkList = t.Sequence[models.Work]


@api.route('/assignments/<int:assignment_id>/submissions/', methods=['GET'])
def get_all_works_for_assignment(
    assignment_id: int
) -> t.Union[JSONResponse[WorkList], ExtendedJSONResponse[WorkList]]:
    """Return all :class:`.models.Work` objects for the given
    :class:`.models.Assignment`.

    .. :quickref: Assignment; Get all works for an assignment.

    :qparam boolean extended: Whether to get extended or normal
        :class:`.models.Work` objects. The default value is ``false``, you can
        enable extended by passing ``true``, ``1`` or an empty string.

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

    obj = models.Work.query.filter_by(
        assignment_id=assignment_id,
    ).options(joinedload(
        models.Work.selected_items,
    )).order_by(t.cast(t.Any, models.Work.created_at).desc())

    if not current_user.has_permission(
        'can_see_others_work', course_id=assignment.course_id
    ):
        obj = obj.filter_by(user_id=current_user.id)

    extended = request.args.get('extended', 'false').lower()

    if extended in {'true', '1', ''}:
        obj = obj.options(undefer(models.Work.comment))
        return extended_jsonify(
            obj.all(),
            use_extended=lambda obj: isinstance(obj, models.Work),
        )
    else:
        return jsonify(obj.all())


@api.route("/assignments/<int:assignment_id>/submissions/", methods=['POST'])
@helpers.feature_required('BLACKBOARD_ZIP_UPLOAD')
def post_submissions(assignment_id: int) -> EmptyResponse:
    """Add submissions to the  given:class:`.models.Assignment` from a
    blackboard zip file as :class:`.models.Work` objects.

    .. :quickref: Assignment; Create works from a blackboard zip.

    You should upload a file as multiform post request. The key should start
    with 'file'. Multiple blackboard zips are not supported and result in one
    zip being chosen at (psuedo) random.

    :param int assignment_id: The id of the assignment
    :returns: An empty response with return code 204

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
    auth.ensure_permission('can_upload_bb_zip', assignment.course_id)
    files = get_submission_files_from_request(check_size=False)

    try:
        submissions = psef.files.process_blackboard_zip(files[0])
    except Exception:
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

    student_course_role = models.CourseRole.query.filter_by(
        name='Student', course_id=assignment.course_id
    ).first()
    global_role = models.Role.query.filter_by(name='Student').first()

    subs = []
    hists = []

    found_users = {
        u.username: u
        for u in models.User.query.filter(
            t.cast(
                models.DbColumn[str],
                models.User.username,
            ).in_([si.student_id for si, _ in submissions])
        ).options(joinedload(models.User.courses))
    }

    newly_assigned: t.Set[t.Optional[int]] = set()

    for submission_info, submission_tree in submissions:
        user = found_users.get(submission_info.student_id, None)

        if user is None:
            # TODO: Check if this role still exists
            user = models.User(
                name=submission_info.student_name,
                username=submission_info.student_id,
                courses={assignment.course_id: student_course_role},
                email='',
                password=None,
                role=global_role,
            )
            found_users[user.username] = user
            # We don't need to track the users to insert as we are already
            # tracking the submissions of them and they are coupled.
        else:
            user.courses[assignment.course_id] = student_course_role

        work = models.Work(
            assignment=assignment,
            user=user,
            created_at=submission_info.created_at,
        )
        subs.append(work)

        if user.id is not None and user.id in sub_lookup:
            work.assigned_to = sub_lookup[user.id].assigned_to

        if work.assigned_to is None:
            if missing:
                work.assigned_to = max(
                    missing.keys(), key=lambda k: missing[k]
                )
                missing = recalc_missing(work.assigned_to)
                sub_lookup[user.id] = work

        hists.append(
            work.set_grade(
                submission_info.grade, current_user, add_to_session=False
            )
        )
        work.add_file_tree(db.session, submission_tree)
        if work.assigned_to is not None:
            newly_assigned.add(work.assigned_to)

    assignment.set_graders_to_not_done(
        list(newly_assigned),
        send_mail=True,
        ignore_errors=True,
    )

    db.session.bulk_save_objects(subs)
    db.session.flush()

    for h in hists:
        h.work_id = h.work.id
        h.user_id = h.user.id

    db.session.bulk_save_objects(hists)
    db.session.commit()

    return make_empty_response()


@api.route('/assignments/<int:assignment_id>/linters/', methods=['GET'])
@helpers.feature_required('LINTERS')
def get_linters(assignment_id: int
                ) -> JSONResponse[t.Sequence[t.Mapping[str, t.Any]]]:
    """Get all linters for the given :class:`.models.Assignment`.

    .. :quickref: Assignment; Get all linters for a assignment.

    :param int assignment_id: The id of the assignment
    :returns: A response containing the JSON serialized linters which is sorted
        by the name of the linter.
    :rtype: flask.Response

    :>jsonarr str state: The state of the linter, which can be ``new``, or any
        state from :py:class:`.models.LinterState`.
    :>jsonarr str name: The name of this linter.
    :>jsonarr str id: The id of the linter, this will only be present when
        ``state`` is not ``new``.
    :>jsonarr ``*rest``: All items as described in
        :py:func:`.linters.get_all_linters`

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
@helpers.feature_required('LINTERS')
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
    except ValueError:
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
        for i in range(0, len(res.tests), 10):
            psef.tasks.lint_instances(
                name,
                cfg,
                [t.id for t in res.tests[i:i + 10]],
            )
    else:
        for linter_inst in res.tests:
            linter_inst.state = models.LinterState.done
        db.session.commit()

    return jsonify(res)


if t.TYPE_CHECKING:  # pragma: no cover
    from werkzeug.datastructures import FileStorage  # noqa

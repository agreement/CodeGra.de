"""
This module defines all API routes with the main directory "submissions". The
APIs allow the retrieving, and patching of :class: Work objects. Furthermore
functions are defined to get related objects and information.
"""

import os
import typing as t
import numbers
import zipfile
import tempfile

from flask import request, send_file, make_response, after_this_request

import psef.auth as auth
import psef.files
import psef.models as models
import psef.helpers as helpers
from psef import db, current_user
from psef.errors import APICodes, APIException
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api

if t.TYPE_CHECKING:  # pragma: no cover
    import werkzeug


@api.route("/submissions/<int:submission_id>", methods=['GET'])
@auth.login_required
def get_submission(
    submission_id: int
) -> JSONResponse[t.Union[models.Work, t.Mapping[str, str]]]:
    """Get the given submission (:class:`.models.Work`).

    .. :quickref: Submission; Get a single submission.

    This API has some options based on the 'type' argument in the request

    - If ``type == 'zip'`` see :py:func:`get_zip`
    - If ``type == 'feedback'`` see :py:func:`get_feedback`

    :param int submission_id: The id of the submission
    :returns: A response with the JSON serialized submission as content unless
              specified otherwise
    :rtype: flask.Response

    :raises APIException: If the submission with given id does not exist.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the submission does not belong to the
                                 current user and the user can not see others
                                 work in the attached course.
                                 (INCORRECT_PERMISSION)
    """
    work = helpers.get_or_404(models.Work, submission_id)

    if work.user_id != current_user.id:
        auth.ensure_permission(
            'can_see_others_work', work.assignment.course_id
        )

    if request.args.get('type') == 'zip':
        return jsonify(get_zip(work))
    elif request.args.get('type') == 'feedback':
        auth.ensure_can_see_grade(work)
        return jsonify(get_feedback(work))
    return jsonify(work)


def get_feedback(work: models.Work) -> t.Mapping[str, str]:
    """Get the feedback of :class:`.models.Work` as a plain text file.

    :param work: The submission with the required feedback.
    :returns: A response with the plain text feedback as attached file.
    """
    comments: t.Sequence[models.Comment] = models.Comment.query.filter(
        models.Comment.file.has(work=work)).order_by(  # type: ignore
            models.Comment.file_id.asc(),  # type: ignore
            models.Comment.line.asc())  # type: ignore

    linter_comments: t.Sequence[models.LinterComment]
    linter_comments = models.LinterComment.query.filter(
        models.LinterComment.file.has(  # type: ignore
            work=work)).order_by(  # type: ignore
                models.LinterComment.file_id.asc(),  # type: ignore
                models.LinterComment.line.asc())  # type: ignore

    filename = f'{work.assignment.name}-{work.user.name}-feedback.txt'

    path, name = psef.files.random_file_path('MIRROR_UPLOAD_DIR')

    with open(path, 'w') as fp:
        fp.write(
            'Assignment: {}\n'
            'Grade: {}\n'
            'General feedback:\n{}\n\n'
            'Comments:\n'.format(
                work.assignment.name, work.grade or '', work.comment or ''
            )
        )
        for comment in comments:
            fp.write(
                '{}:{}:0: {}\n'.format(
                    comment.file.get_filename(), comment.line, comment.comment
                )
            )
        fp.write('\nLinter comments:\n')

        for lcomment in linter_comments:
            fp.write(
                '{}:{}:0: ({} {}) {}\n'.format(
                    lcomment.file.get_filename(), lcomment.line, lcomment.
                    linter.tester.name, lcomment.linter_code, lcomment.comment
                )
            )

    return {'name': name, 'output_name': filename}


def get_zip(work: models.Work) -> t.Mapping[str, str]:
    """Return a :class:`.models.Work` as a zip file.

    :param work: The submission which should be returns as zip file.
    :returns: A response with the zip as attached file.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If submission does not belong to the current
                                 user and the user can not view files in the
                                 attached course. (INCORRECT_PERMISSION)
    """
    if (work.user_id != current_user.id):
        auth.ensure_permission('can_view_files', work.assignment.course_id)

    code = helpers.filter_single_or_404(
        models.File,
        models.File.work_id == work.id,
        models.File.parent_id == None,  # NOQA
    )

    path, name = psef.files.random_file_path('MIRROR_UPLOAD_DIR')

    with open(path, 'w+b') as fp:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Restore the files to tmpdir
            psef.files.restore_directory_structure(code, tmpdir)

            zipf = zipfile.ZipFile(fp, 'w', compression=zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    path = os.path.join(root, file)
                    zipf.write(path, path[len(tmpdir):])
            zipf.close()
        fp.flush()

    return {
        'name': name,
        'output_name': f'{work.assignment.name}-{work.user.name}-archive.zip'
    }


@api.route("/submissions/<int:submission_id>/rubrics/", methods=['GET'])
def get_rubric(submission_id: int) -> JSONResponse[t.Mapping[str, t.Any]]:
    """Return full rubric of the :class:`.models.Assignment` of the given
    submission (:class:`.models.Work`).

    .. :quickref: Submission; Get a rubric and its selected items.

    :param int submission_id: The id of the submission
    :returns: A response containing the JSON serialized rubric as described in
        :py:meth:`.Work.__rubric_to_json__`.

    :raises APIException: If the submission with the given id does not exist.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not see the assignment of the
                                 given submission. (INCORRECT_PERMISSION)
    """
    work = helpers.get_or_404(models.Work, submission_id)
    auth.ensure_permission('can_see_assignments', work.assignment.course_id)
    return jsonify(work.__rubric_to_json__())


@api.route(
    "/submissions/<int:submission_id>/rubricitems/<int:rubricitem_id>",
    methods=['PATCH']
)
def select_rubric_item(submission_id: int, rubricitem_id: int
                       ) -> JSONResponse[t.Mapping[str, t.Any]]:
    """Select a rubric item of the given submission (:class:`.models.Work`).

    .. :quickref: Submission; Select a rubric item.

    :param int submission_id: The id of the submission
    :param int rubricitem_id: The id of the rubric item
    :returns: A response containing the JSON serialized rubric and a status
        code of 201. The rubric is serialized as described in
        :py:meth:`.Work.__rubric_to_json__()`.

    :raises APIException: If either the submission or rubric item with the
                          given ids does not exist. (OBJECT_ID_NOT_FOUND)
    :raises APIException: If the assignment of the rubric is not the assignment
                          of the submission. (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not grade the given submission
                                 (INCORRECT_PERMISSION)
    """
    work = helpers.get_or_404(models.Work, submission_id)
    rubric_item = helpers.get_or_404(models.RubricItem, rubricitem_id)

    auth.ensure_permission('can_grade_work', work.assignment.course_id)
    if rubric_item.rubricrow.assignment_id != work.assignment_id:
        raise APIException(
            'Rubric item selected does not match assignment',
            'The rubric item with id {} does not match the assignment'.
            format(rubricitem_id), APICodes.INVALID_PARAM, 400
        )

    work.remove_selected_rubric_item(rubric_item.rubricrow_id)
    work.select_rubric_item(rubric_item)
    db.session.commit()

    return jsonify(work.__rubric_to_json__(), status_code=201)


@api.route("/submissions/<int:submission_id>", methods=['PATCH'])
def patch_submission(submission_id: int) -> EmptyResponse:
    """Update the given submission (:class:`.models.Work`) if it already
    exists.

    .. :quickref: Submission; Update a submissions grade and feedback.

    :param int submission_id: The id of the submission
    :returns: Empty response with return code 204

    :raise APIException: If the submission with the given id does not exist
        (OBJECT_ID_NOT_FOUND)
    :raise APIException: If the request does not contain the parameters "grade"
        and/or "feedback" (MISSING_REQUIRED_PARAM)
    :raise APIException: If the value of the "grade" parameter is not a float
        (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If user can not grade the submission with the
        given id (INCORRECT_PERMISSION)
    """
    work = helpers.get_or_404(models.Work, submission_id)
    work = db.session.query(models.Work).get(submission_id)
    content = ensure_json_dict(request.get_json())

    auth.ensure_permission('can_grade_work', work.assignment.course_id)

    ensure_keys_in_dict(
        content, [('grade', numbers.Rational),
                  ('feedback', str)]
    )
    feedback = t.cast(str, content['feedback'])
    grade = float(t.cast(numbers.Rational, content['grade']))

    if not 0 <= grade <= 10:
        raise APIException(
            'Grade submitted not between 0 and 10',
            'Grade for work with id {} is {} which is not between 0 and 10'.
            format(submission_id,
                   content['grade']), APICodes.INVALID_PARAM, 400
        )

    work.grade = grade
    work.comment = feedback
    db.session.commit()
    return make_empty_response()


@api.route("/submissions/<int:submission_id>/files/", methods=['GET'])
@auth.login_required
def get_dir_contents(submission_id: int) -> JSONResponse[psef.files.FileTree]:
    """Return the file directory info of a file of the given submission
    (:class:`.models.Work`).

    .. :quickref: Submission; Get the directory contents for a submission.

    The default file is the root of the submission, but a specific file can be
    specified with the file_id argument in the request.

    :param int submission_id: The id of the submission
    :returns: A response with the JSON serialized directory structure as
        content and return code 200. For the exact structure see
        :py:meth:`.File.list_contents`.

    :query int file_id: The file id of the directory to get. If this is not
        given the parent directory for the specified submission is used.

    :raise APIException: If the submission with the given id does not exist or
                         when a file id was specified no file with this id
                         exists. (OBJECT_ID_NOT_FOUND)
    :raises APIException: wWhen a file id is specified and the submission id
                          does not match the submission id of the file.
                          (INVALID_URL)
    :raises APIException: When a file id is specified and the file with that id
                          is not a directory. (OBJECT_WRONG_TYPE)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If submission does not belong to the current
                                 user and the user can not view files in the
                                 attached course. (INCORRECT_PERMISSION)
    """
    work = helpers.get_or_404(models.Work, submission_id)

    if (work.user_id != current_user.id):
        auth.ensure_permission('can_view_files', work.assignment.course_id)

    file_id = request.args.get('file_id')

    if file_id:
        file = helpers.filter_single_or_404(
            models.File,
            models.File.id == file_id,
            models.File.work_id == work.id,
        )
    else:
        file = helpers.filter_single_or_404(
            models.File,
            models.File.work_id == submission_id,
            models.File.parent_id == None  # NOQA
        )

    if not file.is_directory:
        raise APIException(
            'File is not a directory',
            f'The file with code {file.id} is not a directory',
            APICodes.OBJECT_WRONG_TYPE, 400
        )

    return jsonify(file.list_contents())

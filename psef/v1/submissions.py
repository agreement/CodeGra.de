"""
This module defines all API routes with the main directory "submissions". The
APIs allow the retrieving, and patching of :class: Work objects. Furthermore
functions are defined to get related objects and information.
"""

import os
import zipfile
import tempfile

from flask import jsonify, request, send_file, make_response, after_this_request
from flask_login import current_user, login_required

import psef.auth as auth
import psef.files
import psef.models as models
from psef import db
from psef.errors import APICodes, APIException

from . import api


@api.route("/submissions/<int:submission_id>", methods=['GET'])
@login_required
def get_submission(submission_id):
    """Get the given submission (:class:`models.Work`).

    This API has some options based on the 'type' argument in the request
    - If type == 'zip' see :py:func:`get_zip`
    - If type == 'feedback' see :py:func:`get_feedback`

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

    # check if feedback is visible

    work = db.session.query(models.Work).get(submission_id)

    if work.user_id != current_user.id:
        auth.ensure_permission('can_see_others_work',
                               work.assignment.course_id)

    if work is None:
        raise APIException(
            'Work submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    if request.args.get('type') == 'zip':
        return get_zip(work)

    if request.args.get('type') == 'feedback':
        if work.assignment.state != models._AssignmentStateEnum.done:
            raise APIException(
                'Feedback not visible',
                'The assignment state was not set to done',
                APICodes.INVALID_STATE, 405)
        return get_feedback(work)

    return jsonify(work)


@api.route("/submissions/<int:submission_id>/rubrics/", methods=['GET'])
def get_rubric(submission_id):
    """Return full rubric of the :class:`models.Assignment` of the given
    submission (:class:`models.Work`).

    :param int submission_id: The id of the submission
    :returns: A response containing the JSON serialized rubric
    :rtype: flask.Response

    :raises APIException: If the submission with the given id does not exist.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not see the assignment of the
                                 given submission. (INCORRECT_PERMISSION)
    """
    work = models.Work.query.get(submission_id)
    if work is None:
        raise APIException(
            'Work submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_see_assignments', work.assignment.course_id)

    try:
        auth.ensure_can_see_grade(work)

        return jsonify({
            'rubrics': work.assignment.rubric_rows,
            'selected': work.selected_items,
            'points': {
                'max': work.assignment.max_rubric_points,
                'selected': work.selected_rubric_points,
            },
        })
    except auth.PermissionException:
        return jsonify({
            'rubrics': work.assignment.rubric_rows,
        })


@api.route(
    "/submissions/<int:submission_id>/rubricitems/<int:rubricitem_id>",
    methods=['PATCH'])
def select_rubric_item(submission_id, rubricitem_id):
    """Select a rubric item of the given submission (:class:`models.Work`).

    :param int submission_id: The id of the submission
    :param int rubricitem_id: The id of the rubric item
    :returns: A response containing the JSON serialized rubric
    :rtype: flask.Response

    :raises APIException: If either the submission or rubric item with the
                          given ids does not exist. (OBJECT_ID_NOT_FOUND)
    :raises APIException: If the assignment of the rubric is not the assignment
                          of the submission. (INVALID_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not grade the given submission
                                 (INCORRECT_PERMISSION)
    """
    work = models.Work.query.get(submission_id)
    if work is None:
        raise APIException(
            'Work submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    rubric_item = models.RubricItem.query.get(rubricitem_id)
    if rubric_item is None:
        raise APIException(
            'Rubric item not found',
            'The rubric item with id {} was not found'.format(rubricitem_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_grade_work', work.assignment.course_id)
    if rubric_item.rubricrow.assignment_id != work.assignment_id:
        raise APIException(
            'Rubric item selected does not match assignment',
            'The rubric item with id {} does not match the assignment'.format(
                rubricitem_id), APICodes.INVALID_PARAM, 400)

    work.remove_selected_rubric_item(rubric_item.rubricrow_id)
    work.select_rubric_item(rubric_item)
    db.session.commit()

    return jsonify({
        'selected': work.selected_rubric_points,
        'max': work.assignment.max_rubric_points,
        'grade': work.grade,
    }), 201


def get_feedback(work):
    """Get the feedback of :class:`models.Work` as a plain text file.

    :param models.Work work: The submission with the required feedback
    :returns: A response with the plain text feedback as attached file
    :rtype: flask.Response
    """
    comments = models.Comment.query.filter(
        models.Comment.file.has(work=work)).order_by(
            models.Comment.file_id.asc(), models.Comment.line.asc())

    linter_comments = models.LinterComment.query.filter(
        models.LinterComment.file.has(work=work)).order_by(
            models.LinterComment.file_id.asc(),
            models.LinterComment.line.asc())

    filename = '{}-{}-feedback.txt'.format(work.assignment.name,
                                           work.user.name)

    fd, file = tempfile.mkstemp()
    with open(file, 'w') as fp:
        fp.write('Assignment: {}\n'
                 'Grade: {}\n'
                 'General feedback: \n{}\n\n'
                 'Comments:\n'.format(work.assignment.name, work.grade,
                                      work.comment))
        for comment in comments:
            fp.write('{}:{}:0: {}\n'.format(comment.file.get_filename(),
                                            comment.line, comment.comment))
        fp.write('\nLinter comments:\n')

        for lcomment in linter_comments:
            fp.write('{}:{}:0: ({} {}) {}\n'.format(
                lcomment.file.get_filename(), lcomment.line, lcomment.linter.
                tester.name, lcomment.linter_code, lcomment.comment))

    @after_this_request
    def remove_file(response):
        os.close(fd)
        os.remove(file)
        return response

    return send_file(file, attachment_filename=filename, as_attachment=True)


def get_zip(work):
    """Return a :class:`models.Work` as a zip file.

    :param models.Work work: The submission which should be returns as zip file
    :returns: A response with the zip as attached file
    :rtype: flask.Response

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If submission does not belong to the current
                                 user and the user can not view files in the
                                 attached course. (INCORRECT_PERMISSION)
    """
    if (work.user_id != current_user.id):
        auth.ensure_permission('can_view_files', work.assignment.course_id)

    code = models.File.query.filter(models.File.work_id == work.id,
                                    models.File.parent_id == None).one()

    with tempfile.TemporaryFile(mode='w+b') as fp:
        with tempfile.TemporaryDirectory() as tmpdir:
            files = psef.files.restore_directory_structure(code, tmpdir)

            zipf = zipfile.ZipFile(fp, 'w', compression=zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(tmpdir):
                for file in files:
                    path = os.path.join(root, file)
                    zipf.write(path, path[len(tmpdir):])
            zipf.close()
        fp.seek(0)

        response = make_response(fp.read())
        response.headers['Content-Type'] = 'application/zip'
        filename = '{}-{}-archive.zip'.format(work.assignment.name,
                                              work.user.name)
        response.headers[
            'Content-Disposition'] = 'attachment; filename=' + filename
        return response


@api.route("/submissions/<int:submission_id>", methods=['PATCH'])
def patch_submission(submission_id):
    """Update the given submission (:class:`models.Work`) if it already exists.

    :param int submission_id: The id of the submission
    :returns: Empty response with return code 204
    :rtype: (str, int)

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
    work = db.session.query(models.Work).get(submission_id)
    content = request.get_json()

    if not work:
        raise APIException(
            'Submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_grade_work', work.assignment.course_id)
    if 'grade' not in content or 'feedback' not in content:
        raise APIException('Grade or feedback not provided',
                           'Grade and or feedback fields missing in sent JSON',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    if not isinstance(content['grade'], float):
        try:
            content['grade'] = float(content['grade'])
        except ValueError:
            raise APIException(
                'Grade submitted not a number',
                'Grade for work with id {} not a number'.format(submission_id),
                APICodes.INVALID_PARAM, 400)

    if content['grade'] < 0 or content['grade'] > 10:
        raise APIException(
            'Grade submitted not between 0 and 10',
            'Grade for work with id {} is {} which is not between 0 and 10'.
            format(submission_id,
                   content['grade']), APICodes.INVALID_PARAM, 400)

    work.grade = content['grade']
    work.comment = content['feedback']
    db.session.commit()
    return '', 204


@api.route("/submissions/<int:submission_id>/files/", methods=['GET'])
def get_dir_contents(submission_id):
    """Return the file directory info of a file of the given submission
    (:class:`models.Work`).

    The default file is the root of the submission, but a specific file can be
    specified with the file_id argument in the request.

    :param int submission_id: The id of the submission
    :returns: A response with the JSON serialized directory structure as
              content and return code 200
    :rtype: (flask.Response, int)

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
    work = models.Work.query.get(submission_id)
    if work is None:
        raise APIException(
            'Submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    if (work.user_id != current_user.id):
        auth.ensure_permission('can_view_files', work.assignment.course_id)

    file_id = request.args.get('file_id')
    if file_id:
        file = models.File.query.get(file_id)
        if file is None:
            raise APIException(
                'File not found',
                'The file with code {} was not found'.format(file_id),
                APICodes.OBJECT_ID_NOT_FOUND, 404)
        if (file.work_id != submission_id):
            raise APIException(
                'Incorrect URL',
                'The identifiers in the URL do no match those related to the '
                'file with code {}'.format(file.id), APICodes.INVALID_URL, 400)
    else:
        file = models.File.query.filter(models.File.work_id == submission_id,
                                        models.File.parent_id == None).one()

    if not file.is_directory:
        raise APIException(
            'File is not a directory',
            'The file with code {} is not a directory'.format(file.id),
            APICodes.OBJECT_WRONG_TYPE, 400)

    dir_contents = jsonify(file.list_contents())

    return dir_contents, 200

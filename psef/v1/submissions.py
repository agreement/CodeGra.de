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
    """
    Return submission X if the user permission is valid.

    Raises APIException:
        - If submission X was not found
    """
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
        return get_feedback(work)

    return jsonify(work)


@api.route("/submissions/<int:submission_id>/rubrics/", methods=['GET'])
def get_rubric(submission_id):
    """
    Return full rubric of assignment X.
    """
    work = models.Work.query.get(submission_id)
    if work is None:
        raise APIException(
            'Work submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    return jsonify({
        'rubrics': work.assignment.get_rubric(),
        'selected': work.get_selected_rubric_items()
    })


@api.route(
    "/submissions/<int:submission_id>/rubricitems/<int:rubricitem_id>",
    methods=['PATCH'])
def select_rubric_item(submission_id, rubricitem_id):
    """
    Select given rubric item of submission X.
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

    auth.ensure_permission('can_grade_work', work.assignment.course.id)
    if rubric_item.rubricrow.assignment_id != work.assignment_id:
        raise APIException(
            'Rubric item selected does not match assignment',
            'The rubric item with id {} does not match the assignment'.format(
                rubricitem_id), APICodes.INVALID_PARAM, 400)

    work.remove_selected_rubric_item(rubric_item.rubricrow_id)
    work.select_rubric_item(rubric_item)
    db.session.commit()

    return ('', 204)


def get_feedback(work):
    """
    Get the feedback of work as a plain text file.
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
    """
    Return a zip file of a submission.

    Raises APIException:
        - If the submission is None.
    """
    if (work.user.id != current_user.id):
        auth.ensure_permission('can_view_files', work.assignment.course.id)

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
    """
    Update submission X if it already exists and if the user permission is
    valid.

    Raises APIException:
        - If submission X was not found
        - request file does not contain grade and/or feedback
        - request file grade is not a float
    """
    work = db.session.query(models.Work).get(submission_id)
    content = request.get_json()

    if not work:
        raise APIException(
            'Submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_grade_work', work.assignment.course.id)
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

    work.grade = content['grade']
    work.comment = content['feedback']
    db.session.commit()
    return '', 204


@api.route("/submissions/<int:submission_id>/files/", methods=['GET'])
def get_dir_contents(submission_id):
    """
    Return the object containing all the files of submission X

    Raises APIException:
        - If there are no files to be returned
        - If the submission id does not match the work id
        - If the file with code {} is not a directory
    """
    work = models.Work.query.get(submission_id)
    if work is None:
        raise APIException(
            'Submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    if (work.user.id != current_user.id):
        auth.ensure_permission('can_view_files', work.assignment.course.id)

    file_id = request.args.get('file_id')
    if file_id:
        file = models.File.query.get(file_id)
        if file is None:
            raise APIException(
                'File not found',
                'The file with code {} was not found'.format(file_id),
                APICodes.OBJECT_ID_NOT_FOUND, 404)
        if (file.work.id != submission_id):
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

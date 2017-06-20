from flask import jsonify, request, make_response
from flask_login import current_user

import psef.auth as auth
import psef.models as models
import psef.files
from psef import db
from psef.errors import APICodes, APIException
from . import api


@api.route("/file/metadata/<int:file_id>", methods=['GET'])
def get_file_metadata(file_id):
    file = db.session.query(models.File).filter(
        models.File.id == file_id).first()

    return jsonify({"name": file.name, "extension": file.extension})


@api.route("/binary/<int:file_id>")
def get_binary(file_id):
    file = db.session.query(models.File).filter(
        models.File.id == file_id).first()

    file_data = psef.files.get_binary_contents(file)
    response = make_response(file_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=' + file.name

    return response


@api.route("/code/<int:file_id>", methods=['GET'])
def get_code(file_id):
    code = db.session.query(models.File).get(file_id)
    line_feedback = {}
    linter_feedback = {}

    if code is None:
        raise APIException('File not found',
                           'The file with id {} was not found'.format(file_id),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)

    if (code.work.user.id != current_user.id):
        auth.ensure_permission('can_view_files',
                               code.work.assignment.course.id)

    try:
        auth.ensure_can_see_grade(code.work)
        for comment in db.session.query(models.Comment).filter_by(
                file_id=file_id).all():
            line_feedback[str(comment.line)] = comment.comment
        for comment in db.session.query(models.LinterComment).filter_by(
                file_id=file_id).all():
            if str(comment.line) not in linter_feedback:
                linter_feedback[str(comment.line)] = {}
            linter_feedback[str(comment.line)][comment.linter.tester.name] = {
                'code': comment.linter_code,
                'msg': comment.comment
            }
    except auth.PermissionException:
        line_feedback = {}
        linter_feedback = {}

    return jsonify(
        lang=code.extension,
        code=psef.files.get_file_contents(code),
        feedback=line_feedback,
        linter_feedback=linter_feedback)


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

    return (dir_contents, 200)

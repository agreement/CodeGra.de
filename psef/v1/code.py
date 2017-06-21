from flask import jsonify, request, make_response
from flask_login import current_user, login_required

import psef.auth as auth
import psef.files
import psef.models as models
from psef import db
from psef.errors import APICodes, APIException

from . import api


@api.route("/code/<int:id>/comments/<int:line>", methods=['PUT'])
def put_comment(id, line):
    """
    Create or change a single line comment of a code file
    """
    content = request.get_json()

    comment = db.session.query(models.Comment).filter(
        models.Comment.file_id == id,
        models.Comment.line == line).one_or_none()

    if not comment:
        file = db.session.query(models.File).get(id)
        auth.ensure_permission('can_grade_work',
                               file.work.assignment.course.id)
        db.session.add(
            models.Comment(
                file_id=id,
                user_id=current_user.id,
                line=line,
                comment=content['comment']))
    else:
        auth.ensure_permission('can_grade_work',
                               comment.file.work.assignment.course.id)
        comment.comment = content['comment']

    db.session.commit()

    return ('', 204)


@api.route("/code/<int:id>/comments/<int:line>", methods=['DELETE'])
def remove_comment(id, line):
    """
    Removes the comment on line X if the request is valid.

    Raises APIException:
        - If no comment on line X was found
    """
    comment = db.session.query(models.Comment).filter(
        models.Comment.file_id == id,
        models.Comment.line == line).one_or_none()

    if comment:
        auth.ensure_permission('can_grade_work',
                               comment.file.work.assignment.course.id)
        db.session.delete(comment)
        db.session.commit()
    else:
        raise APIException('Feedback comment not found',
                           'The comment on line {} was not found'.format(line),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)
    return ('', 204)


@api.route("/code/<int:file_id>", methods=['GET'])
@login_required
def get_code(file_id):
    file = db.session.query(models.File).filter(
        models.File.id == file_id).first()

    if file is None:
        raise APIException('File not found',
                           'The file with id {} was not found'.format(file_id),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)

    if file.work.user.id != current_user.id:
        auth.ensure_permission('can_view_files',
                               file.work.assignment.course.id)

    if 'type' in request.args and request.args['type'] == 'metadata':
        return get_file_metadata(file)
    if 'type' in request.args and request.args['type'] == 'binary':
        return get_binary_file(file)
    return get_plain_text_code(file)


def get_file_metadata(file):
    return jsonify({"name": file.name, "extension": file.extension})


def get_binary_file(file):
    file_data = psef.files.get_binary_contents(file)
    response = make_response(file_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=' + file.name

    return response


def get_plain_text_code(file):
    line_feedback = {}
    linter_feedback = {}

    try:
        auth.ensure_can_see_grade(file.work)
        for comment in db.session.query(models.Comment).filter_by(
                file_id=file.id).all():
            line_feedback[str(comment.line)] = comment.comment
        for comment in db.session.query(models.LinterComment).filter_by(
                file_id=file.id).all():
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
        lang=file.extension,
        code=psef.files.get_file_contents(file),
        feedback=line_feedback,
        linter_feedback=linter_feedback)

"""
This module defines all API routes with the main directory "code". Thus the
APIs are used to manipulate student submitted code and the related feedback.
"""

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
    Create or change a single line comment of a code file.

    :param id: The id of the code file
    :type id: int
    :param line: The line number of the comment
    :type line: int
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not can grade work in the
        attached course (INCORRECT_PERMISSION)
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

    return '', 204


@api.route("/code/<int:id>/comments/<int:line>", methods=['DELETE'])
def remove_comment(id, line):
    """
    Removes the comment on line X if the request is valid.

    Raises APIException:
        - If no comment on line X was found

    :param id: The id of the code file
    :type id: int
    :param line: The line number of the comment
    :type line: int
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: if there is no comment at the given line number
        (OBJECT_NOT_FOUND)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not can grade work in the
        attached course (INCORRECT_PERMISSION)
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
                           APICodes.OBJECT_NOT_FOUND, 404)
    return '', 204


@api.route("/code/<int:file_id>", methods=['GET'])
@login_required
def get_code(file_id):
    """
    Get data from the file with the given id.

    :param file_id: The id of the file
    :type file_id: int
    :returns: A response containing a plain text file unless specified otherwise
    :rtype: Response

    :raises APIException: if there is file with the given id
        (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the file does not belong to user and the
        user can not view files in the attached course (INCORRECT_PERMISSION)
    """
    file = db.session.query(models.File).filter(
        models.File.id == file_id).first()

    if file is None:
        raise APIException('File not found',
                           'The file with id {} was not found'.format(file_id),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)

    if file.work.user.id != current_user.id:
        auth.ensure_permission('can_view_files',
                               file.work.assignment.course.id)

    if request.args.get('type') == 'metadata':
        return jsonify(file)
    elif request.args.get('type') == 'binary':
        return get_binary_file(file)
    elif request.args.get('type') == 'feedback':
        return get_feedback(file, linter=False)
    elif request.args.get('type') == 'linter-feedback':
        return get_feedback(file, linter=True)
    else:
        contents = psef.files.get_file_contents(file)
        res = make_response(contents)
        res.headers['Content-Type'] = 'text/plain'
        return res


def get_binary_file(file):
    """
    Creates a response with the content of the given file as inline pdf.

    :param file: The file object
    :type file: File
    :returns: A response containing a pdf file
    :rtype: Response
    """
    file_data = psef.files.get_binary_contents(file)
    response = make_response(file_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=' + file.name

    return response


def get_feedback(file, linter=False):
    """
    Returns the comments attached to the given file if the user can see them,
    else returns an empty dict.

    :param file: The file object
    :type file: File
    :param linter: If true returns linter comments instead
    :type linter: bool
    :returns: A response containing the JSON serialized comments
    :rtype: Response
    """
    try:
        auth.ensure_can_see_grade(file.work)
        if linter:
            comments = db.session.query(models.LinterComment).filter_by(
                file_id=file.id).all()

            res = {}
            for comment in comments:
                line = str(comment.line)
                if line not in res:
                    res[line] = {}
                res[line][comment.linter.tester.name] = comment
            return jsonify(res)
        else:
            comments = db.session.query(models.Comment).filter_by(
                file_id=file.id).all()

            res = {}
            for comment in comments:
                res[str(comment.line)] = comment
            return jsonify(res)

    except auth.PermissionException:
        return jsonify({})

"""
This module defines all API routes with the main directory "code". Thus the
APIs are used to manipulate student submitted code and the related feedback.

:license: AGPLv3, see LICENSE for details.
"""

import typing as t

from flask import request, make_response
from flask_login import login_required

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

if t.TYPE_CHECKING:
    import werkzeug  # NOQA

_HumanFeedback = models.Comment
_LinterFeedback = t.Dict[str, models.LinterComment]
_FeedbackMapping = t.Dict[str, t.Union[_HumanFeedback, _LinterFeedback]]


@api.route("/code/<int:id>/comments/<int:line>", methods=['PUT'])
def put_comment(id: int, line: int) -> EmptyResponse:
    """Create or change a single :class:`.models.Comment` of a code
    :class:`.models.File`.

    .. :quickref: Code; Add or change a comment

    :param int id: The id of the code file
    :param int line: The line number of the comment
    :returns: An empty response with return code 204

    :<json str comment: The comment to add to the given file on the given line.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not can grade work in the
                                 attached course. (INCORRECT_PERMISSION)
    """
    content = ensure_json_dict(request.get_json())

    comment = db.session.query(models.Comment).filter(
        models.Comment.file_id == id, models.Comment.line == line
    ).one_or_none()

    ensure_keys_in_dict(content, [('comment', str)])

    if comment:
        auth.ensure_permission(
            'can_grade_work', comment.file.work.assignment.course_id
        )
        comment.comment = content['comment']
    else:
        file = helpers.get_or_404(models.File, id)
        auth.ensure_permission(
            'can_grade_work', file.work.assignment.course_id
        )

        db.session.add(
            models.Comment(
                file_id=id,
                user_id=current_user.id,
                line=line,
                comment=content['comment']
            )
        )

    db.session.commit()

    return make_empty_response()


@api.route("/code/<int:id>/comments/<int:line>", methods=['DELETE'])
def remove_comment(id: int, line: int) -> EmptyResponse:
    """Removes the given :class:`.models.Comment` in the given
    :class:`.models.File`

    .. :quickref: Code; Remove a comment

    :param int id: The id of the code file
    :param int line: The line number of the comment
    :returns: An empty response with return code 204

    :raises APIException: If there is no comment at the given line number.
                          (OBJECT_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not can grade work in the
                                 attached course. (INCORRECT_PERMISSION)
    """
    comment = helpers.filter_single_or_404(
        models.Comment, models.Comment.file_id == id,
        models.Comment.line == line
    )

    auth.ensure_permission(
        'can_grade_work', comment.file.work.assignment.course_id
    )
    db.session.delete(comment)
    db.session.commit()

    return make_empty_response()


@api.route("/code/<int:file_id>", methods=['GET'])
@login_required
def get_code(
    file_id: int
) -> t.Union['werkzeug.wrappers.Response',
             JSONResponse[t.Union[models.File, _FeedbackMapping]]]:
    """Get data from the :class:`.models.File` with the given id.

    .. :quickref: Code; Get code or its metadata

    The are several options to change the data that is returned. Based on the
    argument type in the request different functions are called.

    - If ``type == 'metadata'`` the JSON serialized :class:`.models.File` is
      returned.
    - If ``type == 'binary'`` see :py:func:`get_binary_file`
    - If ``type == 'feedback'`` or ``type == 'linter-feedback'`` see
      :py:func:`get_feedback`
    - Otherwise the content of the file is returned as plain text.

    :param int file_id: The id of the file
    :returns: A response containing a plain text file unless specified
              otherwise

    :raises APIException: If there is not file with the given id.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the file does not belong to user and the
                                 user can not view files in the attached
                                 course. (INCORRECT_PERMISSION)
    """
    file = helpers.filter_single_or_404(models.File, models.File.id == file_id)

    if file.work.user_id != current_user.id:
        auth.ensure_permission(
            'can_view_files', file.work.assignment.course_id
        )

    if request.args.get('type') == 'metadata':
        return jsonify(file)
    elif request.args.get('type') == 'feedback':
        return jsonify(get_feedback(file, linter=False))
    elif request.args.get('type') == 'binary':
        return get_binary_file(file)
    elif request.args.get('type') == 'linter-feedback':
        return jsonify(get_feedback(file, linter=True))
    else:
        contents = psef.files.get_file_contents(file)
        res: 'werkzeug.wrappers.Response' = make_response(contents)
        res.headers['Content-Type'] = 'text/plain'
        return res


def get_binary_file(file: models.File) -> 'werkzeug.wrappers.Response':
    """Creates a response with the content of the given :class:`.models.File`
    as inline pdf.

    :param file: The file object
    :returns: A response containing a pdf file
    """
    file_data = psef.files.get_binary_contents(file)
    response = make_response(file_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=' + file.name

    return response


def get_feedback(file: models.File, linter: bool=False) -> _FeedbackMapping:
    """Returns the :class:`.models.Comment` objects attached to the given
    :class:`.models.File` if the user can see them, else returns an empty dict.

    .. note::

        This function will check if the current user has permission to see
        comments for this file.

    :param models.File file: The file object
    :param bool linter: If true returns linter comments instead
    :returns: Feedback for the given file. If ``linter`` is true it will be
        given in the form ``{line: {linter_name: comment}}`` otherwise it is in
        the form ``{line: comment}``.
    """
    res: _FeedbackMapping = {}
    try:
        auth.ensure_can_see_grade(file.work)

        if linter:
            comments = db.session.query(models.LinterComment).filter_by(
                file_id=file.id
            ).all()

            for linter_comment in comments:  # type: models.LinterComment
                line = str(linter_comment.line)
                if line not in res:
                    res[line] = {}
                name = linter_comment.linter.tester.name
                res[line][name] = linter_comment  # type: ignore
        else:
            comments = db.session.query(models.Comment).filter_by(
                file_id=file.id
            ).all()

            for human_comment in comments:  # type: models.Comment
                res[str(human_comment.line)] = human_comment
        return res

    except auth.PermissionException:
        return res

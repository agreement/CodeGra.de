"""
This module defines all API routes with the main directory "code". Thus the
APIs are used to manipulate student submitted code and the related feedback.

:license: AGPLv3, see LICENSE for details.
"""

import shutil
import typing as t

from flask import request, make_response
from sqlalchemy.orm import make_transient

import psef.auth as auth
import psef.files
import psef.models as models
import psef.helpers as helpers
from psef import db, current_user
from psef.errors import APICodes, APIException
from psef.models import FileOwner
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api

if t.TYPE_CHECKING:  # pragma: no cover
    import werkzeug  # NOQA

_HumanFeedback = models.Comment
_LinterFeedback = t.MutableSequence[t.Tuple[str, models.LinterComment]]
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
    comment = db.session.query(models.Comment).filter(
        models.Comment.file_id == id, models.Comment.line == line
    ).one_or_none()

    def get_comment() -> str:
        content = ensure_json_dict(request.get_json())
        ensure_keys_in_dict(content, [('comment', str)])
        return t.cast(str, content['comment'])

    if comment:
        auth.ensure_permission(
            'can_grade_work', comment.file.work.assignment.course_id
        )

        comment.comment = get_comment()
    else:
        file = helpers.get_or_404(models.File, id)
        auth.ensure_permission(
            'can_grade_work',
            file.work.assignment.course_id,
        )

        db.session.add(
            models.Comment(
                file_id=id,
                user_id=current_user.id,
                line=line,
                comment=get_comment(),
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
@auth.login_required
def get_code(file_id: int
             ) -> t.Union['werkzeug.wrappers.Response', JSONResponse[
                 t.Union[t.Mapping[str, str], models.File, _FeedbackMapping]
             ]]:
    """Get data from the :class:`.models.File` with the given id.

    .. :quickref: Code; Get code or its metadata

    The are several options to change the data that is returned. Based on the
    argument type in the request different functions are called.

    - If ``type == 'metadata'`` the JSON serialized :class:`.models.File` is
        returned.
    - If ``type == 'pdf'`` a object with a single key, `name`, with as value
        the return values of :py:func:`get_pdf_file`.
    - If ``type == 'feedback'`` or ``type == 'linter-feedback'`` see
        :py:func:`get_feedback`
    - Otherwise the content of the file is returned as plain text.

    :param int file_id: The id of the file
    :returns: A response containing a plain text file unless specified
        otherwise.

    :raises APIException: If there is not file with the given id.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the file does not belong to user and the
                                 user can not view files in the attached
                                 course. (INCORRECT_PERMISSION)
    """
    file = helpers.filter_single_or_404(models.File, models.File.id == file_id)

    auth.ensure_can_view_files(file.work, file.fileowner == FileOwner.teacher)

    if request.args.get('type') == 'metadata':
        return jsonify(file)
    elif request.args.get('type') == 'feedback':
        return jsonify(get_feedback(file, linter=False))
    elif request.args.get('type') == 'pdf':
        return jsonify({'name': get_pdf_file(file)})
    elif request.args.get('type') == 'linter-feedback':
        return jsonify(get_feedback(file, linter=True))
    else:
        contents = psef.files.get_file_contents(file)
        res: 'werkzeug.wrappers.Response' = make_response(contents)
        res.headers['Content-Type'] = 'text/plain'
        return res


def get_pdf_file(file: models.File) -> str:
    """Copies the given file to the mirror uploads folder and returns its name.

    To get this file, see the :func:`psef.v1.files.get_file` function.

    :param file: The file object
    :returns: The name of the newly created file (the copy).
    """
    path, name = psef.files.random_file_path('MIRROR_UPLOAD_DIR')
    shutil.copyfile(file.get_diskname(), path)

    return name


def get_feedback(file: models.File, linter: bool=False) -> _FeedbackMapping:
    """Returns the :class:`.models.Comment` objects attached to the given
    :class:`.models.File` if the user can see them, else returns an empty dict.

    .. note::

        This function will check if the current user has permission to see
        comments for this file.

    :param models.File file: The file object
    :param bool linter: If true returns linter comments instead
    :returns: Feedback for the given file. If ``linter`` is true it will be
        given in the form ``{line: [(linter_name, comment)]`` otherwise it is
        in the form ``{line: comment}``.
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
                    res[line] = []
                name = linter_comment.linter.tester.name
                res[line].append((name, linter_comment))  # type: ignore
        else:
            comments = db.session.query(models.Comment).filter_by(
                file_id=file.id
            ).all()

            for human_comment in comments:  # type: models.Comment
                res[str(human_comment.line)] = human_comment
        return res

    except auth.PermissionException:
        return res


@api.route('/code/<int:file_id>', methods=['DELETE'])
def delete_code(file_id: int) -> EmptyResponse:
    """Delete the given file.

    .. :quickref: Code; Delete the given file.

    If a student does this request before the deadline, the file will be
    completely deleted. , if the request is done after the deadline the user
    doing the delete will be removed from the ownership of the file and if
    there are no owners left the file is deleted.

    :returns: Nothing.

    :raises APIException: If there is not file with the given id.
        (OBJECT_ID_NOT_FOUND)
    :raises APIException: If you do not have permission to delete the given
        file. (INCORRECT_PERMISSION)
    """
    code: models.File = helpers.filter_single_or_404(
        models.File,
        models.File.id == file_id,
        ~models.File.children.any(),  # type: ignore
    )

    auth.ensure_can_edit_work(code.work)

    def _raise_invalid() -> None:
        raise APIException(
            'You cannot delete this file as you don\'t own it',
            f'File {file_id} is not owned by {current_user.id}',
            APICodes.INCORRECT_PERMISSION, 403
        )

    if code.work.user_id == current_user.id:
        current, other = models.FileOwner.student, models.FileOwner.teacher
    else:
        current, other = models.FileOwner.teacher, models.FileOwner.student

    if code.fileowner == other:
        _raise_invalid()
    elif code.fileowner == current:
        code.delete_from_disk()
        db.session.delete(code)
    elif code.fileowner == models.FileOwner.both:
        code.fileowner = other

    db.session.commit()

    return make_empty_response()


@api.route('/code/<int:file_id>', methods=['PATCH'])
@auth.login_required
def update_code(file_id: int) -> JSONResponse[models.File]:
    """Update the content of the given file.

    .. :quickref: Code; Update the content of the given file.

    The body of the request should contain the new content of the file. If a
    student does this request before the deadline, the owner of the file will
    be the student and the teacher (`both`), if the request is done after the
    deadline the owner of the new file will be the one doing the request while
    the old file will be removed or given to the other owner if the file was
    owned by `both`.

    .. note::

      The id of the returned code object can change, but does not have to.

    :returns: The created code object.

    :raises APIException: If there is not file with the given id.
        (OBJECT_ID_NOT_FOUND)
    :raises APIException: If you do not have permission to change the given
        file. (INCORRECT_PERMISSION)
    """
    code = helpers.filter_single_or_404(
        models.File,
        models.File.id == file_id,
        models.File.is_directory == False,  # NOQA
    )

    auth.ensure_can_edit_work(code.work)

    def _raise_invalid() -> None:
        raise APIException(
            'You cannot delete this file as you don\'t own it',
            f'File {file_id} is not owned by {current_user.id}',
            APICodes.INCORRECT_PERMISSION, 403
        )

    def _write_to_file(code: models.File) -> None:
        with open(code.get_diskname(), 'w') as f:
            f.write(request.get_data(as_text=True))

    if code.work.user_id == current_user.id:
        current, other = models.FileOwner.student, models.FileOwner.both
        if code.fileowner == models.FileOwner.teacher:
            _raise_invalid()
        _write_to_file(code)
    else:
        current, other = models.FileOwner.teacher, models.FileOwner.student
        if code.fileowner == models.FileOwner.student:
            _raise_invalid()
        elif code.fileowner == current:
            _write_to_file(code)
        else:
            code.fileowner = other
            db.session.commit()
            # reload after commit
            code = db.session.query(models.File).get(code.id)

            db.session.expunge(code)
            make_transient(code)
            code.id = None
            db.session.add(code)

            _, code.filename = psef.files.random_file_path()
            _write_to_file(code)
            code.fileowner = current

    db.session.commit()

    return jsonify(code)

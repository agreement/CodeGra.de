"""
This module defines all API routes with the main directory "code". Thus the
APIs are used to manipulate student submitted code and the related feedback.

:license: AGPLv3, see LICENSE for details.
"""

import shutil
import typing as t

import sqlalchemy.sql as sql
from flask import request, make_response
from sqlalchemy.orm import make_transient

import psef.auth as auth
import psef.files
import psef.models as models
import psef.helpers as helpers
from psef import app, current_user
from psef.errors import APICodes, APIException
from psef.models import FileOwner, db
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

    .. :quickref: Code; Add or change a comment.

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

    .. :quickref: Code; Remove a comment.

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

    .. :quickref: Code; Get code or its metadata.

    The are several options to change the data that is returned. Based on the
    argument type in the request different functions are called.

    - If ``type == 'metadata'`` the JSON serialized :class:`.models.File` is
        returned.
    - If ``type == 'file-url'`` or ``type == 'pdf'`` (deprecated) an object
        with a single key, `name`, with as value the return values of
        :py:func:`get_file_url`.
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
    get_type = request.args.get('type', None)

    if get_type == 'metadata':
        return jsonify(file)
    elif get_type == 'feedback':
        return jsonify(get_feedback(file, linter=False))
    elif get_type == 'pdf' or get_type == 'file-url':
        return jsonify({'name': get_file_url(file)})
    elif get_type == 'linter-feedback':
        return jsonify(get_feedback(file, linter=True))
    else:
        contents = psef.files.get_file_contents(file)
        res: 'werkzeug.wrappers.Response' = make_response(contents)
        res.headers['Content-Type'] = 'application/octet-stream'
        return res


def get_file_url(file: models.File) -> str:
    """Copies the given file to the mirror uploads folder and returns its name.

    To get this file, see the :func:`psef.v1.files.get_file` function.

    :param file: The file object
    :returns: The name of the newly created file (the copy).
    """
    path, name = psef.files.random_file_path('MIRROR_UPLOAD_DIR')
    shutil.copyfile(file.get_diskname(), path)

    return name


def get_feedback(file: models.File, linter: bool = False) -> _FeedbackMapping:
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
            comments = db.session.query(models.LinterComment
                                        ).filter_by(file_id=file.id).all()

            for linter_comment in comments:  # type: models.LinterComment
                line = str(linter_comment.line)
                if line not in res:
                    res[line] = []
                name = linter_comment.linter.tester.name
                res[line].append((name, linter_comment))  # type: ignore
        else:
            comments = db.session.query(models.Comment
                                        ).filter_by(file_id=file.id).all()

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
    completely deleted. If the request is done after the deadline the user
    doing the delete will be removed from the ownership of the file and if
    there are no owners left the file is deleted.

    If the file owner of the given file is the same as that of the user doing
    the request (so the file will be completely deleted) the given file should
    not have any comments (Linter or normal) associated with it. If it still
    has comments the request will fail with error code 400.

    :returns: Nothing.

    :raises APIException: If the request will result in wrong
        state. (INVALID_STATE)
    :raises APIException: If there is not file with the given id.
        (OBJECT_ID_NOT_FOUND)
    :raises APIException: If you do not have permission to delete the given
        file. (INCORRECT_PERMISSION)
    """
    code: models.File = helpers.get_or_404(models.File, file_id)

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

    if not all(child.fileowner == other for child in code.children.all()):
        raise APIException(
            'You cannot delete this directory as it has children',
            f'The file "{file_id}" has children with fileowner "{current}"',
            APICodes.INVALID_STATE, 400
        )

    if code.fileowner == other:
        _raise_invalid()
    elif code.fileowner == current:
        if db.session.query(
            sql.or_(
                models.Comment.query.filter_by(file_id=code.id).exists(),
                models.LinterComment.query.filter_by(file_id=code.id).exists(),
            )
        ).scalar():
            raise APIException(
                'You cannot delete this file as it has comments',
                f'The file "{file_id}" has comments associated with it.',
                APICodes.INVALID_STATE,
                400,
            )
        code.delete_from_disk()
        db.session.delete(code)
    elif code.fileowner == models.FileOwner.both:
        code.fileowner = other

    db.session.commit()

    return make_empty_response()


def split_code(
    code: models.File, new_owner: FileOwner, old_owner: FileOwner, copy: bool
) -> models.File:
    """Split the given ``code`` into multiple code objects.

    The old object in the database will be given a ``fileowner`` of
    ``old_owner`` and the newly created object will be given ``new_owner``. If
    ``code`` is a directory this directory is splitted (see
    :py:func:`redistribute_directory`), if it is a file the original content of
    the file is only copied if ``copy`` is ``True``.

    :param code: The file to split.
    :param new_owner: The new ``fileowner`` of the new file.
    :param old_owner: The new ``fileowner`` of the old file.
    :param copy: Should the file contents be copied over to the new file.
    :returns: The newly constructed file.
    """
    code.fileowner = old_owner
    old_id = code.id
    old_diskname = None if code.is_directory else code.get_diskname()
    db.session.flush()
    code = db.session.query(models.File).get(code.id)

    db.session.expunge(code)
    make_transient(code)
    code.id = None
    db.session.add(code)
    db.session.flush()

    code.fileowner = new_owner
    if not code.is_directory:
        _, code.filename = psef.files.random_file_path()
        shutil.copyfile(old_diskname, code.get_diskname())
    else:
        redistribute_directory(code, models.File.query.get(old_id))

    return code


def redistribute_directory(
    new_directory: models.File, old_directory: models.File
) -> None:
    """Redistribute a given old directory between itself and a new directory.

    .. note::

        None of the given directories may be owned by ``both`` and they should
        not have the same owner.

    All files in the given ``old_directory`` are checked, if the file is owned
    by ``both`` it is split up (see :py:func:`split_code`), if it is owned by
    the owner of the ``new_directory`` its parent is changed and if it is owned
    by the owner of ``old_directory`` nothing is changed.

    :param new_directory: The directory files should be redistributed into.
    :param old_directory: The directory files should be redistributed out of.
    :returns: Nothing.
    """
    assert old_directory.fileowner != FileOwner.both
    assert new_directory.fileowner != FileOwner.both
    assert new_directory.fileowner != old_directory.fileowner

    for child in old_directory.children:
        if child.fileowner == new_directory.fileowner:
            child.parent = new_directory
        elif child.fileowner == old_directory.fileowner:
            pass
        else:
            code = split_code(
                child,
                new_directory.fileowner,
                old_directory.fileowner,
                copy=True
            )
            code.parent = new_directory
    db.session.flush()


@api.route('/code/<int:file_id>', methods=['PATCH'])
@auth.login_required
def update_code(file_id: int) -> JSONResponse[models.File]:
    """Update the content or name of the given file.

    .. :quickref: Code; Update the content or name of the given file.

    If a
    student does this request before the deadline, the owner of the file will
    be the student and the teacher (`both`), if the request is done after the
    deadline the owner of the new file will be the one doing the request while
    the old file will be removed or given to the other owner if the file was
    owned by `both`. You can give a request parameter ``operation`` to
    determine the operation:

    - If ``operation`` is ``rename`` the request should also contain a new path
      for the file under the key ``new_path``.
    - If ``operation`` is ``content`` the body of the request should contain
      the new content of the file. This operation is used if no or no valid
      operation was given.

    .. note::

      The id of the returned code object can change, but does not have to.

    :returns: The created code object.

    :raises APIException: If there is not file with the given id.
        (OBJECT_ID_NOT_FOUND)
    :raises APIException: If you do not have permission to change the given
        file. (INCORRECT_PERMISSION)
    :raises APIException: If the request is bigger than the maximum upload
        size. (REQUEST_TOO_LARGE)
    """
    dir_filter = None if request.args.get('operation') == 'rename' else True
    code = helpers.filter_single_or_404(
        models.File,
        models.File.id == file_id,
        models.File.is_directory != dir_filter,
    )

    auth.ensure_can_edit_work(code.work)

    if (request.content_length and
            request.content_length > app.config['MAX_UPLOAD_SIZE']):
        raise APIException(
            'Uploaded files are too big.', 'Request is bigger than maximum '
            f'upload size of {app.config["MAX_UPLOAD_SIZE"]}.',
            APICodes.REQUEST_TOO_LARGE, 400
        )

    def _update_file(
        code: models.File,
        other: models.FileOwner,
    ) -> None:
        if request.args.get('operation', None) == 'rename':
            code.rename_code(new_name, new_parent, other)
            db.session.flush()
            code.parent = new_parent
        else:
            with open(code.get_diskname(), 'wb') as f:
                f.write(request.get_data())

    if code.work.assignment.is_open and current_user.id == code.work.user_id:
        current, other = models.FileOwner.both, models.FileOwner.teacher
    elif code.work.user_id == current_user.id:
        current, other = models.FileOwner.student, models.FileOwner.teacher
    else:
        current, other = models.FileOwner.teacher, models.FileOwner.student

    if request.args.get('operation', None) == 'rename':
        ensure_keys_in_dict(request.args, [('new_path', str)])
        new_path = t.cast(str, request.args['new_path'])
        path_arr, _ = psef.files.split_path(new_path)
        new_name = path_arr[-1]
        new_parent = code.work.search_file(
            '/'.join(path_arr[:-1]) + '/', other
        )

    if code.fileowner == current:
        _update_file(code, other)
    elif code.fileowner != models.FileOwner.both:
        raise APIException(
            'This file does not belong to you',
            f'The file {code.id} belongs to {code.fileowner.name}',
            APICodes.INVALID_STATE, 403
        )
    else:
        with db.session.begin_nested():
            code = split_code(code, current, other, copy=False)
            _update_file(code, other)

    db.session.commit()

    return jsonify(code)

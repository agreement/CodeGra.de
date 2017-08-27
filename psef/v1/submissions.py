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
from psef.models import FileOwner
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response, filter_single_or_404
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

    :query str owner: The type of files to list, if set to `teacher` only
        teacher files will be listed, otherwise only student files will be
        listed.

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
        exclude_owner = models.File.get_exclude_owner(
            request.args.get('owner'),
            work.assignment.course_id,
        )
        return jsonify(get_zip(work, exclude_owner))
    elif request.args.get('type') == 'feedback':
        auth.ensure_can_see_grade(work)
        return jsonify(get_feedback(work))
    return jsonify(work)


def get_feedback(work: models.Work) -> t.Mapping[str, str]:
    """Get the feedback of :class:`.models.Work` as a plain text file.

    :param work: The submission with the required feedback.
    :returns: A object with two keys: ``name`` where the value is the name
        which can be given to ``GET - /api/v1/files/<name>`` and
        ``output_name`` which is the resulting file should be named.
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


def get_zip(work: models.Work,
            exclude_owner: FileOwner) -> t.Mapping[str, str]:
    """Return a :class:`.models.Work` as a zip file.

    :param work: The submission which should be returns as zip file.
    :param exclude_owner: The owner to exclude from the files in the zip. So if
        this is `teacher` only files owned by `student` and `both` will be in
        the zip.
    :returns: A object with two keys: ``name`` where the value is the name
        which can be given to ``GET - /api/v1/files/<name>`` and
        ``output_name`` which is the resulting file should be named.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If submission does not belong to the current
                                 user and the user can not view files in the
                                 attached course. (INCORRECT_PERMISSION)
    """
    auth.ensure_can_view_files(work, exclude_owner == FileOwner.student)

    code = helpers.filter_single_or_404(
        models.File,
        models.File.work_id == work.id,
        models.File.parent_id == None,  # NOQA
    )

    path, name = psef.files.random_file_path('MIRROR_UPLOAD_DIR')

    with open(path, 'w+b') as fp:
        with tempfile.TemporaryDirectory() as tmpdir:
            # Restore the files to tmpdir
            psef.files.restore_directory_structure(code, tmpdir, exclude_owner)

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
@helpers.feature_required('RUBRICS')
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
    work.select_rubric_item(rubric_item, current_user)
    db.session.commit()

    return jsonify(work.__rubric_to_json__(), status_code=201)


@api.route("/submissions/<int:submission_id>", methods=['PATCH'])
def patch_submission(submission_id: int) -> JSONResponse[models.Work]:
    """Update the given submission (:class:`.models.Work`) if it already
    exists.

    .. :quickref: Submission; Update a submissions grade and feedback.

    :param int submission_id: The id of the submission
    :returns: Empty response with return code 204

    :>json float grade: The new grade, if this is not `null` it should be a
        float and feedback is then also required. If it is `null` the grade
        will be cleared or reset to the rubric grade.
    :>json str feedback: The feedback for the student. This is required if
        grade is not `null`, it will be ignored if grade is `null`.

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

    if 'grade' in content and content['grade'] is None:
        work.set_grade(None, current_user)
    else:
        ensure_keys_in_dict(
            content, [('grade', numbers.Real),
                      ('feedback', str)]
        )
        feedback = t.cast(str, content['feedback'])
        grade = float(t.cast(numbers.Real, content['grade']))

        if not 0 <= grade <= 10:
            raise APIException(
                'Grade submitted not between 0 and 10',
                f'Grade for work with id {submission_id} '
                f'is {content["grade"]} which is not between 0 and 10',
                APICodes.INVALID_PARAM, 400
            )

        work.set_grade(grade, current_user)
        work.comment = feedback

    db.session.commit()
    return jsonify(work)


@api.route('/submissions/<int:submission_id>/grade_history/', methods=['GET'])
def get_grade_history(submission_id: int
                      ) -> JSONResponse[t.Sequence[models.GradeHistory]]:
    """Get the grade history for the given submission.

    .. quickref:: Submission; Get the grade history for the given submission.

    :returns: A list of :class:`.models.GradeHistory` object serialized to
        json for the given assignment.
    :raises PermissionException: If the current user has no permission to see
        the grade history. (INCORRECT_PERMISSION)
    """
    work = helpers.get_or_404(models.Work, submission_id)

    auth.ensure_permission('can_see_grade_history', work.assignment.course_id)

    hist: t.MutableSequence[models.GradeHistory]
    hist = db.session.query(models.GradeHistory).filter_by(
        work_id=work.id
    ).order_by(
        models.GradeHistory.changed_at.desc(),  # type: ignore
    ).all()

    return jsonify(hist)


@api.route("/submissions/<int:submission_id>/files/", methods=['POST'])
def create_new_file(submission_id: int) -> JSONResponse[psef.files.FileTree]:
    """Create a new file or directory for the given submission.

    .. :quickref: Submission; Create a new file or directory for a submission.

    :param str path: The path of the new file to create.
    :param str is_directory: If this value is `true` the new file will be a
        directory and the body of the post is ignored.

    :returns: The new file tree for this assignment.
    """
    work = helpers.get_or_404(models.Work, submission_id)
    exclude_owner = models.File.get_exclude_owner(
        'auto', work.assignment.course_id
    )

    auth.ensure_can_edit_work(work)
    if exclude_owner == FileOwner.teacher:  # we are a student
        assig = work.assignment
        new_owner = FileOwner.both if assig.is_open else FileOwner.student
    else:
        new_owner = FileOwner.teacher

    is_directory = request.args.get('is_directory', None) == 'true'
    ensure_keys_in_dict(request.args, [('path', str)])

    pathname = request.args.get('path', None)
    pathname = pathname[1:] if pathname[0] == '/' else pathname
    pathname = pathname[:-1] if pathname[-1] == '/' else pathname
    patharr = pathname.split('/')
    print(new_owner, exclude_owner, pathname)

    if len(patharr) < 2:
        raise APIException(
            'Path should contain at least a two parts',
            f'"{pathname}" only contains {len(patharr)} parts',
            APICodes.INVALID_PARAM, 400
        )

    parent = helpers.filter_single_or_404(
        models.File,
        models.File.work_id == submission_id,
        models.File.fileowner != exclude_owner,
        models.File.name == patharr[0],
        models.File.parent_id == None,  # NOQA
    )

    code = None
    for idx, part in enumerate(patharr[1:]):
        code = models.File.query.filter(
            models.File.fileowner != exclude_owner,
            models.File.name == part,
            models.File.parent == parent,
        ).first()
        end_idx = idx + 1
        if code is None:
            break
        parent = code

    def _is_last(idx: int) -> bool:
        return end_idx + idx + 1 == len(patharr)

    if _is_last(-1) or not parent.is_directory:
        raise APIException(
            'All part did already exist',
            f'The path "{pathname}" did already exist',
            APICodes.INVALID_STATE,
            400,
        )

    for idx, part in enumerate(patharr[end_idx:]):
        if _is_last(idx) and not is_directory:
            is_dir = False
            name, ext = os.path.splitext(part)
            d_filename, filename = psef.files.random_file_path()
            with open(d_filename, 'w') as f:
                f.write(request.get_data(as_text=True))
        else:
            is_dir, name, ext, filename = True, part, None, None
        code = models.File(
            work_id=submission_id,
            extension=ext,
            name=name,
            filename=filename,
            is_directory=is_dir,
            parent=parent,
            fileowner=new_owner,
        )
        db.session.add(code)
        parent = code
    db.session.commit()

    return jsonify(
        helpers.filter_single_or_404(
            models.File,
            models.File.work_id == submission_id,
            models.File.parent_id == None,  # NOQA
        ).list_contents(exclude_owner)
    )


@api.route("/submissions/<int:submission_id>/files/", methods=['GET'])
@auth.login_required
def get_dir_contents(submission_id: int
                     ) -> t.Union[JSONResponse[psef.files.FileTree],
                                  JSONResponse[t.Mapping[str, t.Any]]]:
    """Return the file directory info of a file of the given submission
    (:class:`.models.Work`).

    .. :quickref: Submission; Get the directory contents for a submission.

    The default file is the root of the submission, but a specific file can be
    specified with the file_id argument in the request.

    :param int submission_id: The id of the submission
    :returns: A response with the JSON serialized directory structure as
        content and return code 200. For the exact structure see
        :py:meth:`.File.list_contents`. If path is given the return value will
        be stat datastructure, see :py:func:`files.get_stat_information`.

    :query int file_id: The file id of the directory to get. If this is not
        given the parent directory for the specified submission is used.
    :query str path: The path that should be searched. The ``file_id`` query
        parameter is used if both ``file_id`` and ``path`` are present.
    :query str owner: The type of files to list, if set to `teacher` only
        teacher files will be listed, otherwise only student files will be
        listed.

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

    file_id = request.args.get('file_id', False)
    path = request.args.get('path', False)

    exclude_owner = models.File.get_exclude_owner(
        request.args.get('owner', None),
        work.assignment.course_id,
    )

    auth.ensure_can_view_files(work, exclude_owner == FileOwner.student)

    if file_id:
        file = helpers.filter_single_or_404(
            models.File,
            models.File.id == file_id,
            models.File.work_id == work.id,
        )
    elif path:
        found_file = search_file(submission_id, path, exclude_owner)
        return jsonify(psef.files.get_stat_information(found_file))
    else:
        file = helpers.filter_single_or_404(
            models.File,
            models.File.work_id == submission_id,
            models.File.parent_id == None,  # NOQA
            models.File.fileowner != exclude_owner
        )

    if not file.is_directory:
        raise APIException(
            'File is not a directory',
            f'The file with code {file.id} is not a directory',
            APICodes.OBJECT_WRONG_TYPE, 400
        )

    return jsonify(file.list_contents(exclude_owner))


def search_file(
    submission_id: int,
    pathname: str,
    exclude: FileOwner,
) -> models.File:
    """Search for a file in the given submission with the given name.

    :param submission_id: The id of the submission in which the file should be.
    :param pathname: The path of the file to search for, this may contain
        leading and trailing slashes which do not have any meaning.
    :param exclude: The fileowner to exclude from search, like described in
        :func:`get_zip`.
    :returns: The found file.
    """
    pathname = pathname[1:] if pathname[0] == '/' else pathname
    pathname = pathname[:-1] if pathname[-1] == '/' else pathname

    patharr = pathname.split('/')

    parent: t.Optional[t.Any] = None
    for idx, pathpart in enumerate(patharr[:-1]):
        if parent is not None:
            parent = parent.c.id

        parent = db.session.query(models.File.id).filter(
            models.File.name == pathpart,
            models.File.parent_id == parent,
            models.File.work_id == submission_id,
            models.File.is_directory == True,  # NOQA
        ).subquery(f'parent_{idx}')

    filename, ext = os.path.splitext(patharr[-1])

    if parent is not None:
        parent = parent.c.id

    return filter_single_or_404(
        models.File,
        models.File.extension == ext,
        models.File.name == filename,
        models.File.parent_id == parent,
        models.File.fileowner != exclude,
        models.File.is_directory == False,  # NOQA
    )

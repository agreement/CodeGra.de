"""
This module defines all API routes with the main directory "linters" and
"linter_comments". These APIs are used to directly communicate about the  state
of linters and their output.

:license: AGPLv3, see LICENSE for details.
"""

import typing as t

from flask import request

import psef.auth as auth
import psef.models as models
import psef.helpers as helpers
from psef import db
from psef.errors import APICodes, APIException
from psef.helpers import (
    JSONType,
    JSONResponse,
    EmptyResponse,
    jsonify,
    ensure_json_dict,
    make_empty_response
)

from . import api


@api.route('/linter_comments/<token>', methods=['PUT'])
def put_linter_comment(token: str) -> EmptyResponse:
    """Add a :class:`.models.LinterComment`.

    .. :quickref: Linter; Add a linter comment.

    :param str token: The token of the :class:`.models.LinterInstance`.
    :returns: An empty response with return code 204

    :<json obj files: The list of files with its comments. It should be a
        a object where the key is the ``file_id`` and the value is a list of
        lists where each sublist contains three items: the ``line`` (int,
        linenumber where the comment should be placed (zero indexed)), the
        ``code`` (str, a status code of the linter) and the feedback (str, the
        feedback or error of the linter).
    :<json crashed: If this item is in the linter instance state will be
        set to crashed. The actual value does not matter.

    :raises APIException: If the linter with the given token was not found.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIExcpetion: If the "file" parameter was missing from the request.
                          (MISSING_REQUIRED_PARAM)
    """
    unit = helpers.get_or_404(models.LinterInstance, token)

    content = ensure_json_dict(request.get_json())

    if 'crashed' in content:
        unit.state = models.LinterState.crashed
        db.session.commit()
        return make_empty_response()

    unit.state = models.LinterState.done

    helpers.ensure_keys_in_dict(content, [('files', dict)])

    with db.session.no_autoflush:
        if isinstance(content['files'], dict):
            files: t.Dict[str, JSONType] = content['files']
            for file_id, feedbacks in files.items():
                if not isinstance(feedbacks, t.List):
                    continue

                f = models.File.query.get(file_id)
                if f is None or f.work_id != unit.work_id:
                    pass

                # TODO: maybe simply delete all comments for this linter on
                # this file
                comments = models.LinterComment.query.filter_by(
                    linter_id=unit.id, file_id=file_id).all()
                lookup = {c.line: c for c in comments}

                for item in feedbacks:
                    if not isinstance(item, t.List) or len(item) != 3:
                        continue
                    line, code, feedback = item
                    if line in lookup:
                        lookup[line].comment = feedback
                        lookup[line].linter_code = code
                    else:
                        c = models.LinterComment(
                            file_id=file_id,
                            line=line,
                            linter_code=code,
                            linter_id=unit.id,
                            comment=feedback)
                        lookup[line] = c
                        db.session.add(c)

    db.session.commit()
    return make_empty_response()


@api.route('/linters/<linter_id>', methods=['DELETE'])
def delete_linter_output(linter_id) -> EmptyResponse:
    """Delete the all the output created by the
    :class:`.models.AssignmentLinter` with the given id.

    .. :quickref: Linter; Delete all linter input for a given linter.

    :param int linter_id: The id of the linter
    :returns: An empty response with return code 204

    :raises APIException: If the linter with the given id does not exist.
                          (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not use the linters in the
                                 course attached to the linter with the given
                                 id. (INCORRECT_PERMISSION)
    """
    linter = helpers.get_or_404(models.AssignmentLinter, linter_id)

    auth.ensure_permission('can_use_linter', linter.assignment.course_id)

    db.session.delete(linter)
    db.session.commit()

    return make_empty_response()


@api.route('/linters/<linter_id>', methods=['GET'])
def get_linter_state(linter_id: str) -> JSONResponse[models.AssignmentLinter]:
    """Get the state of the :class:`.models.AssignmentLinter` with the given
    id.

    .. :quickref: Linter; Get the state of a given linter.

    :param str linter_id: The id of the linter
    :returns: A response containing the JSON serialized linter

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not use the linters in the
                                 course attached to the linter with the given
                                 id. (INCORRECT_PERMISSION)
    """
    linter = helpers.get_or_404(models.AssignmentLinter, linter_id)

    auth.ensure_permission('can_use_linter', linter.assignment.course_id)

    return jsonify(linter)

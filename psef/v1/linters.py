"""
This module defines all API routes with the main directory "linters" and
"linter_comments". These APIs are used to directly communicate about the  state
of linters and their output.
"""

from flask import jsonify, request

import psef.auth as auth
import psef.models as models
from psef import db
from psef.errors import APICodes, APIException

from . import api


@api.route('/linter_comments/<token>', methods=['PUT'])
def put_linter_comment(token):
    """
    Add a linter comment.

    :param token: The token of the linter
    :type token: ?
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: if the linter with the given token was not found
        (OBJECT_ID_NOT_FOUND)
    :raises APIExcpetion: if the "file" parameter was missing from the request
        (MISSING_REQUIRED_PARAM)
    """
    unit = models.LinterInstance.query.get(token)

    if unit is None:
        raise APIException(
            'Linter was not found',
            'The linter with token "{}" was not found'.format(token),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    content = request.get_json()

    if 'crashed' in content:
        unit.state = models.LinterState.crashed
        db.session.commit()
        return '', 204

    unit.state = models.LinterState.done

    if 'files' not in content:
        raise APIException('Not all required keys were found',
                           'The keys "file" was missing form the request body',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    with db.session.no_autoflush:
        for file_id, feedbacks in content['files'].items():
            f = models.File.query.get(file_id)
            if f is None or f.work_id != unit.work_id:
                pass

            # TODO: maybe simply delete all comments for this linter on
            # this file
            comments = models.LinterComment.query.filter_by(
                linter_id=unit.id, file_id=file_id).all()
            lookup = {c.line: c for c in comments}

            for line, code, feedback in feedbacks:
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
    return '', 204


@api.route('/linters/<linter_id>', methods=['DELETE'])
def delete_linter_output(linter_id):
    """
    Delete the all the output created by the linter with the given id.

    :param linter_id: The id of the linter
    :type linter_id: int
    :returns: An empty response with return code 204
    :rtype: (str, int)

    :raises APIException: if the linter with the given id does not exist
        (OBJECT_ID_NOT_FOUND)
    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not use the linters in the
        course attached to the linter with the given id (INCORRECT_PERMISSION)
    """
    linter = models.AssignmentLinter.query.get(linter_id)

    if linter is None:
        raise APIException('Specified linter was not found',
                           'Linter {} was not found'.format(linter_id),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_use_linter', linter.assignment.course_id)

    db.session.delete(linter)
    db.session.commit()

    return '', 204


@api.route('/linters/<linter_id>', methods=['GET'])
def get_linter_state(linter_id):
    """
    Get the state of the linter with the given id.

    :param linter_id: The id of the linter
    :type linter_id: int
    :returns: A response containing the JSON serialized linter
    :rtype: Response

    :raises PermissionException: if there is no logged in user (NOT_LOGGED_IN)
    :raises PermissionException: if the user can not use the linters in the
        course attached to the linter with the given id (INCORRECT_PERMISSION)
    """
    # check for user rights
    perm = db.session.query(models.AssignmentLinter).get(linter_id)
    auth.ensure_permission('can_use_linter', perm.assignment.course_id)

    return jsonify(models.AssignmentLinter.query.get(linter_id))

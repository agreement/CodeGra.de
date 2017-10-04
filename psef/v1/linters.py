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
from psef.models import db
from psef.errors import APICodes, APIException
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    make_empty_response
)

from . import api


@api.route('/linters/<linter_id>', methods=['DELETE'])
def delete_linter_output(linter_id: str) -> EmptyResponse:
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

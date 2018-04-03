"""
This module defines all API routes with the main directory "snippet" or
"snippets. These APIs can be used to add, modify, delete and retrieve the
snippets of the current user.

:license: AGPLv3, see LICENSE for details.
"""
import typing as t

from flask import request

import psef.auth as auth
import psef.models as models
import psef.helpers as helpers
from psef import current_user
from psef.errors import APICodes, APIException
from psef.models import db
from psef.helpers import (
    JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api


@api.route('/snippet', methods=['PUT'])
@auth.permission_required('can_use_snippets')
def add_snippet() -> JSONResponse[models.Snippet]:
    """Add or modify a :class:`.models.Snippet` by key.

    .. :quickref: Snippet; Add or modify a snippet.

    :returns: A response containing the JSON serialized snippet and return
              code 201.
    :<json str value: The new value of the snippet.
    :<json str key: The key of the new or existing snippet.

    :raises APIException: If the parameters "key" and/or "value" were not in
                          the request. (MISSING_REQUIRED_PARAM)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not user snippets
                                 (INCORRECT_PERMISSION)
    """
    content = ensure_json_dict(request.get_json())
    ensure_keys_in_dict(content, [('value', str), ('key', str)])
    value = t.cast(str, content['value'])

    snippet: models.Snippet = models.Snippet.query.filter_by(
        user_id=current_user.id, key=content['key']
    ).first()
    if snippet is None:
        snippet = models.Snippet(
            key=content['key'], value=content['value'], user=current_user
        )
        db.session.add(snippet)
    else:
        snippet.value = value

    db.session.commit()

    return jsonify(snippet, status_code=201)


@api.route('/snippets/', methods=['GET'])
@auth.permission_required('can_use_snippets')
def get_snippets() -> JSONResponse[t.Sequence[models.Snippet]]:
    """Get all snippets (:class:`.models.Snippet`) of the curren
    :class:`.models.User`.

    .. :quickref: Snippet; Get all snippets for the currently logged in user.

    :returns: The an array containing all snippets for the currently logged in
        user.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not user snippets.
        (INCORRECT_PERMISSION)
    """
    return jsonify(models.Snippet.get_all_snippets(current_user))


@api.route('/snippets/<int:snippet_id>', methods=['PATCH'])
@auth.permission_required('can_use_snippets')
def patch_snippet(snippet_id: int) -> EmptyResponse:
    """Modify the :class:`.models.Snippet` with the given id.

    .. :quickref: Snippet; Change a snippets key and value.

    :param int snippet_id: The id of the snippet to change.
    :returns: An empty response with return code 204.

    :<json str key: The new key of the snippet.
    :<json str value: The new value of the snippet.

    :raises APIException: If the parameters "key" and/or "value" were not in
                          the request. (MISSING_REQUIRED_PARAM)
    :raises APIException: If the snippet does not belong to the current user.
                          (INCORRECT_PERMISSION)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not use snippets.
                                 (INCORRECT_PERMISSION)
    """
    content = ensure_json_dict(request.get_json())

    ensure_keys_in_dict(content, [('key', str), ('value', str)])
    key = t.cast(str, content['key'])
    value = t.cast(str, content['value'])

    snip = helpers.get_or_404(models.Snippet, snippet_id)

    if snip.user_id != current_user.id:
        raise APIException(
            'The given snippet is not your snippet',
            'The snippet "{}" does not belong to user "{}"'.format(
                snip.id, current_user.id
            ), APICodes.INCORRECT_PERMISSION, 403
        )

    snip.key = key
    snip.value = value
    db.session.commit()

    return make_empty_response()


@api.route('/snippets/<int:snippet_id>', methods=['DELETE'])
@auth.permission_required('can_use_snippets')
def delete_snippets(snippet_id: int) -> EmptyResponse:
    """Delete the :class:`.models.Snippet` with the given id.

    .. :quickref: Snippet; Delete a snippet.

    :param int snippet_id: The id of the snippet
    :returns: An empty response with return code 204

    :raises APIException: If the snippet with the given id does not exist.
                          (OBJECT_ID_NOT_FOUND)
    :raises APIException: If the snippet does not belong the current user.
                          (INCORRECT_PERMISSION)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not use snippets.
                                 (INCORRECT_PERMISSION)
    """
    snip = helpers.get_or_404(models.Snippet, snippet_id)
    snip = models.Snippet.query.get(snippet_id)

    if snip.user_id != current_user.id:
        raise APIException(
            'The given snippet is not your snippet',
            'The snippet "{}" does not belong to user "{}"'.format(
                snip.id, current_user.id
            ), APICodes.INCORRECT_PERMISSION, 403
        )
    else:
        db.session.delete(snip)
        db.session.commit()
        return make_empty_response()

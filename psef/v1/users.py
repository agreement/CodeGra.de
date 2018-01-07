"""
This module defines all API routes with the main directory "users". Thus the
APIs in this module are mostly used to manipulate :class:`.models.User` objects
and their relations. However to manipulate the current logged in user the main
directory "login" should be used.

:license: AGPLv3, see LICENSE for details.
"""
import typing as t

from flask import request
from sqlalchemy.sql.expression import or_

import psef.auth as auth
import psef.models as models
from psef import limiter, current_user
from psef.errors import APICodes, APIException
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, escape_like,
    ensure_json_dict, ensure_keys_in_dict, make_empty_response
)

from . import api


@api.route('/users/', methods=['GET'])
@auth.permission_required('can_search_users')
@limiter.limit('1 per second', key_func=lambda: str(current_user.id))
def search_users() -> JSONResponse[t.Sequence[models.User]]:
    """Search for a user by name and username.

    .. :quickref: User; Fuzzy search for a user by name and username.

    :param str q: The string to search for, all SQL wildcard are escaped and
        spaces are replaced by wildcards.

    :returns: A list of :py:class:`.models.User` objects that match the given
        query string.

    :raises APIException: If the query string less than 3 characters
        long. (INVALID_PARAM)
    :raises PermissionException: If the currently logged in user does not have
        the permission ``can_search_users``. (INCORRECT_PERMISSION)
    :raises RateLimitExceeded: If you hit this end point more than once per
        second. (RATE_LIMIT_EXCEEDED)
    """
    ensure_keys_in_dict(request.args, [('q', str)])
    query = t.cast(str, request.args.get('q'))

    if len(query) < 3:
        raise APIException(
            'The search string should be at least 3 chars',
            f'The search string "{query}" is not 3 chars or longer.',
            APICodes.INVALID_PARAM, 400
        )

    likes = [
        t.cast(t.Any, col).ilike(
            '%{}%'.format(
                escape_like(query).replace(' ', '%'),
            )
        ) for col in [models.User.name, models.User.username]
    ]
    return jsonify(models.User.query.filter(or_(*likes)).all())

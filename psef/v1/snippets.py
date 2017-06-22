from flask import jsonify, request
from flask_login import current_user

import psef.auth as auth
import psef.models as models
from psef import db
from psef.errors import APICodes, APIException

from . import api


@api.route('/snippet', methods=['PUT'])
@auth.permission_required('can_use_snippets')
def add_snippet():
    content = request.get_json()
    if 'key' not in content or 'value' not in content:
        raise APIException(
            'Not all required keys were in content',
            'The given content ({}) does  not contain "key" and "value"'.
            format(content), APICodes.MISSING_REQUIRED_PARAM, 400)

    snippet = models.Snippet.query.filter_by(
        user_id=current_user.id, key=content['key']).first()
    if snippet is None:
        snippet = models.Snippet(
            key=content['key'], value=content['value'], user=current_user)
        db.session.add(snippet)
    else:
        snippet.value = content['value']
    db.session.commit()

    return jsonify(snippet), 201


@api.route('/snippets/', methods=['GET'])
@auth.permission_required('can_use_snippets')
def get_snippets():
    res = models.Snippet.get_all_snippets(current_user)
    if res:
        return jsonify(res)
    else:
        return '', 204


@api.route('/snippets/<int:snippet_id>', methods=['PATCH'])
@auth.permission_required('can_use_snippets')
def patch_snippet(snippet_id):
    content = request.get_json()
    if 'key' not in content or 'value' not in content:
        raise APIException(
            'Not all required keys were in content',
            'The given content ({}) does  not contain "key" and "value"'.
            format(content), APICodes.MISSING_REQUIRED_PARAM, 400)
    snip = models.Snippet.query.get(snippet_id)
    if snip is None:
        raise APIException('Snippet not found',
                           'The snippet with id {} was not found'.format(snip),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)
    if snip.user.id != current_user.id:
        raise APIException(
            'The given snippet is not your snippet',
            'The snippet "{}" does not belong to user "{}"'.format(
                snip.id, current_user.id), APICodes.INCORRECT_PERMISSION, 403)

    snip.key = content['key']
    snip.value = content['value']
    db.session.commit()

    return '', 204


@api.route('/snippets/<int:snippet_id>', methods=['DELETE'])
@auth.permission_required('can_use_snippets')
def delete_snippets(snippet_id):
    snip = models.Snippet.query.get(snippet_id)
    if snip is None:
        raise APIException(
            'The specified snippet does not exits',
            'The snipped with id "{}" does not exist'.format(snippet_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)
    elif snip.user_id != current_user.id:
        raise APIException(
            'The given snippet is not your snippet',
            'The snippet "{}" does not belong to user "{}"'.format(
                snip.id, current_user.id), APICodes.INCORRECT_PERMISSION, 403)
    else:
        db.session.delete(snip)
        db.session.commit()
        return '', 204

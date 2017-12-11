"""
This module defines all API routes with the main directory "files". These APIs
serve to upload and download temporary files which are not stored explicitly in
the database.
"""
import os
import typing as t

import werkzeug
from flask import request, safe_join, after_this_request, send_from_directory
from werkzeug.exceptions import NotFound
from werkzeug.datastructures import FileStorage

import psef.auth as auth
import psef.files
from psef import app
from psef.auth import APICodes, APIException
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api


@api.route("/files/", methods=['POST'])
@auth.login_required
def post_file() -> JSONResponse[str]:
    """Temporarily store some data on the server.

    .. :quickref: File; Safe a file temporarily on the server.

    .. note::
        The posted data will be removed after 60 seconds.

    :returns: A response with the JSON serialized name of the file as content
              and return code 201.

    :raises APIException: If the request is bigger than the maximum upload
                          size. (REQUEST_TOO_LARGE)
    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    if (
        request.content_length and
        request.content_length > app.config['MAX_UPLOAD_SIZE']):
        raise APIException(
            'Uploaded file is too big.',
            'Request is bigger than maximum upload size of {}.'.format(
                app.config['MAX_UPLOAD_SIZE']
            ), APICodes.REQUEST_TOO_LARGE, 400
        )

    path, name = psef.files.random_file_path('MIRROR_UPLOAD_DIR')

    FileStorage(request.stream).save(path)

    return jsonify(name, status_code=201)


@api.route('/files/<file_name>', methods=['GET'])
@api.route('/files/<file_name>/<name>')
def get_file(
    file_name: str, name: str = 'export'
) -> werkzeug.wrappers.Response:
    """Serve some specific file in the uploads folder.

    .. :quickref: File; Get an uploaded file directory.

    .. note::
        Only files uploaded using :http:post:`/api/v1/files/` may be retrieved.

    :param str file_name: The filename of the file to get.
    :returns: The requested file.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    name = request.args.get('name', name)

    directory = app.config['MIRROR_UPLOAD_DIR']
    error = False

    @after_this_request
    def delete_file(response: t.Any) -> t.Any:
        if not error:
            filename = safe_join(directory, file_name)
            os.unlink(filename)
        return response

    try:
        mimetype = request.args.get('mime', None)
        as_attachment = request.args.get('not_as_attachment', False)
        return send_from_directory(
            directory,
            file_name,
            attachment_filename=name,
            as_attachment=as_attachment,
            mimetype=mimetype
        )
    except NotFound:
        error = True
        raise APIException(
            'The specified file was not found',
            f'The file with name "{file_name}" was not found or is deleted.',
            APICodes.OBJECT_NOT_FOUND,
            404,
        )

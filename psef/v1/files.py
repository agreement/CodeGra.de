"""
This module defines all API routes with the main directory "files". These APIs
serve to upload and download temporary files which are not stored explicitly in
the database.
"""
import os
import typing as t
import threading

import werkzeug
from flask import request, send_from_directory
from flask_login import login_required
from werkzeug.datastructures import FileStorage

import psef.files
from psef import app
from psef.auth import APICodes, APIException
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api


@api.route("/files/", methods=['POST'])
@login_required
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
            'Request is bigger than maximum upload size of {}.'.
            format(app.config['MAX_UPLOAD_SIZE']), APICodes.REQUEST_TOO_LARGE,
            400
        )

    path, name = psef.files.random_file_path()

    FileStorage(request.stream).save(path)

    threading.Timer(60, lambda: os.remove(path))

    return jsonify(name, status_code=201)


@api.route('/files/<file_name>', methods=['GET'])
@login_required
def get_file(file_name) -> werkzeug.wrappers.Response:
    """Serve some specific file in the uploads folder.

    .. :quickref: File; Get a uploaded file directory

    .. note::
        Only files uploaded using :py:func:`post_file` may be retrieved.

    :param str file_name: The filename of the file to get.
    :returns: The requested file.

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    """
    name = request.args.get('name')

    return send_from_directory(
        app.config['UPLOAD_DIR'],
        file_name,
        attachment_filename=name if name else 'export',
        as_attachment=True
    )

import os
import threading

from flask import jsonify, request, send_from_directory
from flask_login import login_required
from werkzeug.datastructures import FileStorage

import psef.files
from psef import app

from . import api


@api.route("/files/", methods=['POST'])
@login_required
def post_file():
    """
    Temporarily store some data on the server.
    The posted data will be removed after 60 seconds.
    """
    if (request.content_length and
            request.content_length > app.config['MAX_UPLOAD_SIZE']):
        raise APIException(
            'Uploaded file is too big.',
            'Request is bigger than maximum upload size of {}.'.format(
                app.config['MAX_UPLOAD_SIZE']), APICodes.REQUEST_TOO_LARGE,
            400)

    path, name = psef.files.random_file_path()

    FileStorage(request.stream).save(path)

    threading.Timer(60, lambda: os.remove(path))

    return jsonify(name), 201


@api.route('/files/<file_name>', methods=['GET'])
@login_required
def get_file(file_name):
    """
    Serve some specific file in the uploads folder
    """
    name = request.args.get('name')

    return send_from_directory(
        app.config['UPLOAD_DIR'],
        file_name,
        attachment_filename=name if name else 'export',
        as_attachment=True)

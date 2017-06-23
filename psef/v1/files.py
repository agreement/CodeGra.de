import os
import threading

from flask import jsonify, request, send_from_directory
from werkzeug.datastructures import FileStorage

import psef.files
from psef import app

from . import api


@api.route("/files/", methods=['POST'])
def post_file():
    """
    Temporarily store some data on the server.
    The posted data will be removed after 60 seconds.
    """
    path, name = psef.files.random_file_path()
    FileStorage(request.stream).save(path)

    threading.Timer(60, lambda: os.remove(path))

    return jsonify(name), 200


@api.route('/files/<file_name>', methods=['GET'])
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

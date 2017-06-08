#!/usr/bin/env python3
import os
import uuid

from flask import jsonify, make_response, request
from psef import app
from werkzeug.utils import secure_filename


@app.route("/api/hello")
def say_hello():
    return jsonify({"msg": "Hello this is Flask."})


@app.route("/api/v1/assignments/<int:assignment_id>"
           "/works/<int:work_id>/file", methods=['POST'])
def upload_file(assignment_id, work_id):
    """
    Saves the file on the server if the request is valid.

    For a request to be valid there needs to be:
        - a file under key 'file' in the request files
        - this file may not be unnamed
    """

    # Check if a valid submission was made
    try:
        file = request.files['file']

        if file.filename == '':
            raise ValueError

    except KeyError:
        return make_response(jsonify({
            "message": "No file was attached under the correct key",
            "description": "There was no file in the http request with the "
            "key 'file'.",
            "code": None
        }), 400)
    except ValueError:
        return make_response(jsonify({
            "message": "There was no file selected or the submitted file has "
                       "no name.",
            "description": "The name of the file in the http request was an "
                           "empty string.",
            "code": None
        }), 400)

    # Save file under random name
    random_file = os.path.join(app.config['UPLOAD_DIR'], str(uuid.uuid4()))
    file.save(random_file)

    # Add entry to database

    return make_response(jsonify({
        "message": "File was successfully uploaded",
        "description": "The file was uploaded and is stored in the uploads "
                       "folder",
        "code": None
    }), 200)

#!/usr/bin/env python3
from psef import app
from flask import jsonify, request
from werkzeug.utils import secure_filename
import os
import uuid


@app.route("/api/hello")
def say_hello():
    return jsonify({"msg": "Hello this is Flask."})


@app.route("/api/upload-code", methods=['POST'])
def upload_code():
    """
    Saves the file on the server if the submission is valid.

    For a submission to be valid there needs to be:
        - a named file under key 'file' in the request files
        - a value under key 'student' in the request headers
        - a value under key 'assignment' in the request headers
    """

    # Check if a valid submission was made
    try:
        file = request.files['file']
        student = int(request.headers['student'])
        assignment = int(request.headers['assignment'])

    except (KeyError, ValueError) as e:
        return "Invalid submission"
    

    # Save file under random name
    random_file = os.path.join(app.config['UPLOAD_DIR'], str(uuid.uuid4()))
    file.save(random_file)

    # Add entry to database

    return "Submission success"

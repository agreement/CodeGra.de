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

	# Check if a file was sent
	try:
		file = request.files['file']
	except KeyError:
		return jsonify(False)

	# Check if file is valid
	if file.filename == '':
		return jsonify(False)
	# if file.content_length > app.config['MAX_CONTENT_LENGTH']:
	# 	return jsonify(False)

	# Save file under random name
	random_file = os.path.join(app.config['UPLOAD_DIR'], str(uuid.uuid4()))
	# file.save(random_file)  # works but pointless at the moment

	# Add entry to database
	pass

	return jsonify(True)

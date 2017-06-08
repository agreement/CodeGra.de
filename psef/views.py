#!/usr/bin/env python3
from psef import app
from flask import jsonify


@app.route("/api/hello")
def say_hello():
    return jsonify({"msg": "Hello this is Flask."})

@app.route("/api/v1/general-feedback/<id>")
def get_general_feedback(id):
	print(id)
	if id == "0":
		return jsonify({
			"id": 0,
			"grade": 8.5,
			"general_feedback": "test feedback voor id nul"
		})
	else:
		return jsonify({
			"id": 0,
			"grade": 6.5,
			"general_feedback": "test feedback"
		})


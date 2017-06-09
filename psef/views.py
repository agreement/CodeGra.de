#!/usr/bin/env python3
from psef import app
from flask import jsonify, request, make_response


@app.route("/api/hello")
def say_hello():
    return jsonify({"msg": "Hello this is Flask."})


@app.route("/api/v1/work/<int:work_id>/general-feedback/",
           methods=['GET', 'PUT'])
def get_general_feedback(work_id):
    if request.method == 'GET':
        if id == 0:
            return jsonify({
                "work_id": 0,
                "grade": 8.5,
                "general_feedback": "test feedback voor id nul"
            })
        else:
            return jsonify({
                "work_id": 0,
                "grade": 6.5,
                "general_feedback": "test feedback"
            })
    elif request.method == 'PUT':
        content = request.get_json()

        # doe iets in de database
        print(content)

        resp = make_response("grade and feedback submitted", 204)
        return resp

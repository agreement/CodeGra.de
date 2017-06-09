#!/usr/bin/env python3
from psef import app
from flask import jsonify, request, make_response




@app.route("/api/v1/code/<id>")
def get_code(id):
    if id == "0":
        return jsonify({
            "lang": "python",
            "code": "def id0func0():\n\treturn 0\n\n\ndef id0func1():\n\t" +
                    "return 1",
            "feedback": {
                "0": "wtf",
            }
        })
    else:
        return jsonify({
            "lang": "c",
            "code": "void\nsome_func(void) {}\n\nvoid other_func(int x)" +
                    "{\n\treturn 2 * x;\n}",
            "feedback": {
                "1": "slechte naam voor functie",
                "3": "niet veel beter..."
            }
        })


@app.route("/api/v1/dir/<path>")
def get_dir_contents(path):
    return jsonify(dir_contents(path))


def dir_contents(path):
    return {
        "name": path,
        "entries": [
            {
                "name": "a",
                "entries": [
                    {"name": "a_1", "id": 0, },
                    {"name": "a_2", "id": 1, },
                    {
                        "name": "a_3",
                        "entries": [
                            {"name": "a_3_1", "id": 2},
                        ],
                    },
                ],
            },
            {"name": "b", "id": 3},
            {"name": "c", "id": 4},
            {"name": "d", "id": 5},
        ]
    }


@app.route("/api/v1/submission/<submission_id>")
def get_submission(submission_id):
    return jsonify({
        "title": "Assignment 1",
        "fileTree": dir_contents("abc"),
    })


@app.route("/api/v1/submission/<submission_id>/general-feedback", methods=['GET', 'PUT'])
def get_general_feedback(submission_id):
    if request.method == 'GET':
    	if id == 0:
    		return jsonify({
    			"grade": 8.5,
    			"feedback": "test feedback voor id nul"
    		})
    	else:
    		return jsonify({
    			"grade": 6.5,
    			"feedback": "test feedback"
    		})
    elif request.method == 'PUT':
        content = request.get_json()

        # doe iets in de database
        print(content)

        resp = make_response("grade and feedback submitted", 204)
        return resp

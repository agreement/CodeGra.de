#!/usr/bin/env python3
from psef import app
from flask import jsonify


@app.route("/api/v1/students/<student_id>/assignments/<assignment_id>")
def get_student_assignment(student_id, assignment_id):
    return jsonify({
        "title": "Assignment 1",
        "due_date": "1497020367",
        "fileTree": dir_contents("abc"),
    })


@app.route("/api/v1/code/<id>")
def get_code(id):
    if id == "0":
        return jsonify({
            "id": 0,
            "lang": "python",
            "code": "def id0func0():\n\treturn 0\n\n\ndef id0func1():\n\t" +
                    "return 1",
            "feedback": {
                "0": "wtf",
            }
        })
    else:
        return jsonify({
            "id": id,
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

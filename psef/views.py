#!/usr/bin/env python3
from psef import app
from flask import jsonify


@app.route("/api/hello")
def say_hello():
    return jsonify({"msg": "Hello this is Flask."})


@app.route("/api/dir/<path>")
def get_dir_contents(path):
    return jsonify({
        "path": path,
        "name": "path",
        "entries": [
            {
                "name": "a",
                "entries": [
                    { "name": "a_1", },
                    { "name": "a_2", },
                    {
                        "name": "a_3",
                        "entries": [
                            { "name": "a_3_1", },
                        ],
                    },
                ],
            },
            { "name": "b", },
            { "name": "c", },
            { "name": "d", },
        ]
    })

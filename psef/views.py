#!/usr/bin/env python3
from flask import jsonify

from psef import app


@app.route("/api/hello")
def say_hello():
    return jsonify({"msg": "Hello this is Flask."})

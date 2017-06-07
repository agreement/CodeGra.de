#!/usr/bin/env python3
from psef import app
from flask import jsonify


@app.route("/api/hello")
def say_hello():
    return jsonify({"msg": "Hello this is Flask."})

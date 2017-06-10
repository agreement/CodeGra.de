#!/usr/bin/env python3
from psef import app
from flask import jsonify, request, abort
from flask_login import login_user, UserMixin


class User(UserMixin):

    def __init__(self, id):
        self.id = id


@app.route("/api/hello")
def say_hello():
    return jsonify({"msg": "Hello this is Flask."})


@app.route("/api/login", methods=["post"])
def login():
    data = request.get_json()

    # TODO: Some authentication here

    user = User(data["email"])

    # Login and validate the user.
    # user should be an instance of your `User` class
    login_user(user)

    next = request.args.get('next')

    return jsonify({"success": True})

#!/usr/bin/env python3
from flask import jsonify, request, session, make_response
from flask_login import login_user, logout_user

import psef.auth as auth
import psef.models as models
from psef import db, app
from psef.errors import APICodes, APIException


@app.route("/api/v1/code/<int:id>")
def get_code(id):
    # Code not used yet:

    code = db.session.query(models.File).filter(  # NOQA: F841
        models.File.id == id).first()
    line_feedback = {}
    for comment in db.session.query(models.Comment).filter(
            models.Comment.file_id == id):
        line_feedback[str(comment.line)] = comment.comment
    print(line_feedback)

    # TODO: Return JSON following API
    return jsonify(
        lang="python",
        code="def id0func0():\n\treturn 0\n\n\n" +
        "def id0func1():\n\t return 1",
        feedback=line_feedback)


@app.route("/api/v1/code/<int:id>/comment/<int:line>", methods=['PUT'])
def put_comment(id, line):
    content = request.get_json()

    comment = db.session.query(models.Comment).filter(
        models.Comment.file_id == id, models.Comment.line == line).first()
    if not comment:
        # TODO: User id 0 for now, change later on
        db.session.add(
            models.Comment(
                file_id=id, user_id=0, line=line, comment=content['comment']))
    else:
        comment.comment = content['comment']

    db.session.commit()

    return ('', 204)


@app.route("/api/v1/dir/<path>")
def get_dir_contents(path):
    return jsonify(dir_contents(path))


def dir_contents(path):
    return {
        "name":
        path,
        "entries": [
            {
                "name":
                "a",
                "entries": [
                    {
                        "name": "a_1",
                        "id": 0,
                    },
                    {
                        "name": "a_2",
                        "id": 1,
                    },
                    {
                        "name": "a_3",
                        "entries": [
                            {
                                "name": "a_3_1",
                                "id": 2
                            },
                        ],
                    },
                ],
            },
            {
                "name": "b",
                "id": 3
            },
            {
                "name": "c",
                "id": 4
            },
            {
                "name": "d",
                "id": 5
            },
        ]
    }


@app.route("/api/v1/submission/<submission_id>")
def get_submission(submission_id):
    return jsonify({
        "title": "Assignment 1",
        "fileTree": dir_contents("abc"),
    })


@app.route(
    "/api/v1/submission/<submission_id>/general-feedback",
    methods=['GET', 'PUT'])
def get_general_feedback(submission_id):
    if request.method == 'GET':
        if id == 0:
            return jsonify({
                "grade": 8.5,
                "feedback": "test feedback voor id nul"
            })
        else:
            return jsonify({"grade": 6.5, "feedback": "test feedback"})
    elif request.method == 'PUT':
        content = request.get_json()

        # Here you should connect to the database
        print(content)

        resp = make_response("grade and feedback submitted", 204)
        return resp


@app.route("/api/v1/login", methods=["POST"])
def login():
    data = request.get_json()

    if 'email' not in data or 'password' not in data:
        raise APIException('Email and passwords are required fields',
                           'Email or password was missing from the request',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    user = models.User.query.filter_by(email=data['email']).first()
    if user is None or user.password != data['password']:
        raise APIException(
            'The supplied email or password is wrong.',
            ('The user with email {} does not exist ' +
             'or has a different password').format(data['email']),
            APICodes.LOGIN_FAILURE, 400)

    if not login_user(user):
        raise APIException('User is not active', (
            'The user with id "{}" is not active any more').format(user.id),
                           APICodes.INACTIVE_USER, 403)
    return jsonify({
        "id": user.id,
        "name": user.name,
    })


@app.route("/api/v1/logout", methods=["POST"])
def logout():
    logout_user()
    return '', 204

#!/usr/bin/env python3
from flask import jsonify, request, make_response
from flask_login import UserMixin, login_user, logout_user

from psef import app, db
from psef.models import *
from flask_login import UserMixin, login_user

@app.route("/api/v1/code/<int:id>")
def get_code(id):
    # Code not used yet:
    code = db.session.query(File).filter(File.id==id).first()
    line_feedback = {}
    for comment in db.session.query(Comment).filter(Comment.file_id==id):
        line_feedback[str(comment.line)] = comment.comment
    print(line_feedback)
    # TODO: Return JSON following API
    #if code != None:
    return jsonify(lang="python",
                   code="def id0func0():\n\treturn 0\n\n\n" +
                        "def id0func1():\n\t return 1",
                   feedback=line_feedback)

@app.route("/api/v1/code/<int:id>/comment/<int:line>", methods=['PUT'])
def put_comment(id, line):
    if request.method == 'PUT':
        content = request.get_json()

        comment = db.session.query(Comment).filter(Comment.file_id==id,
                                                   Comment.line==line).first()
        if not comment:
            # TODO: User id 0 for now, change later on
            db.session.add(Comment(file_id=id,
                                   user_id=0,
                                   line=line,
                                   comment=content['comment']))
        else:
            comment.comment = content['comment']

        db.session.commit()

        return make_response("Comment updated or inserted!", 204)
    else:
        return make_response("Request not valid!", 400)


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


@app.route("/api/v1/submission/<submission_id>/general-feedback",
           methods=['GET', 'PUT'])
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

        # Here you should connect to the database
        print(content)

        resp = make_response("grade and feedback submitted", 204)
        return resp

@app.route("/api/v1/login", methods=["POST"])
def login():
    class User(UserMixin):

        def __init__(self, id):
            self.id = id

    data = request.get_json()

    # TODO: Some authentication here
    # TODO: Get integer user id from email
    user = User(1)

    login_user(user)
    return jsonify({
        "success": True,
        "id": 1,
        "name": data["email"].partition("@")[0]
    })


@app.route("/api/v1/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({
        "success": True
    })

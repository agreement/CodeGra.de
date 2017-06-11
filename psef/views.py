#!/usr/bin/env python3
from flask import jsonify, request, make_response
from flask_login import UserMixin, login_user, logout_user

import psef.auth as auth
import psef.files
import psef.models as models
from psef import db, app
from psef.errors import APICodes, APIException
from psef.models import *


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
    return jsonify({"success": True})


@app.route("/api/v1/works/<int:work_id>/file", methods=['POST'])
def upload_file(work_id):
    """
    Saves the files on the server if the request is valid.

    For a request to be valid there needs to be:
        - at least one file under key 'file' in the request files
        - all files must be named
    """

    # Check if a valid submission was made
    files = []

    if (request.content_length and
            request.content_length > app.config['MAX_UPLOAD_SIZE']):
        raise APIException('Uploaded files are too big.', (
            'Request is bigger than maximum ' +
            'upload size of {}.').format(app.config['MAX_UPLOAD_SIZE']),
                           APICodes.REQUEST_TOO_LARGE, 400)

    if len(request.files) == 0:
        raise APIException("No file in HTTP request.",
                           "There was no file in the HTTP request.",
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    for key, file in request.files.items():
        if not key.startswith('file'):
            raise APIException('The parameter name should start with "file".',
                               'Expected ^file.*$ got {}.'.format(key),
                               APICodes.INVALID_PARAM, 400)

        if file.filename == '':
            raise APIException('The filename should not be empty.',
                               'Got an empty filename for key {}'.format(key),
                               APICodes.INVALID_PARAM, 400)

        files.append(file)

    work = models.Work.query.get(work_id)
    if work is None:
        raise APIException(
            'Work not found',
            'The work with code {} was not found'.format(work_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)
    auth.ensure_permission('can_submit_own_work', work.assignment.course.id)

    tree = psef.files.process_files(files)
    work.add_file_tree(tree)

    return ('', 204)

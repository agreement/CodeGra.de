#!/usr/bin/env python3
from flask import jsonify, request
from flask_login import login_user, logout_user, current_user, login_required

import psef.auth as auth
import psef.files
import psef.models as models
from psef import db, app
from psef.errors import APICodes, APIException


@app.route("/api/v1/code/<int:id>")
def get_code(file_id):
    # Code not used yet:

    code = db.session.query(models.File).filter(  # NOQA: F841
        models.File.id == id).first()
    line_feedback = {}
    for comment in db.session.query(models.Comment).filter_by(
            file_id=file_id).all():
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

    comment = db.session.query(models.Comment).filter_by(
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

        return ('', 204)


@app.route("/api/v1/login", methods=["POST"])
def login():
    data = request.get_json()

    if 'email' not in data or 'password' not in data:
        raise APIException('Email and passwords are required fields',
                           'Email or password was missing from the request',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    user = db.session.query(models.User).filter_by(email=data['email']).first()

    # TODO: Use bcrypt password validation (as soon as we got that)
    # TODO: Return error whether user or password is wrong
    if user is None or user.password != data['password']:
        raise APIException('The supplied email or password is wrong.', (
            'The user with email {} does not exist ' +
            'or has a different password').format(data['email']),
                           APICodes.LOGIN_FAILURE, 400)

    if not login_user(user, remember=True):
        raise APIException('User is not active', (
            'The user with id "{}" is not active any more').format(user.id),
                           APICodes.INACTIVE_USER, 403)

    return me()


@app.route("/api/v1/login", methods=["GET"])
@login_required
def me():
    return jsonify({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }), 200


@app.route("/api/v1/logout", methods=["POST"])
def logout():
    logout_user()
    return '', 204


@app.route("/api/v1/assignments/<int:assignment_id>/work", methods=['POST'])
def upload_work(assignment_id):
    """
    Saves the work on the server if the request is valid.

    For a request to be valid there needs to be:
        - at least one file starting with key 'file' in the request files
        - all files must be named
    """

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

    assignment = models.Assignment.query.get(assignment_id)
    if assignment is None:
        raise APIException(
            'Assignment not found',
            'The assignment with code {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_submit_own_work', assignment.course.id)

    work = models.Work(assignment_id=assignment_id, user_id=0)
    db.session.add(work)

    tree = psef.files.process_files(files)
    work.add_file_tree(db, tree)

    db.session.commit()

    return ('', 204)

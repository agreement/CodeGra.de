#!/usr/bin/env python3
import os
from random import shuffle
from itertools import cycle

from flask import jsonify, request, send_file, make_response, after_this_request
from flask_login import login_user, logout_user, current_user, login_required

import psef.auth as auth
import psef.files
import psef.models as models
from psef import db, app
from psef.errors import APICodes, APIException
from sqlalchemy_utils.functions import dependent_objects


@app.route("/api/v1/file/metadata/<int:file_id>", methods=['GET'])
def get_file_metadata(file_id):
    file = db.session.query(models.File).filter(
        models.File.id == file_id).first()

    return jsonify({"name": file.name, "extension": file.extension})


@app.route("/api/v1/binary/<int:file_id>")
def get_binary(file_id):
    file = db.session.query(models.File).filter(
        models.File.id == file_id).first()

    file_data = psef.files.get_binary_contents(file)
    response = make_response(file_data)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=' + file.name

    return response


@app.route("/api/v1/code/<int:file_id>", methods=['GET'])
def get_code(file_id):
    code = db.session.query(models.File).get(file_id)
    assig = code.work.assignment
    line_feedback = {}

    if code is None:
        raise APIException('File not found',
                           'The file with id {} was not found'.format(file_id),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)

    if (code.work.user.id != current_user.id):
        auth.ensure_permission('can_view_files',
                               code.work.assignment.course.id)

    try:
        auth.ensure_can_see_grade(code.work)
        for comment in db.session.query(models.Comment).filter_by(
                file_id=file_id).all():
            line_feedback[str(comment.line)] = comment.comment
    except auth.PermissionException:
        line_feedback = {}

    # TODO: Return JSON following API
    return jsonify(
        lang=code.extension,
        code=psef.files.get_file_contents(code),
        feedback=line_feedback)


@app.route("/api/v1/code/<int:id>/comments/<int:line>", methods=['PUT'])
def put_comment(id, line):
    """
    Create or change a single line comment of a code file
    """
    content = request.get_json()

    comment = db.session.query(models.Comment).filter(
        models.Comment.file_id == id,
        models.Comment.line == line).one_or_none()
    if not comment:
        file = db.session.query(models.File).get(id)
        auth.ensure_permission('can_grade_work',
                               file.work.assignment.course.id)
        db.session.add(
            models.Comment(
                file_id=id,
                user_id=current_user.id,
                line=line,
                comment=content['comment']))
    else:
        auth.ensure_permission('can_grade_work',
                               comment.file.work.assignment.course.id)
        comment.comment = content['comment']

    db.session.commit()

    return ('', 204)


@app.route("/api/v1/code/<int:id>/comments/<int:line>", methods=['DELETE'])
def remove_comment(id, line):
    """
    Removes the comment on line X if the request is valid.

    Raises APIException:
        - If no comment on line X was found
    """
    comment = db.session.query(models.Comment).filter(
        models.Comment.file_id == id,
        models.Comment.line == line).one_or_none()

    if comment:
        auth.ensure_permission('can_grade_work',
                               comment.file.work.assignment.course.id)
        db.session.delete(comment)
        db.session.commit()
    else:
        raise APIException('Feedback comment not found',
                           'The comment on line {} was not found'.format(line),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)
    return ('', 204)


@app.route("/api/v1/submissions/<int:submission_id>/files/", methods=['GET'])
def get_dir_contents(submission_id):
    """
    Return the object containing all the files of submission X

    Raises APIException:
        - If there are no files to be returned
        - If the submission id does not match the work id
        - If the file with code {} is not a directory
    """
    work = models.Work.query.get(submission_id)
    if work is None:
        raise APIException(
            'Submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    if (work.user.id != current_user.id):
        auth.ensure_permission('can_view_files', work.assignment.course.id)

    file_id = request.args.get('file_id')
    if file_id:
        file = models.File.query.get(file_id)
        if file is None:
            raise APIException(
                'File not found',
                'The file with code {} was not found'.format(file_id),
                APICodes.OBJECT_ID_NOT_FOUND, 404)
        if (file.work.id != submission_id):
            raise APIException(
                'Incorrect URL',
                'The identifiers in the URL do no match those related to the '
                'file with code {}'.format(file.id), APICodes.INVALID_URL, 400)
    else:
        file = models.File.query.filter(models.File.work_id == submission_id,
                                        models.File.parent_id == None).one()

    if not file.is_directory:
        raise APIException(
            'File is not a directory',
            'The file with code {} is not a directory'.format(file.id),
            APICodes.OBJECT_WRONG_TYPE, 400)

    dir_contents = jsonify(file.list_contents())

    return (dir_contents, 200)


@app.route("/api/v1/assignments/", methods=['GET'])
@login_required
def get_student_assignments():
    """
    Get all the student assignments that the current user can see.
    """
    perm = models.Permission.query.filter_by(
        name='can_see_assignments').first()
    courses = []
    for course_role in current_user.courses.values():
        if course_role.has_permission(perm):
            courses.append(course_role.course_id)
    if courses:
        return jsonify([
            assignment.to_dict()
            for assignment in models.Assignment.query.filter(
                models.Assignment.course_id.in_(courses)).all()
        ])
    else:
        return (jsonify([]), 204)


@app.route("/api/v1/assignments/<int:assignment_id>", methods=['GET'])
def get_assignment(assignment_id):
    """
    Return student assignment X if the user permission is valid.
    """
    assignment = models.Assignment.query.get(assignment_id)
    auth.ensure_permission('can_see_assignments', assignment.course_id)
    if assignment is None:
        raise APIException(
            'Assignment not found',
            'The assignment with id {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)
    else:
        return jsonify(assignment.to_dict())


@app.route('/api/v1/assignments/<int:assignment_id>', methods=['PATCH'])
def update_assignment(assignment_id):
    assig = models.Assignment.query.get(assignment_id)
    if assig is None:
        raise APIException(
            'Assignment not found',
            'The assignment with id "{}" was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_manage_course', assig.course_id)

    content = request.get_json()

    print(content)
    if 'state' in content:
        if content['state'] not in ['hidden', 'open', 'done']:
            raise APIException(
                'Invalid new state',
                'The state {} is not a valid state'.format(content['state']),
                APICodes.INVALID_PARAM, 400)
        if content['state'] == 'open':
            assig.state = 'submitting'
        else:
            assig.state = content['state']

    if 'name' in content:
        if not isinstance(content['name'], str):
            raise APIException(
                'The name of an assignment should be a a string',
                '{} is not a string'.format(content['name']),
                APICodes.INVALID_PARAM, 400)
        assig.name = content['name']

    # TODO also make it possible to update the close date of an assignment

    db.session.commit()

    return '', 204


@app.route(
    '/api/v1/assignments/<int:assignment_id>/submissions/', methods=['GET'])
def get_all_works_for_assignment(assignment_id):
    """
    Return all works for assignment X if the user permission is valid.
    """
    assignment = models.Assignment.query.get(assignment_id)
    if current_user.has_permission(
            'can_see_others_work', course_id=assignment.course_id):
        obj = models.Work.query.filter_by(assignment_id=assignment_id)
    else:
        obj = models.Work.query.filter_by(
            assignment_id=assignment_id, user_id=current_user.id)

    res = obj.order_by(models.Work.created_at.desc()).all()

    if 'csv' in request.args:
        if assignment.state != models.AssignmentStateEnum.done:
            auth.ensure_permission('can_see_grade_before_open',
                                   assignment.course.id)
        headers = [
            'id', 'user_name', 'user_id', 'state', 'edit', 'grade', 'comment',
            'created_at'
        ]
        file = psef.files.create_csv_from_rows([headers] + [[
            work.id, work.user.name
            if work.user else "Unknown", work.user_id, work.grade,
            work.comment, work.created_at.strftime("%d-%m-%Y %H:%M")
        ] for work in res])

        @after_this_request
        def remove_file(response):
            os.remove(file)
            return response

        return send_file(
            file, attachment_filename=request.args['csv'], as_attachment=True)

    out = []
    for work in res:
        item = {
            'id': work.id,
            'user_name': work.user.name if work.user else "Unknown",
            'user_id': work.user_id,
            'edit': work.edit,
            'created_at': work.created_at.strftime("%d-%m-%Y %H:%M"),
        }
        try:
            auth.ensure_can_see_grade(work)
            item['grade'] = work.grade
            item['comment'] = work.comment
        except auth.PermissionException:
            item['grade'] = '-'
            item['comment'] = '-'
        finally:
            out.append(item)

    return jsonify(out)


@app.route("/api/v1/submissions/<int:submission_id>", methods=['GET'])
@login_required
def get_submission(submission_id):
    """
    Return submission X if the user permission is valid.

    Raises APIException:
        - If submission X was not found
    """
    work = db.session.query(models.Work).get(submission_id)

    if work:
        auth.ensure_can_see_grade(work)

        return jsonify({
            'id': work.id,
            'user_id': work.user_id,
            'edit': work.edit,
            'grade': work.grade,
            'comment': work.comment,
            'created_at': work.created_at,
        })
    else:
        raise APIException(
            'Work submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)


@app.route("/api/v1/submissions/<int:submission_id>", methods=['PATCH'])
def patch_submission(submission_id):
    """
    Update submission X if it already exists and if the user permission is valid.

    Raises APIException:
        - If submission X was not found
        - request file does not contain grade and/or feedback
        - request file grade is not a float
    """
    work = db.session.query(models.Work).get(submission_id)
    content = request.get_json()

    if not work:
        raise APIException(
            'Submission not found',
            'The submission with code {} was not found'.format(submission_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_grade_work', work.assignment.course.id)
    if 'grade' not in content or 'feedback' not in content:
        raise APIException('Grade or feedback not provided',
                           'Grade and or feedback fields missing in sent JSON',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    if not isinstance(content['grade'], float):
        try:
            content['grade'] = float(content['grade'])
        except ValueError:
            raise APIException(
                'Grade submitted not a number',
                'Grade for work with id {} not a number'.format(submission_id),
                APICodes.INVALID_PARAM, 400)

    work.grade = content['grade']
    work.comment = content['feedback']
    db.session.commit()
    return ('', 204)


@app.route('/api/v1/courses/<int:course_id>/assignments/', methods=['GET'])
def get_all_course_assignments(course_id):
    auth.ensure_permission('can_see_assignments', course_id)

    course = models.Course.query.get(course_id)
    if course is None:
        return APIException('Specified course not found',
                            'The course {} was not found'.format(course_id),
                            APICodes.OBJECT_ID_NOT_FOUND, 404)

    res = [assig.to_dict() for assig in course.assignments]
    res.sort(key=lambda item: item['date'])
    return jsonify(res)


@app.route("/api/v1/login", methods=["POST"])
def login():
    """
    Login a user if the request is valid.

    Raises APIException:
        - request file does not contain email and/or password
        - request file contains invalid login credentials
        - request file contains inactive login credentials
    """
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
    return (jsonify({
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email
    }), 200)


@app.route("/api/v1/logout", methods=["POST"])
def logout():
    logout_user()
    return ('', 204)


@app.route(
    "/api/v1/assignments/<int:assignment_id>/submission", methods=['POST'])
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

    work = models.Work(assignment_id=assignment_id, user_id=current_user.id)
    db.session.add(work)

    tree = psef.files.process_files(files)
    work.add_file_tree(db.session, tree)

    db.session.commit()

    return (jsonify({'id': work.id}), 201)


@app.route('/api/v1/assignments/<int:assignment_id>/divide', methods=['PATCH'])
def divide_assignments(assignment_id):
    assignment = models.Assignment.query.get(assignment_id)
    auth.ensure_permission('can_manage_course', assignment.course.id)
    if not assignment:
        raise APIException(
            'Assignment not found',
            'The assignment with code {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    content = request.get_json()

    if 'graders' not in content or not isinstance(
            content['graders'], list) or len(content['graders']) == 0:
        raise APIException('List of assigned graders is required',
                           'List of assigned graders is required',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    submissions = assignment.get_all_latest_submissions()

    if not submissions:
        raise APIException(
            'No submissions found',
            'No submissions found for assignment {}'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    users = models.User.query.filter(
        models.User.id.in_(content['graders'])).all()
    if len(users) != len(content['graders']):
        raise APIException('Invalid grader id given',
                           'Invalid grader (=user) id given',
                           APICodes.INVALID_PARAM, 400)

    for grader in users:
        if not grader.has_permission('can_grade_work', assignment.course.id):
            raise APIException('Selected grader has no permission to grade',
                               'Selected grader has no permission to grade',
                               APICodes.INVALID_PARAM, 400)

    shuffle(submissions)
    shuffle(content['graders'])
    for submission, grader in zip(submissions, cycle(content['graders'])):
        submission.assigned_to = grader

    db.session.commit()
    return ('', 204)


@app.route('/api/v1/assignments/<int:assignment_id>/graders', methods=['GET'])
def get_all_graders(assignment_id):
    assignment = models.Assignment.query.get(assignment_id)
    auth.ensure_permission('can_manage_course', assignment.course.id)

    if not assignment:
        raise APIException(
            'Assignment not found',
            'The assignment with code {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    permission = db.session.query(models.Permission.id).filter(
        models.Permission.name == 'can_grade_work').as_scalar()

    us = db.session.query(
        models.User.id, models.User.name, models.user_course.c.course_id).join(
            models.user_course,
            models.User.id == models.user_course.c.user_id).subquery('us')
    per = db.session.query(models.course_permissions.c.course_role_id).join(
        models.CourseRole,
        models.CourseRole.id == models.course_permissions.c.course_role_id
    ).filter(
        models.course_permissions.c.permission_id == permission,
        models.CourseRole.course_id == assignment.course_id).subquery('per')
    result = db.session.query(us.c.name, us.c.id).join(
        per, us.c.course_id == per.c.course_role_id).order_by(us.c.name).all()

    divided = set(r[0]for r in
        db.session.query(models.Work.assigned_to).filter(
        models.Work.assignment_id == assignment_id).group_by(
            models.Work.assigned_to).all())

    return jsonify([{
        'id': res[1],
        'name': res[0],
        'divided': res[1] in divided
    } for res in result])


@app.route('/api/v1/permissions/', methods=['GET'])
@login_required
def get_permissions():
    if 'course_id' in request.args:
        try:
            course_id = int(request.args['course_id'])
        except ValueError:
            raise APIException(
                'The specified course id was invalid',
                'The course id should be a number but '
                '{} is not a number'.format(request.args['course_id']),
                APICodes.INVALID_PARAM, 400)
    else:
        course_id = None

    if 'permission' in request.args:
        perm = request.args['permission']
        try:
            return jsonify(current_user.has_permission(perm, course_id))
        except KeyError:
            raise APIException('The specified permission does not exist',
                               'The permission '
                               '"{}" is not real permission'.format(perm),
                               APICodes.OBJECT_NOT_FOUND, 404)
    else:
        return (jsonify(current_user.get_all_permissions(course_id=course_id)),
                200)


@app.route('/api/v1/snippets/', methods=['GET'])
@auth.permission_required('can_use_snippets')
def get_snippets():
    res = models.Snippet.get_all_snippets(current_user)
    if res:
        return jsonify({r.key: {'value': r.value, 'id': r.id} for r in res})
    else:
        return ('', 204)


@app.route('/api/v1/snippet', methods=['PUT'])
@auth.permission_required('can_use_snippets')
def add_snippet():
    content = request.get_json()
    if 'key' not in content or 'value' not in content:
        raise APIException(
            'Not all required keys were in content',
            'The given content ({}) does  not contain "key" and "value"'.
            format(content), APICodes.MISSING_REQUIRED_PARAM, 400)

    snippet = models.Snippet.query.filter_by(
        user_id=current_user.id, key=content['key']).first()
    if snippet is None:
        snippet = models.Snippet(
            key=content['key'], value=content['value'], user=current_user)
        db.session.add(snippet)
    else:
        snippet.value = content['value']
    db.session.commit()

    return (jsonify({'id': snippet.id}), 201)


@app.route('/api/v1/snippets/<int:snippet_id>', methods=['PATCH'])
@auth.permission_required('can_use_snippets')
def patch_snippet(snippet_id):
    content = request.get_json()
    if 'key' not in content or 'value' not in content:
        raise APIException(
            'Not all required keys were in content',
            'The given content ({}) does  not contain "key" and "value"'.
            format(content), APICodes.MISSING_REQUIRED_PARAM, 400)
    snip = models.Snippet.query.get(snippet_id)
    if snip is None:
        raise APIException('Snippet not found',
                           'The snippet with id {} was not found'.format(snip),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)
    if snip.user.id != current_user.id:
        raise APIException(
            'The given snippet is not your snippet',
            'The snippet "{}" does not belong to user "{}"'.format(
                snip.id, current_user.id), APICodes.INCORRECT_PERMISSION, 403)

    snip.key = content['key']
    snip.value = content['value']
    db.session.commit()

    return ('', 204)


@app.route('/api/v1/snippets/<int:snippet_id>', methods=['DELETE'])
@auth.permission_required('can_use_snippets')
def delete_snippets(snippet_id):
    snip = models.Snippet.query.get(snippet_id)
    if snip is None:
        raise APIException(
            'The specified snippet does not exits',
            'The snipped with id "{}" does not exist'.format(snippet_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)
    elif snip.user_id != current_user.id:
        raise APIException(
            'The given snippet is not your snippet',
            'The snippet "{}" does not belong to user "{}"'.format(
                snip.id, current_user.id), APICodes.INCORRECT_PERMISSION, 403)
    else:
        db.session.delete(snip)
        db.session.commit()
        return ('', 204)
    pass

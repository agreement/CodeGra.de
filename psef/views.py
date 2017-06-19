#!/usr/bin/env python3
import os
import threading

from flask import jsonify, request, send_file, make_response, after_this_request
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy.orm import subqueryload

import psef.auth as auth
import psef.files
import psef.models as models
import psef.linters as linters
from psef import db, app
from psef.errors import APICodes, APIException


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
    linter_feedback = {}

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
        for comment in db.session.query(models.LinterComment).filter_by(
                file_id=file_id).all():
            if str(comment.line) not in linter_feedback:
                linter_feedback[str(comment.line)] = {}
            linter_feedback[str(comment.line)][comment.linter.tester.name] = {
                'code': comment.linter_code,
                'msg': comment.comment
            }
    except auth.PermissionException:
        line_feedback = {}
        linter_feedback = {}

    return jsonify(
        lang=code.extension,
        code=psef.files.get_file_contents(code),
        feedback=line_feedback,
        linter_feedback=linter_feedback)


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
        return (jsonify([{
            'id':
            assignment.id,
            'state':
            assignment.state,
            'date':
            assignment.created_at.strftime('%d-%m-%Y %H:%M'),
            'name':
            assignment.name,
            'course_name':
            assignment.course.name,
            'course_id':
            assignment.course_id,
        }
                         for assignment in models.Assignment.query.filter(
                             models.Assignment.course_id.in_(courses)).all()]),
                200)
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
        return (jsonify({
            'name': assignment.name,
            'state': assignment.state,
            'description': assignment.description,
            'course_name': assignment.course.name,
            'course_id': assignment.course_id,
        }), 200)


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
    Update submission X if it already exists and if the user permission is
    valid.

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
        db.session.add(
            models.Snippet(
                key=content['key'], value=content['value'], user=current_user))
    else:
        snippet.value = content['value']
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


@app.route('/api/v1/linter_comments/<token>', methods=['PUT'])
def put_linter_comment(token):
    # TODO: Fix error messages
    unit = models.LinterInstance.query.get(token)
    content = request.get_json()
    if 'crashed' in content:
        unit.state = models.LinterState.crashed
        db.session.commit()
        return '', 204
    unit.state = models.LinterState.done
    name = content['name']

    with db.session.no_autoflush:
        if unit is not None:
            for file_id, feedbacks in content['files'].items():
                f = models.File.query.get(file_id)
                if f is None or f.work_id != unit.work_id:
                    pass

                # TODO: maybe simply delete all comments for this linter on
                # this file
                comments = models.LinterComment.query.filter_by(
                    linter_id=unit.id, file_id=file_id).all()
                lookup = {c.line: c for c in comments}

                for line, code, feedback in feedbacks:
                    if line in lookup:
                        lookup[line].comment = feedback
                        lookup[line].linter_code = code
                    else:
                        c = models.LinterComment(
                            file_id=file_id,
                            line=line,
                            linter_code=code,
                            linter_id=unit.id,
                            comment=feedback)
                        lookup[line] = c
                        db.session.add(c)

    db.session.commit()
    return '', 204


@app.route('/api/v1/assignments/<int:assignment_id>/linters/', methods=['GET'])
def get_linters(assignment_id):
    res = {}
    for name, opts in linters.get_all_linters().items():
        linter = models.AssignmentLinter.query.filter_by(
            assignment_id=assignment_id, name=name).first()

        if linter:
            running = db.session.query(
                models.LinterInstance.query.filter(
                    models.LinterInstance.tester_id == linter.id,
                    models.LinterInstance.state == models.LinterState.running)
                .exists()).scalar()
            crashed = db.session.query(
                models.LinterInstance.query.filter(
                    models.LinterInstance.tester_id == linter.id,
                    models.LinterInstance.state == models.LinterState.crashed)
                .exists()).scalar()
            if running:
                state = models.LinterState.running
            elif crashed:
                state = models.LinterState.crashed
            else:
                state = models.LinterState.done
            opts['id'] = linter.id
        else:
            state = -1
        opts['state'] = state
        res[name] = opts
    return jsonify(res)


@app.route('/api/v1/linters/<linter_id>', methods=['DELETE'])
def delete_linter_output(linter_id):
    linter = models.AssignmentLinter.query.get(linter_id)
    db.session.delete(linter)
    db.session.commit()
    return '', 204


@app.route('/api/v1/linters/<linter_id>', methods=['GET'])
def get_linter_state(linter_id):
    res = []
    any_working = False
    crashed = False
    for test in models.AssignmentLinter.query.get(linter_id).tests:
        if test.state == models.LinterState.running:
            any_working = True
        elif test.state == models.LinterState.crashed:
            crashed = True
        res.append((test.work.user.name, test.state))
    res.sort(key=lambda el: el[0])
    return jsonify({
        'children': res,
        'done': not any_working,
        'crashed': not any_working and crashed,
        'id': linter_id,
    })


@app.route('/api/v1/assignments/<int:assignment_id>/linter', methods=['POST'])
def start_linting(assignment_id):
    content = request.get_json()

    if db.session.query(
            models.LinterInstance.query.filter(
                models.AssignmentLinter.assignment_id == assignment_id,
                models.AssignmentLinter.name == content['name'])
            .exists()).scalar():
        # TODO Error
        return

    res = models.AssignmentLinter.create_tester(assignment_id, content['name'])
    db.session.add(res)
    db.session.commit()

    codes = []
    tokens = []
    try:
        for test in res.tests:
            tokens.append(test.id)
            codes.append(
                models.File.query.options(subqueryload('children')).filter_by(
                    parent=None, work_id=test.work_id).first())
            runner = linters.LinterRunner(
                linters.get_linter_by_name(content['name']), content['cfg'])
            thread = threading.Thread(
                target=runner.run,
                args=(codes, tokens, '{}api/v1/linter_comments/{}'.format(
                    request.url_root, '{}')))
    except:
        for test in res.tests:
            test.state = models.LinterState.crashed
        db.session.commit()

    thread.start()
    return get_linter_state(res.id)

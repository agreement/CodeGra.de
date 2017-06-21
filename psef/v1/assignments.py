import os
import threading
from random import shuffle
from itertools import cycle

from flask import jsonify, request, send_file, after_this_request
from flask_login import current_user, login_required

import psef.auth as auth
import psef.files
import psef.models as models
import psef.linters as linters
from psef import db, app
from psef.errors import APICodes, APIException

from . import api


@api.route("/assignments/", methods=['GET'])
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


@api.route("/assignments/<int:assignment_id>", methods=['GET'])
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


@api.route('/assignments/<int:assignment_id>', methods=['PATCH'])
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


@api.route("/assignments/<int:assignment_id>/submission", methods=['POST'])
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


@api.route('/assignments/<int:assignment_id>/divide', methods=['PATCH'])
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


@api.route('/assignments/<int:assignment_id>/graders', methods=['GET'])
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

    divided = set(r[0]
                  for r in db.session.query(models.Work.assigned_to).filter(
                      models.Work.assignment_id == assignment_id).group_by(
                          models.Work.assigned_to).all())

    return jsonify([{
        'id': res[1],
        'name': res[0],
        'divided': res[1] in divided
    } for res in result])


@api.route('/assignments/<int:assignment_id>/submissions/', methods=['GET'])
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
            'id', 'user_name', 'user_id', 'grade', 'comment', 'created_at'
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


@api.route("/assignments/<int:assignment_id>/submissions/", methods=['POST'])
@login_required
def post_submissions(assignment_id):
    """Add submissions to the server from a blackboard zip file.
    """
    assignment = models.Assignment.query.get(assignment_id)

    if not assignment:
        raise APIException(
            'Assignment not found',
            'The assignment with code {} was not found'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)
    auth.ensure_permission('can_manage_course', assignment.course.id)

    if len(request.files) == 0:
        raise APIException("No file in HTTP request.",
                           "There was no file in the HTTP request.",
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    if 'file' not in request.files:
        key_string = ", ".join(request.files.keys())
        raise APIException('The parameter name should be "file".',
                           'Expected ^file$ got [{}].'.format(key_string),
                           APICodes.INVALID_PARAM, 400)

    file = request.files['file']
    submissions = psef.files.process_blackboard_zip(file)

    for submission_info, submission_tree in submissions:
        user = models.User.query.filter_by(
            name=submission_info.student_name).first()

        if user is None:
            perms = {
                assignment.course.id:
                models.CourseRole.query.filter_by(
                    name='student', course_id=assignment.course.id).first()
            }
            user = models.User(
                name=submission_info.student_name,
                courses=perms,
                email=submission_info.student_name + '@example.com',
                password='password',
                role=models.Role.query.filter_by(name='student').first())

            db.session.add(user)
        work = models.Work(
            assignment_id=assignment.id,
            user=user,
            created_at=submission_info.created_at,
            grade=submission_info.grade)
        db.session.add(work)
        work.add_file_tree(db.session, submission_tree)

    db.session.commit()

    return ('', 204)


@api.route('/assignments/<int:assignment_id>/linters/', methods=['GET'])
def get_linters(assignment_id):
    assignment = models.Assignment.query.get(assignment_id)

    if assignment is None:
        raise APIException(
            'The specified assignment could not be found',
            'Assignment {} does not exist'.format(assignment_id),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_use_linter', assignment.course_id)

    res = []
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
        res.append({'name': name, **opts})
    res.sort(key=lambda item: item['name'])
    return jsonify(res)


@api.route('/assignments/<int:assignment_id>/linter', methods=['POST'])
def start_linting(assignment_id):
    content = request.get_json()

    if not ('cfg' in content and 'name' in content):
        raise APIException(
            'Missing required params.',
            'Missing one ore more of children, cfg or name in the payload',
            APICodes.MISSING_REQUIRED_PARAM, 400)

    if db.session.query(
            models.LinterInstance.query.filter(
                models.AssignmentLinter.assignment_id == assignment_id,
                models.AssignmentLinter.name == content['name'])
            .exists()).scalar():
        raise APIException(
            'There is still a linter instance running',
            'There is a linter named "{}" running for assignment {}'.format(
                content['name'], assignment_id), APICodes.INVALID_STATE, 409)

    perm = models.Assignment.query.get(assignment_id)
    auth.ensure_permission('can_use_linter', perm.course_id)
    res = models.AssignmentLinter.create_tester(assignment_id, content['name'])
    db.session.add(res)
    db.session.commit()

    try:
        runner = linters.LinterRunner(
            linters.get_linter_by_name(content['name']), content['cfg'])

        thread = threading.Thread(
            target=runner.run,
            args=([t.work_id for t in res.tests], [t.id for t in res.tests],
                  ('{}api/v1/linter' + '_comments/{}').format(
                      request.url_root, '{}')))

        thread.start()
    except:
        for test in res.tests:
            test.state = models.LinterState.crashed
        db.session.commit()
    finally:
        return linters.get_linter_state(res.id)

import threading

from flask import jsonify, request
from sqlalchemy.orm import subqueryload

import psef.models as models
import psef.models as auth
import psef.linters as linters
from psef import db
from psef.errors import APICodes, APIException
from . import api


@api.route('/linter_comments/<token>', methods=['PUT'])
def put_linter_comment(token):
    unit = models.LinterInstance.query.get(token)

    if unit is None:
        raise APIException(
            'Linter was not found',
            'The linter with token "{}" was not found'.format(token),
            APICodes.OBJECT_ID_NOT_FOUND, 404)

    content = request.get_json()

    if 'crashed' in content:
        unit.state = models.LinterState.crashed
        db.session.commit()
        return '', 204

    unit.state = models.LinterState.done

    if 'files' not in content:
        raise APIException('Not all required keys were found',
                           'The keys "file" was missing form the request body',
                           APICodes.MISSING_REQUIRED_PARAM, 400)

    with db.session.no_autoflush:
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


@api.route('/linters/<linter_id>', methods=['DELETE'])
def delete_linter_output(linter_id):
    linter = models.AssignmentLinter.query.get(linter_id)

    if linter is None:
        raise APIException('Specified linter was not found',
                           'Linter {} was not found'.format(linter_id),
                           APICodes.OBJECT_ID_NOT_FOUND, 404)

    auth.ensure_permission('can_use_linter', linter.assignment.course_id)

    db.session.delete(linter)
    db.session.commit()

    return '', 204


@api.route('/linters/<linter_id>', methods=['GET'])
def get_linter_state(linter_id):
    res = []
    any_working = False
    crashed = False
    # check for user rights
    perm = db.session.query(models.AssignmentLinter).get(linter_id)
    auth.ensure_permission('can_use_linter', perm.assignment.course_id)
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
        thread.start()
    except:
        for test in res.tests:
            test.state = models.LinterState.crashed
        db.session.commit()
    finally:
        return get_linter_state(res.id)
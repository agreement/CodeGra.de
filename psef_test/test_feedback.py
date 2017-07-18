import re
import threading

import pytest

import psef.models as m

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error
late_error = pytest.mark.late_error


@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=403)('admin'),
        perm_error(error=403)('Stupid1'),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=True
)
@pytest.mark.parametrize(
    'data', [
        data_error('err'),
        data_error({}),
        data_error({
            'sr': 'err'
        }),
        data_error({
            'comment': 5
        }),
        {
            'comment': 'correct'
        },
    ]
)
def test_add_feedback(
    named_user, request, logged_in, test_client, assignment_real_works,
    session, data, error_template, ta_user
):
    assignment, work = assignment_real_works
    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error') is not None

    code_id = session.query(m.File.id).filter(
        m.File.work_id == work['id'],
        m.File.parent != None,  # NOQA
        m.File.name != '__init__',
    ).first()[0]

    if perm_err:
        code = perm_err.kwargs['error']
    elif data_err:
        code = 400
    else:
        code = 204

    def get_result():
        if data_err or perm_err:
            return {}
        return {'0': {'line': 0, 'msg': data['comment']}}

    with logged_in(named_user):
        test_client.req(
            'put',
            f'/api/v1/code/{code_id}/comments/0',
            code,
            data=data,
            result=None if code == 204 else error_template
        )

    with logged_in(ta_user):
        test_client.req(
            'get',
            f'/api/v1/code/{code_id}',
            200,
            query={'type': 'feedback'},
            result=get_result()
        )

    with logged_in(named_user):
        if not data_err:
            data['comment'] = 'bye'
            test_client.req(
                'put',
                f'/api/v1/code/{code_id}/comments/0',
                code,
                data=data,
                result=None if code == 204 else error_template
            )

    with logged_in(ta_user):
        test_client.req(
            'get',
            f'/api/v1/code/{code_id}',
            200,
            query={'type': 'feedback'},
            result=get_result()
        )


@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=403)('admin'),
        late_error(('Stupid1')),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=True
)
def test_get_feedback(
    named_user, request, logged_in, test_client, assignment_real_works,
    session, error_template, ta_user
):
    assignment, work = assignment_real_works
    perm_err = request.node.get_marker('perm_error')
    late_err = request.node.get_marker('late_error')

    code_id = session.query(m.File.id).filter(
        m.File.work_id == work['id'],
        m.File.parent != None,  # NOQA
        m.File.name != '__init__',
    ).first()[0]

    with logged_in(ta_user):
        test_client.req(
            'put',
            f'/api/v1/code/{code_id}/comments/0',
            204,
            data={'comment': 'for line 0'},
        )
        test_client.req(
            'put',
            f'/api/v1/code/{code_id}/comments/1',
            204,
            data={'comment': 'for line - 1'},
        )

    with logged_in(named_user):
        code = perm_err.kwargs['error'] if perm_err else 200

        if perm_err:
            res = error_template
        elif late_err:
            res = {}
        else:
            res = {
                '0': {
                    'line': 0,
                    'msg': 'for line 0'
                },
                '1': {
                    'line': 1,
                    'msg': 'for line - 1'
                }
            }

        test_client.req(
            'get',
            f'/api/v1/code/{code_id}',
            code,
            query={'type': 'feedback'},
            result=res
        )

    assig = session.query(m.Assignment).get(assignment.id)
    assig.state = m._AssignmentStateEnum.done
    session.commit()

    with logged_in(named_user):
        code = perm_err.kwargs['error'] if perm_err else 200

        if perm_err:
            res = error_template
        else:
            res = {
                '0': {
                    'line': 0,
                    'msg': 'for line 0'
                },
                '1': {
                    'line': 1,
                    'msg': 'for line - 1'
                }
            }

        test_client.req(
            'get',
            f'/api/v1/code/{code_id}',
            code,
            query={'type': 'feedback'},
            result=res
        )


@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=403)('admin'),
        perm_error(error=403)(('Stupid1')),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=True
)
def test_delete_feedback(
    named_user, request, logged_in, test_client, assignment_real_works,
    session, error_template, ta_user
):
    assignment, work = assignment_real_works
    perm_err = request.node.get_marker('perm_error')

    code_id = session.query(m.File.id).filter(
        m.File.work_id == work['id'],
        m.File.parent != None,  # NOQA
        m.File.name != '__init__',
    ).first()[0]

    result = {
        '0': {
            'line': 0,
            'msg': 'for line 0'
        },
        '1': {
            'line': 1,
            'msg': 'line1'
        }
    }

    with logged_in(ta_user):
        test_client.req(
            'put',
            f'/api/v1/code/{code_id}/comments/1',
            204,
            data={'comment': 'line1'},
        )
        test_client.req(
            'put',
            f'/api/v1/code/{code_id}/comments/0',
            204,
            data={'comment': 'for line 0'},
        )

        test_client.req(
            'get',
            f'/api/v1/code/{code_id}',
            200,
            query={'type': 'feedback'},
            result=result
        )

    with logged_in(named_user):
        test_client.req(
            'delete',
            f'/api/v1/code/{code_id}/comments/0',
            perm_err.kwargs['error'] if perm_err else 204,
        )

    if not perm_err:
        result.pop('0')

    with logged_in(ta_user):
        test_client.req(
            'get',
            f'/api/v1/code/{code_id}',
            200,
            query={'type': 'feedback'},
            result=result
        )


@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=403)('admin'),
        late_error(('Stupid1')),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=True
)
def test_get_all_feedback(
    named_user, request, logged_in, test_client, assignment_real_works,
    session, error_template, ta_user, monkeypatch
):
    class MyThread:
        def __init__(self, target, args=None):
            self.run = target
            self.args = [] if args is None else args

        def start(self):
            print(self.args)
            self.run(*self.args)

    monkeypatch.setattr(threading, 'Thread', MyThread)

    assignment, work = assignment_real_works
    perm_err = request.node.get_marker('perm_error')
    late_err = request.node.get_marker('late_error')

    code_id = session.query(m.File.id).filter(
        m.File.work_id == work['id'],
        m.File.parent != None,  # NOQA
        m.File.name != '__init__',
    ).first()[0]

    with logged_in(ta_user):
        test_client.req(
            'put',
            f'/api/v1/code/{code_id}/comments/0',
            204,
            data={'comment': 'for line 0'},
        )
        test_client.req(
            'put',
            f'/api/v1/code/{code_id}/comments/1',
            204,
            data={'comment': 'for line - 1'},
        )

        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/linter',
            200,
            data={'name': 'Flake8',
                  'cfg': ''}
        )

    expected = re.compile(
        r'Assignment: TEST COURSE\n'
        r'Grade: \n'
        r'General feedback:\n'
        r'\n'
        r'\n'
        r'Comments:\n'
        r'test.py:0:0: for line 0\n'
        r'test.py:1:0: for line - 1\n'
        r'\nLinter comments:\n'
        r'(test.py:1:0: \(Flake8 .*\) .*\n)+\n*'
    )

    with logged_in(named_user):
        res = test_client.get(
            f'/api/v1/submissions/{work["id"]}',
            query_string={'type': 'feedback'}
        )

        print(res.data.decode('utf8'))

        if late_err:
            code = 403
        else:
            code = perm_err.kwargs['error'] if perm_err else 200

        assert res.status_code == code
        if not (perm_err or late_err):
            assert expected.match(res.data.decode('utf8'))

    assig = session.query(m.Assignment).get(assignment.id)
    assig.state = m._AssignmentStateEnum.done
    session.commit()

    with logged_in(named_user):
        res = test_client.get(
            f'/api/v1/submissions/{work["id"]}',
            query_string={'type': 'feedback'}
        )

        print(res.data.decode('utf8'))
        code = perm_err.kwargs['error'] if perm_err else 200
        assert res.status_code == code

        if not perm_err:
            assert expected.match(res.data.decode('utf8'))

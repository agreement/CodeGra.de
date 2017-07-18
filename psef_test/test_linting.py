"""Here be dragons, watch out!
"""
import os
import copy
import datetime
import threading
from random import shuffle

import pytest

import psef.models as m
import psef.linters as l

run_error = pytest.mark.run_error
perm_error = pytest.mark.perm_error
get_works = pytest.mark.get_works


@pytest.fixture(autouse=True)
def monkey_patch_thread(monkeypatch):
    class MyThread:
        def __init__(self, target, args=None):
            self.run = target
            self.args = [] if args is None else args

        def start(self):
            print(self.args)
            self.run(*self.args)

    monkeypatch.setattr(threading, 'Thread', MyThread)
    yield


ALL_LINTERS = sorted(['Flake8', 'MixedWhitespace', 'Pylint'])


@pytest.mark.parametrize(
    'filename,linter_cfgs_exp',
    [
        (
            'test_flake8.tar.gz',
            [('Flake8', '', ['W191', 'E211', 'E201', 'E202'])]
        ),
        run_error(
            error=400,
        )(('test_flake8.tar.gz', [('Flake8', False, '')])),
        run_error(error=400)(('test_flake8.tar.gz', [('Flake8', 5, '')])),
        run_error(error=400)(('test_flake8.tar.gz', [(6, '666', '')])),
        run_error(error=400)(('test_flake8.tar.gz', [(False, False, '')])),
        run_error(error=400)(('test_flake8.tar.gz', [(False, '', '')])),
        run_error(crash='Pylint')(
            ('test_flake8.tar.gz', [('Pylint', '[MASTER]\njobs=-1', '')])
        ),
        run_error(crash='Flake8')(
            (
                'test_flake8.tar.gz', [
                    (
                        'Flake8',
                        '[flake8]\ndisable_noqa=Trues # This should crash', ''
                    )
                ]
            )
        ),
        run_error(crash='Flake8')(
            (
                'test_flake8.tar.gz', [
                    (
                        'Flake8',
                        '[flake8]\ndisable_noqa=Trues # This should crash', ''
                    ),
                    ('Pylint', '', ['ERR']),
                ]
            )
        ),
        (
            'test_pylint.tar.gz', [
                (
                    'Pylint', '', [
                        'C0111',
                        'C0103',
                        'C0103',
                        'C0111',
                        'W0613',
                        'W0312',
                        'C0326',
                        'C0326',
                    ]
                )
            ]
        ),
        ('test_flake8.tar.gz', [('Pylint', '', ['ERR'])]),
        (
            'test_flake8.tar.gz', [
                ('Pylint', '', ['ERR']),
                ('Flake8', '', ['W191', 'E211', 'E201', 'E202'])
            ]
        ),
    ],
    indirect=['filename'],
)
@pytest.mark.parametrize(
    'named_user,use_ta', [
        ('Thomas Schaper', False),
        get_works(perm_error(error=403)(('Stupid1', True))),
        get_works(perm_error(error=403)(('Stupid1', False))),
        perm_error(error=403)(('admin', False)),
        perm_error(error=401)(('NOT_LOGGED_IN', False)),
        perm_error(error=401)(('NOT_LOGGED_IN', True)),
    ],
    indirect=['named_user']
)
def test_linters(
    ta_user, named_user, test_client, logged_in, use_ta, assignment_real_works,
    linter_cfgs_exp, request, error_template, session
):
    assignment, single_work = assignment_real_works
    run_err = request.node.get_marker('run_error')

    if run_err:
        run_err = copy.deepcopy(run_err.kwargs)
    else:
        run_err = {}

    get_work = request.node.get_marker('get_works')
    perm_err = request.node.get_marker('perm_error')
    set_perm_err = (not use_ta) and perm_err
    if set_perm_err:
        run_err['error'] = set_perm_err.kwargs['error']

    with logged_in(ta_user if use_ta else named_user):
        for linter, cfg, _ in linter_cfgs_exp:
            data = {}
            if linter != False:  # NOQA
                data['name'] = linter
            if cfg != False:  # NOQA
                data['cfg'] = cfg

            code = run_err.get('error') or 200

            test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/linter',
                code,
                data=data,
                result=error_template if run_err.get('error') else {
                    'done': 0 if run_err.get('crash') == linter else 2,
                    'working': 0,
                    'id': str,
                    'crashed': 2 if run_err.get('crash') == linter else 0,
                    'name': linter,
                }
            )

        result = []
        for linter in ALL_LINTERS:
            tried_linter = [
                True for lint in linter_cfgs_exp if lint[0] == linter
            ]
            item = {
                'name': linter,
                'desc': str,
                'opts': dict,
            }
            if run_err.get('crash') == linter:
                item['state'] = 'crashed'
                item['id'] = str
            elif not run_err.get('error') and tried_linter:
                item['state'] = 'done'
                item['id'] = str
            else:
                item['state'] = 'new'

            result.append(item)

        linter_result = test_client.req(
            'get',
            f'/api/v1/assignments/{assignment.id}/linters/',
            code if set_perm_err else 200,
            result=error_template if set_perm_err else result,
        )

        for linter in linter_result if not set_perm_err else []:
            if [True for lint in linter_cfgs_exp if lint[0] == linter['name']]:
                if 'id' not in linter:
                    assert run_err.get('crash') != linter['name']
                    continue
                lname = linter['name']
                test_client.req(
                    'get',
                    f'/api/v1/linters/{linter["id"]}',
                    400 if set_perm_err else 200,
                    result=error_template if set_perm_err else {
                        'name': linter['name'],
                        'done': 0 if run_err.get('crash') == lname else 2,
                        'working': 0,
                        'id': str,
                        'crashed': 2 if run_err.get('crash') == lname else 0,
                    }
                )

    with logged_in(named_user):
        code_id = session.query(m.File.id).filter(
            m.File.work_id == single_work['id'],
            m.File.parent != None,  # NOQA
            m.File.name != '__init__',
        ).first()[0]

        linters = {}
        for linter, _, exp in linter_cfgs_exp:
            linters[linter] = list(exp)

        can_see_comm = not perm_err or get_work

        res = sorted(
            test_client.req(
                'get',
                f'/api/v1/code/{code_id}',
                200 if can_see_comm else perm_err.kwargs['error'],
                query={'type': 'linter-feedback'},
            ).items(),
            key=lambda el: el[0]
        )

        if can_see_comm:
            for _, feedbacks in res:
                for name, linter_comm in feedbacks:
                    assert linters[name].pop(0) == linter_comm['code']

            if get_work:
                assert not res
            else:
                assert not any(linters.values())

        for linter in linter_result:
            if 'id' not in linter:
                continue

            test_client.req(
                'delete',
                f'/api/v1/linters/{linter["id"]}',
                perm_err.kwargs['error'] if perm_err else 204,
            )
            test_client.req(
                'get',
                f'/api/v1/linters/{linter["id"]}',
                perm_err.kwargs['error'] if perm_err else 404,
                result=None if perm_err else error_template
            )


@pytest.mark.parametrize('with_works', [True], indirect=True)
def test_whitespace_linter(ta_user, test_client, assignment, logged_in):
    with logged_in(ta_user):
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/linter',
            200,
            data={'name': 'MixedWhitespace',
                  'cfg': 'ANY'},
            result={
                'done': 3,
                'working': 0,
                'id': str,
                'crashed': 0,
                'name': 'MixedWhitespace',
            }
        )
        res = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}', 200
        )
        assert res
        assert res['whitespace_linter']


@pytest.mark.parametrize(
    'filename,exps',
    [
        ('test_flake8.tar.gz', ['W191', 'E211', 'E201', 'E202']),
    ],
)
def test_lint_later_submission(
    test_client, logged_in, assignment, exps, error_template, session,
    filename, ta_user, student_user
):
    with logged_in(ta_user):
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/linter',
            200,
            data={'name': 'Flake8',
                  'cfg': ''},
            result={
                'done': 0,
                'working': 0,
                'id': str,
                'crashed': 0,
                'name': 'Flake8',
            }
        )

    with logged_in(student_user):
        single_work = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission',
            201,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../'
                        f'test_data/test_linter/{filename}', filename
                    )
            }
        )

    with logged_in(ta_user):
        code_id = session.query(m.File.id).filter(
            m.File.work_id == single_work['id'],
            m.File.parent != None,  # NOQA
            m.File.name != '__init__',
        ).first()[0]

        res = sorted(
            test_client.req(
                'get',
                f'/api/v1/code/{code_id}',
                200,
                query={'type': 'linter-feedback'},
            ).items(),
            key=lambda el: el[0]
        )

        assert res

        for _, feedbacks in res:
            for name, linter_comm in feedbacks:
                assert exps.pop(0) == linter_comm['code']

        assert not exps


@pytest.mark.parametrize('with_works', [True], indirect=True)
def test_already_running_linter(
    ta_user, test_client, assignment, logged_in, monkeypatch, error_template
):
    class MyThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            pass

    monkeypatch.setattr(threading, 'Thread', MyThread)

    with logged_in(ta_user):
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/linter',
            200,
            data={'name': 'Flake8',
                  'cfg': 'ANY'},
            result={
                'done': 0,
                'working': 3,
                'id': str,
                'crashed': 0,
                'name': 'Flake8',
            }
        )

        res = test_client.req(
            'get',
            f'/api/v1/assignments/{assignment.id}/linters/',
            200,
        )
        found = 0
        for r in res:
            if r['name'] == 'Flake8':
                found += 1
                assert r['state'] == 'running'
        assert found == 1

        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/linter',
            409,
            data={'name': 'Flake8',
                  'cfg': 'ANY'},
            result=error_template,
        )


@pytest.mark.parametrize('with_works', [True], indirect=True)
def test_non_existing_linter(
    ta_user, test_client, assignment, logged_in, monkeypatch, error_template
):
    with logged_in(ta_user):
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/linter',
            404,
            data={'name': 'NON_EXISTING',
                  'cfg': 'ERROR'},
            result=error_template
        )

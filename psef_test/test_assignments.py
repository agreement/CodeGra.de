import io
import os
import copy
import json
import uuid
import random
import datetime
from functools import reduce
from collections import defaultdict

import pytest

import psef
import psef.models as m
from psef.errors import APICodes
from psef.helpers import ensure_keys_in_dict

http_err = pytest.mark.http_err
perm_error = pytest.mark.perm_error


@pytest.fixture
def original_rubric_data():
    yield {
        'rows':
            [
                {
                    'header':
                        'My header',
                    'description':
                        'My description',
                    'items':
                        [
                            {
                                'description': 'item description',
                                'header': 'header',
                                'points': 5,
                            }, {
                                'description': 'item description',
                                'header': 'header',
                                'points': 4,
                            }
                        ]
                }
            ]
    }


@pytest.fixture
def rubric(logged_in, ta_user, test_client, original_rubric_data, assignment):
    with logged_in(ta_user):
        original = original_rubric_data
        yield test_client.req(
            'put',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            200,
            data=original,
            result=[
                {
                    'header': original['rows'][0]['header'],
                    'description': original['rows'][0]['description'],
                    'id': int,
                    'items': list,
                }
            ]
        )


@pytest.mark.parametrize(
    'named_user,hidden', [
        ('Thomas Schaper', True),
        ('Stupid1', False),
        ('nobody', False),
        perm_error(error=401)(('NOT_LOGGED_IN', False)),
    ],
    indirect=['named_user']
)
def test_get_all_assignments(
    named_user, hidden, test_client, logged_in, request, error_template
):
    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        assigs = test_client.req('get', '/api/v1/assignments/', error or 200)
        has_hidden = False
        if not error:
            for assig in assigs:
                ensure_keys_in_dict(
                    assig, [
                        ('id', int),
                        ('state', str),
                        ('description', str),
                        ('created_at', str),
                        ('name', str),
                        ('deadline', str),
                        ('is_lti', bool),
                        ('whitespace_linter', bool),
                        ('course', dict)
                    ]
                )
                has_hidden = has_hidden or assig['state'] == 'hidden'
            assert has_hidden == hidden


@pytest.mark.parametrize(
    'named_user,course_name,state_is_hidden,perm_err', [
        ('Thomas Schaper', 'Project Software Engineering', True, True),
        ('Thomas Schaper', 'Project Software Engineering', False, False),
        ('Thomas Schaper', 'Programmeertalen', True, False),
        ('Stupid1', 'Programmeertalen', False, False),
        ('Stupid1', 'Project Software Engineering', False, True),
        ('NOT_LOGGED_IN', 'Programmeertalen', False, True),
    ],
    indirect=['named_user', 'course_name', 'state_is_hidden']
)
def test_get_assignment(
    named_user, course_name, state_is_hidden, perm_err, test_client, logged_in,
    session, error_template, assignment
):
    with logged_in(named_user):
        if named_user == 'NOT_LOGGED_IN':
            status = 401
        else:
            status = 403 if perm_err else 200
        if status == 200:
            res = {
                'id': assignment.id,
                'state': 'hidden' if state_is_hidden else 'submitting',
                'description': '',
                'created_at': assignment.created_at.isoformat(),
                'deadline': assignment.deadline.isoformat(),
                'name': assignment.name,
                'is_lti': False,
                'cgignore': None,
                'course': dict,
                'whitespace_linter': False,
                'reminder_type': 'none',
                'reminder_time': None,
            }
        else:
            res = error_template
        test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}', status, result=res
        )


def test_get_non_existing_assignment(
    ta_user, test_client, logged_in, error_template
):
    with logged_in(ta_user):
        test_client.req(
            'get', f'/api/v1/assignments/0', 404, result=error_template
        )


@pytest.mark.parametrize(
    'update_data', [
        {
            'name': 'NEW AND UPDATED NAME',
            'state': 'open',
            'deadline': datetime.datetime.utcnow().isoformat(),
        }
    ]
)
@pytest.mark.parametrize('keep_name', [True, False])
@pytest.mark.parametrize('keep_deadline', [True, False])
@pytest.mark.parametrize('keep_state', [True, False])
@pytest.mark.parametrize(
    'changes,err_code', [
        ({
            'state': 'open'
        }, False),
        ({
            'state': 'done'
        }, False),
        ({
            'state': 'hidden'
        }, False),
        ({
            'state': 'wow'
        }, 400),
        ({
            'state': 2,
        }, 400),
        ({
            'deadline': 'nodate'
        }, 400),
        ({
            'deadline': []
        }, 400),
        ({
            'name': ''
        }, 400),
        ({
            'name': 1
        }, 400),
    ]
)
def test_update_assignment(
    changes,
    err_code,
    keep_name,
    keep_deadline,
    keep_state,
    ta_user,
    test_client,
    logged_in,
    assignment,
    update_data,
    error_template,
):
    with logged_in(ta_user):
        data = copy.deepcopy(update_data)
        assig_id = assignment.id

        for val, name in [
            (keep_state, 'state'), (keep_name, 'name'),
            (keep_deadline, 'deadline')
        ]:
            if not val:
                data.pop(name)
                if name in changes:
                    changes.pop(name)

        if not changes:
            err_code = False

        data.update(changes)

        old_state = assignment.state.name
        old_name = assignment.name
        old_deadline = assignment.deadline

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assig_id}',
            err_code if err_code else 204,
            data=data,
            result=error_template if err_code else None
        )
        if not err_code:
            new_assig = psef.helpers.get_or_404(m.Assignment, assig_id)
            if keep_state:
                assert new_assig.state.name == data['state']
            if keep_name:
                assert new_assig.name == data['name']
            if keep_deadline:
                assert new_assig.deadline.isoformat() == data['deadline']
        else:
            new_assig = psef.helpers.get_or_404(m.Assignment, assig_id)
            assert new_assig.state.name == old_state
            assert new_assig.name == old_name
            assert new_assig.deadline == old_deadline


@pytest.mark.parametrize(
    'named_user',
    [http_err(error=403)('Stupid1'),
     http_err(error=401)('NOT_LOGGED_IN')],
    indirect=True
)
def test_update_assignment_wrong_permissions(
    assignment,
    named_user,
    logged_in,
    test_client,
    error_template,
    request,
):
    marker = request.node.get_marker('http_err')
    with logged_in(named_user):
        is_logged_in = not isinstance(named_user, str)
        res = test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}',
            marker.kwargs['error'],
            result=error_template,
            data={
                'name': 'name',
                'state': 'open',
                'deadline': datetime.datetime.utcnow().isoformat(),
            }
        )
        res['code'] = (
            APICodes.NOT_LOGGED_IN
            if is_logged_in else APICodes.INCORRECT_PERMISSION
        )


err400 = http_err(error=400)


@pytest.mark.parametrize(
    'item_description',
    [err400(None), 'new idesc', err400(5)]
)
@pytest.mark.parametrize('item_header', [err400(None), 'new ihead', err400(5)])
@pytest.mark.parametrize('item_points', [err400(None), 5.3, 11, err400('Wow')])
@pytest.mark.parametrize(
    'row_description',
    [err400(None), 'new rdesc', err400(5)]
)
@pytest.mark.parametrize(
    'row_header',
    [err400(None), 'new rheader', err400(5)]
)
def test_add_rubric_row(
    item_description, item_points, row_description, row_header, assignment,
    ta_user, logged_in, test_client, error_template, request, item_header,
    rubric
):
    row = {}
    if row_header is not None:
        row['header'] = row_header
    if row_description is not None:
        row['description'] = row_description

    item = {}
    if item_header is not None:
        item['header'] = item_header
    if item_description is not None:
        item['description'] = item_description
    if item_points is not None:
        item['points'] = item_points

    row['items'] = [item, item]

    marker = request.node.get_marker('http_err')
    code = 200 if marker is None else marker.kwargs['error']

    with logged_in(ta_user):
        data = test_client.req(
            'put',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            status_code=code,
            data={'rows': rubric + [row]},
            result=error_template if marker else rubric + [dict],
        )
        if marker is None:
            assert len(data) == len(rubric) + 1
            assert data[-1]['header'] == row_header
            assert data[-1]['description'] == row_description
            assert len(data[-1]['items']) == 2
            assert data[-1]['items'][0]['id'] > 0
            assert data[-1]['items'][0]['points'] == item_points
        else:
            test_client.req(
                'get',
                f'/api/v1/assignments/{assignment.id}/rubrics/',
                status_code=200,
                result=rubric,
            )


@pytest.mark.parametrize(
    'item_description',
    [err400(None), 'new idesc', err400(5)]
)
@pytest.mark.parametrize('item_header', [err400(None), 'new ihead', err400(5)])
@pytest.mark.parametrize('item_points', [err400(None), 5.3, 11, err400('Wow')])
@pytest.mark.parametrize('row_description', [None, 'new rdesc', err400(5)])
@pytest.mark.parametrize('row_header', [None, 'new rheader', err400(5)])
def test_update_rubric_row(
    item_description, item_points, row_description, row_header, assignment,
    ta_user, logged_in, test_client, error_template, request, item_header,
    rubric
):
    row = {}
    if row_header is not None:
        row['header'] = row_header
    if row_description is not None:
        row['description'] = row_description

    item = {}
    if item_header is not None:
        item['header'] = item_header
    if item_description is not None:
        item['description'] = item_description
    if item_points is not None:
        item['points'] = item_points

    row['items'] = [item, item]

    marker = request.node.get_marker('http_err')
    code = 200 if marker is None else marker.kwargs['error']

    with logged_in(ta_user):
        new_rubric = copy.deepcopy(rubric)
        new_rubric[0].update(row)

        data = test_client.req(
            'put',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            status_code=code,
            data={'rows': new_rubric},
            result=error_template if marker else [dict],
        )
        if marker is None:
            assert len(data) == len(rubric)
            assert data[0]['header'] == row_header or rubric[0]['header']
            assert data[0]['description'
                           ] == row_description or rubric[0]['description']
            assert len(data[0]['items']) == 2
            assert data[0]['items'][0]['id'] > 0
            assert data[0]['items'][0]['points'] == item_points
            assert data[0]['items'][0]['header'] == item_header
            assert data[0]['items'][0]['description'] == item_description
        else:
            test_client.req(
                'get',
                f'/api/v1/assignments/{assignment.id}/rubrics/',
                status_code=200,
                result=rubric,
            )


@pytest.mark.parametrize(
    'item_description',
    [err400(None), 'You did well', err400(5)]
)
@pytest.mark.parametrize(
    'item_header',
    [err400(None), 'You very well', err400(5)]
)
@pytest.mark.parametrize(
    'item_points',
    [err400(None), 5.3, 5, 11, err400('Wow')]
)
@pytest.mark.parametrize(
    'row_description',
    [err400(None), 'A row desc', err400(5)]
)
@pytest.mark.parametrize(
    'row_header',
    [err400(None), 'A row header', err400(5)]
)
def test_get_and_add_rubric_row(
    item_description, item_points, row_description, row_header, assignment,
    ta_user, logged_in, test_client, error_template, request, item_header
):
    row = {}
    if row_header is not None:
        row['header'] = row_header
    if row_description is not None:
        row['description'] = row_description
    item = {}
    if item_header is not None:
        item['header'] = item_header
    if item_description is not None:
        item['description'] = item_description
    if item_points is not None:
        item['points'] = item_points
    for item in [item] if item else [item, None]:
        if item is not None:
            row['items'] = [item]
        marker = request.node.get_marker('http_err')
        code = 200 if marker is None else marker.kwargs['error']
        res = [
            {
                'id':
                    int,
                'header':
                    row['header'],
                'description':
                    row['description'],
                'items':
                    [
                        {
                            'id': int,
                            'description': item['description'],
                            'header': item['header'],
                            'points': item['points'],
                        }
                    ],
            }
        ] if marker is None else error_template
        res = res if marker is None else error_template

        with logged_in(ta_user):
            test_client.req(
                'put',
                f'/api/v1/assignments/{assignment.id}/rubrics/',
                code,
                result=res,
                data={
                    'rows': [row]
                }
            )
            test_client.req(
                'get',
                f'/api/v1/assignments/{assignment.id}/rubrics/',
                200 if marker is None else 404,
                result=res,
            )


@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        http_err(error=403)('Stupid1'),
        http_err(error=401)('NOT_LOGGED_IN')
    ],
    indirect=True
)
def test_delete_rubric(
    assignment, named_user, logged_in, test_client, error_template, request,
    ta_user, rubric
):
    marker = request.node.get_marker('http_err')
    code = 204 if marker is None else marker.kwargs['error']

    with logged_in(named_user):
        test_client.req(
            'delete',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            code,
            result=marker if marker is None else error_template,
        )
    if marker is None:
        with logged_in(named_user):
            test_client.req(
                'get',
                f'/api/v1/assignments/{assignment.id}/rubrics/',
                404,
                result=error_template,
            )
            test_client.req(
                'delete',
                f'/api/v1/assignments/{assignment.id}/rubrics/',
                404,
                result=error_template,
            )
    else:
        with logged_in(ta_user):
            test_client.req(
                'get',
                f'/api/v1/assignments/{assignment.id}/rubrics/',
                200,
                result=rubric
            )


@pytest.mark.parametrize(
    'named_user',
    [http_err(error=403)('Stupid1'),
     http_err(error=401)('NOT_LOGGED_IN')],
    indirect=True
)
def test_update_add_rubric_wrong_permissions(
    assignment,
    named_user,
    logged_in,
    test_client,
    error_template,
    request,
    ta_user,
):
    marker = request.node.get_marker('http_err')
    rubric = {
        'header':
            f'My header',
        'description':
            f'My description',
        'items':
            [
                {
                    'header': 'The header',
                    'description': f'item description',
                    'points': 2,
                },
            ]
    }
    with logged_in(named_user):
        res = test_client.req(
            'put',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            marker.kwargs['error'],
            result=error_template,
            data={
                'rows': [rubric]
            }
        )
        res['code'] = (
            APICodes.NOT_LOGGED_IN
            if marker.kwargs['error'] == 401 else APICodes.INCORRECT_PERMISSION
        )
    with logged_in(ta_user):
        rubric = test_client.req(
            'put',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            200,
            data={
                'rows': [rubric]
            }
        )
    with logged_in(named_user):
        res = test_client.req(
            'put',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            marker.kwargs['error'],
            result=error_template,
            data=res
        )
        res['code'] = (
            APICodes.NOT_LOGGED_IN
            if marker.kwargs['error'] == 401 else APICodes.INCORRECT_PERMISSION
        )
    with logged_in(ta_user):
        test_client.req(
            'get',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            200,
            result=rubric
        )


def test_creating_wrong_rubric(
    request,
    test_client,
    logged_in,
    error_template,
    ta_user,
    assignment,
    session,
    course_name,
):
    assig_id = assignment.id

    with logged_in(ta_user):
        rubric = {
            'rows': [{
                'header': 'My header',
                'description': 'My description',
                'items': [{
                    'description': '5points',
                    'points': 5
                }, {
                    'description': '10points',
                    'points': 10,
                }]
            }, {
                'header': 'My header2',
                'description': 'My description',
                'items': [{
                    'description': '5points',
                    'points': -15
                }, {
                    'description': '10points',
                    'points': -10,
                }],
            }]
        }  # yapf: disable
        test_client.req(
            'put',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            400,
            data=rubric,
            result=error_template,
        )
        test_client.req(
            'get',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            404,
            result=error_template,
        )
        rubric = {
            'rows': [{
                'header': 'My header',
                'description': 'My description',
                'items': [{
                    'description': '5points',
                    'points': -5
                }, {
                    'description': '10points',
                    'points': -10,
                }]
            }]
        }  # yapf: disable
        test_client.req(
            'put',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            400,
            data=rubric,
            result=error_template,
        )
        test_client.req(
            'get',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            404,
            result=error_template,
        )
        rubric = {
            'rows': [{
                'header': 'My header',
                'description': 'My description',
                'items': []
            }]
        }  # yapf: disable
        test_client.req(
            'put',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            400,
            data=rubric,
            result=error_template,
        )
        test_client.req(
            'get',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            404,
            result=error_template,
        )
        rubric = {
            'rows': []
        }  # yapf: disable
        test_client.req(
            'put',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            400,
            data=rubric,
            result=error_template,
        )
        test_client.req(
            'get',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            404,
            result=error_template,
        )


def test_updating_wrong_rubric(
    request,
    test_client,
    logged_in,
    error_template,
    ta_user,
    assignment,
    session,
    course_name,
):
    assig_id = assignment.id
    with logged_in(ta_user):
        rubric = {
            'rows': [{
                'header': 'My header',
                'description': 'My description',
                'items': [{
                    'description': '5points',
                    'header': 'head5',
                    'points': 5
                }, {
                    'description': '10points',
                    'header': 'head10',
                    'points': 10,
                }]
            }]
        }  # yapf: disable
        rubric = test_client.req(
            'put',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            200,
            data=rubric,
        )
        server_rubric = copy.deepcopy(rubric)

        rubric[0]['items'][1]['points'] = 7
        rubric.append(
            {
                'header': 'head',
                'description': '22',
                'items': [{
                    'description': '-7points',
                    'points': -7,
                }]
            }
        )
        test_client.req(
            'put',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            400,
            data=rubric,
            result=error_template,
        )
        rubric = test_client.req(
            'get',
            f'/api/v1/assignments/{assig_id}/rubrics/',
            200,
            result=server_rubric
        )


# yapf: disable
@pytest.mark.parametrize(
    'name,entries,dirname,exts', [
        (
            'single_file_archive', [{
                'id': int,
                'name': 'single_file_work'
            }], 'single_file_archive', ['.tar.gz', '.zip']
        ), (
            'multiple_file_archive', [
                {
                    'id': int,
                    'name': 'single_file_work'
                }, {
                    'id': int,
                    'name': 'single_file_work_copy'
                }
            ], 'multiple_file_archive', ['.tar.gz', '.zip']
        ), (
            'deheading_dir_archive', [
                {
                    'id': int,
                    'name': 'single_file_work'
                }, {
                    'id': int,
                    'name': 'single_file_work_copy'
                }
            ], 'dir', ['.tar.gz', '.zip']
        ),
        (
            'single_dir_archive', [
                {
                    'id': int,
                    'name': 'single_file_work'
                }, {
                    'id': int,
                    'name': 'single_file_work_copy'
                }
            ], 'dir', ['.tar.gz', '.zip']
        ), (
            'multiple_dir_archive', [
                {
                    'id': int,
                    'name': 'dir',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }, {
                    'id': int,
                    'name': 'dir2',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }
            ],
            'multiple_dir_archive', ['.tar.gz', '.zip']
        ), (
            'single_file_work', [
                {
                    'name': 'single_file_work',
                    'id': int,
                }
            ],
            'top', ['']
        )
    ]
)
@pytest.mark.parametrize('assignment', ['new', 'old'], indirect=True)
@pytest.mark.parametrize('named_user', ['Stupid1', 'Devin Hillenius'],
                         indirect=True)
# yapf: enable
def test_upload_files(
    named_user, exts, test_client, logged_in, assignment, name, entries,
    dirname, error_template, ta_user
):
    for ext in exts:
        print(f'Testing with extension "{ext}"')
        with logged_in(named_user):
            res = test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/submission',
                400,
                real_data={},
                result=error_template
            )
            assert res['message'].startswith('No file in HTTP')

            res = test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/submission',
                400,
                real_data={'err': (io.BytesIO(b'my file content'), 'ror')},
                result=error_template
            )
            assert res['message'].startswith('The parameter name should')

            res = test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/submission',
                400,
                real_data={
                    'file':
                        (
                            f'{os.path.dirname(__file__)}/../test_data/'
                            f'test_submissions/{name}{ext}', f''
                        )
                },
                result=error_template
            )
            assert res['message'
                       ].startswith('The filename should not be empty')

            if assignment.is_open or named_user.has_permission(
                'can_upload_after_deadline', assignment.course_id
            ):
                res = test_client.req(
                    'post',
                    f'/api/v1/assignments/{assignment.id}/submission?extended',
                    201,
                    real_data={
                        'file':
                            (
                                f'{os.path.dirname(__file__)}/../test_data/'
                                f'test_submissions/{name}{ext}', f'{name}{ext}'
                            )
                    },
                    result={
                        'id': int,
                        'user': named_user.__to_json__(),
                        'created_at': str,
                        'assignee': None,
                        'grade': None,
                    }
                )

                test_client.req(
                    'get',
                    f'/api/v1/submissions/{res["id"]}/files/',
                    200,
                    result={
                        'entries': entries,
                        'id': int,
                        'name': f'{dirname}'
                    }
                )

            else:
                res = test_client.req(
                    'post',
                    f'/api/v1/assignments/{assignment.id}/submission',
                    403,
                    real_data={
                        'file':
                            (
                                f'{os.path.dirname(__file__)}/../test_data/'
                                f'test_submissions/{name}{ext}', f'{name}{ext}'
                            )
                    },
                    result=error_template
                )


def test_upload_too_large_file(
    student_user, test_client, error_template, logged_in, assignment
):
    filestr = b'0' * 2 * 2 ** 20
    with logged_in(student_user):
        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission',
            400,
            real_data={'file': (io.BytesIO(filestr), f'filename')},
            result=error_template
        )
        assert res['message'].startswith('Uploaded files are too big')


@pytest.mark.parametrize('named_user', ['Thomas Schaper'], indirect=True)
@pytest.mark.parametrize(
    'graders', [
        (['Thomas Schaper', 'Devin Hillenius']),
        (['Devin Hillenius']),
        http_err(error=400)(['Thomas Schaper', -1]),
        http_err(error=400)(['Thomas Schaper', 'Stupid1']),
        http_err(error=400)(['Stupid1']),
        http_err(error=400)(['Stupid1', 'Devin Hillenius']),
        http_err(error=400)(['Devin Hillenius', 'admin']),
    ]
)
@pytest.mark.parametrize('with_works', [True, False], indirect=True)
def test_divide_assignments(
    assignment, graders, named_user, logged_in, test_client, error_template,
    request, with_works
):
    marker = request.node.get_marker('http_err')
    code = 204 if marker is None else marker.kwargs['error']
    res = None if marker is None else error_template

    grader_ids = []
    for grader in graders:
        if isinstance(grader, int):
            grader_ids.append(grader)
        else:
            grader_ids.append(m.User.query.filter_by(name=grader).one().id)
    with logged_in(named_user):
        assigs = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
        )
        for assig in assigs:
            assert assig['assignee'] is None
        assert with_works == bool(assigs)

        if code == 204:
            gid = grader_ids[0]
            for d in [{gid: '1'}, {gid: 'boe'}]:
                test_client.req(
                    'patch',
                    f'/api/v1/assignments/{assignment.id}/divide',
                    400,
                    result=error_template,
                    data={
                        'graders': d
                    }
                )

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            code,
            result=res,
            data={
                'graders': {i: 1
                            for i in grader_ids}
            }
        )
        assigs = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
        )
        seen = set()
        graders_seen = set()
        for assig in assigs:
            if assig['user']['email'] in seen:
                continue
            else:
                seen.add(assig['user']['email'])
            if marker is None:
                assert assig['assignee']['id'] in grader_ids
                graders_seen.add(assig['assignee']['id'])
            else:
                assert assig['assignee'] is None

        if with_works and marker is None:
            assert graders_seen == set(grader_ids)

        if with_works and code == 204 and len(grader_ids) == 2:
            grader_assigs = defaultdict(lambda: set())
            seen = set()
            for assig in assigs:
                if assig['user']['email'] in seen:
                    continue
                seen.add(assig['user']['email'])
                grader_assigs[assig['assignee']['id']].add(assig['id'])
            assert (
                len(grader_assigs[grader_ids[0]]) == len(
                    grader_assigs[grader_ids[1]]
                )
            )
            test_client.req(
                'patch',
                f'/api/v1/assignments/{assignment.id}/divide',
                code,
                result=res,
                data={
                    'graders': {i: j
                                for i, j in zip(grader_ids, [1.5, 3.0])}
                }
            )
            assigs = test_client.req(
                'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
            )
            grader_assigs2 = defaultdict(lambda: set())
            seen = set()
            for assig in assigs:
                if assig['user']['email'] in seen:
                    continue
                seen.add(assig['user']['email'])
                grader_assigs2[assig['assignee']['id']].add(assig['id'])
            assert (
                len(grader_assigs2[grader_ids[0]]) <
                len(grader_assigs2[grader_ids[1]])
            )
            assert grader_assigs[grader_ids[0]].issuperset(
                grader_assigs2[grader_ids[0]]
            )
            assert grader_assigs[grader_ids[1]].issubset(
                grader_assigs2[grader_ids[1]]
            )
            test_client.req(
                'patch',
                f'/api/v1/assignments/{assignment.id}/divide',
                code,
                result=res,
                data={
                    'graders': {i: j
                                for i, j in zip(grader_ids, [1.5, 3])}
                }
            )
            assert assigs == test_client.req(
                'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
            )

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders': {}
            }
        )
        for assig in test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
        ):
            assert assig['assignee'] is None


def test_divide_non_existing_assignment(
    ta_user, logged_in, test_client, error_template
):
    with logged_in(ta_user):
        test_client.req(
            'patch', f'/api/v1/assignments/0/divide', 404, error_template
        )


@pytest.mark.parametrize('with_works', [True], indirect=True)
def test_reminder_email_divide(
    ta_user,
    logged_in,
    test_client,
    assignment,
    stubmailer,
    monkeypatch_celery,
):
    assig_id = assignment.id
    graders_done_query = m.AssignmentGraderDone.query.filter_by(
        assignment_id=assig_id
    )

    def get_graders():
        with logged_in(ta_user):
            return test_client.req(
                'get',
                f'/api/v1/assignments/{assig_id}/graders/',
                200,
                result=list
            )

    graders = get_graders()

    with logged_in(ta_user):
        graders = get_graders()
        random.shuffle(graders)
        grader_done = graders[0]['id']
        grader_done2 = graders[1]['id']
        print('grader_done:', graders[0])
        print('grader_done2:', graders[1])

        assert len(graders) > 2, (
            'To run this test we '
            'should have atleast 3 graders'
        )

        test_client.req(
            'post',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            204,
        )
        test_client.req(
            'post',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done2}/done',
            204,
        )

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders': {g['id']: 1
                            for g in graders[:2]}
            }
        )

        assert stubmailer.called == 2, (
            'Only the graders that were done should have been mailed'
        )
        assert not graders_done_query.all(), """
        Nobody should be done after this.
        """
        stubmailer.reset()

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders': {g['id']: 1
                            for g in graders[:3]}
            }
        )
        assert not stubmailer.called, (
            'As the grader should have less assignments assigned (1/3 now '
            'instead of 1/2 before) no mail should have been send'
        )
        stubmailer.reset()

        test_client.req(
            'post',
            f'/api/v1/assignments/{assig_id}/graders/{graders[2]["id"]}/done',
            204,
        )

        test_client.req(
            'post',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            204,
        )
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders': {
                    grader_done: 1
                }
            }
        )
        assert stubmailer.called == 1, (
            'Make sure user is mailed even if it had assigned submissions '
            'and new submissions were from graders that were done'
        )

        new_graders = get_graders()
        for g in new_graders:
            if g['id'] in {grader_done, grader_done2}:
                assert not g['done'], (
                    'The done status of grader_done and grader_done2 should '
                    'be reset by the notification emails'
                )
            elif g['id'] == graders[2]['id']:
                assert g['done'], 'The third grader should still be done'
            else:
                assert not g['done'], "All the other graders shouldn't be done"


@pytest.mark.parametrize(
    'with_assignees',
    [['Devin Hillenius'], ['Thomas Schaper', 'Devin Hillenius'], []]
)
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        http_err(error=403)('Stupid1'),
        http_err(error=401)('NOT_LOGGED_IN')
    ],
    indirect=True
)
@pytest.mark.parametrize('with_works', [True, False], indirect=True)
def test_get_all_graders(
    named_user,
    assignment,
    logged_in,
    test_client,
    with_works,
    ta_user,
    with_assignees,
    request,
    error_template,
):
    with logged_in(ta_user):
        graders = []
        for grader in with_assignees:
            graders.append(m.User.query.filter_by(name=grader).one().id)
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders': {g: 1
                            for g in graders}
            }
        )

    with logged_in(named_user):
        marker = request.node.get_marker('http_err')
        code = 200 if marker is None else marker.kwargs['error']
        test_client.req(
            'get',
            f'/api/v1/assignments/{assignment.id}/graders/',
            code,
            result=[
                {
                    'name': 'b',
                    'id': int,
                    'weight': 0,
                    'done': False,
                },
                {
                    'name': 'Devin Hillenius',
                    'id': int,
                    'weight': float('Devin Hillenius' in with_assignees),
                    'done': False,
                },
                {
                    'name': 'Robin',
                    'id': int,
                    'weight': 0,
                    'done': False,
                },
                {
                    'name': 'Thomas Schaper',
                    'id': int,
                    'weight': int('Thomas Schaper' in with_assignees),
                    'done': False,
                },
            ] if marker is None else error_template
        )


@pytest.mark.parametrize('state_is_hidden', [True, False])
@pytest.mark.parametrize('with_works', [True, False, 'single'])
@pytest.mark.parametrize(
    'named_user', [
        http_err(error=403)('admin'),
        http_err(error=401)('NOT_LOGGED_IN'),
        'Devin Hillenius',
        pytest.mark.no_grade(
            pytest.mark.no_others(pytest.mark.no_hidden('Stupid1'))
        ),
    ],
    indirect=True
)
@pytest.mark.parametrize('extended', [True, False])
def test_get_all_submissions(
    with_works,
    state_is_hidden,
    named_user,
    logged_in,
    test_client,
    request,
    assignment,
    error_template,
    extended,
):
    marker = request.node.get_marker('http_err')
    no_hide = request.node.get_marker('no_hidden')
    no_grade = request.node.get_marker('no_grade')

    with logged_in(named_user):
        if no_hide and state_is_hidden:
            code = 403
        elif marker is None:
            code = 200
            works = m.Work.query.filter_by(assignment_id=assignment.id)
            if request.node.get_marker('no_others') is not None:
                works = works.filter_by(user_id=named_user.id)

            res = []
            for work in sorted(
                works, key=lambda w: w.created_at, reverse=True
            ):
                res.append(
                    {
                        'assignee': None if no_hide else work.assignee,
                        'grade': None if no_grade else work.grade,
                        'id': work.id,
                        'user': dict,
                        'created_at': work.created_at.isoformat(),
                    }
                )
                if extended:
                    res[-1]['comment'] = None if no_grade else work.comment
        else:
            code = marker.kwargs['error']

        print(named_user if isinstance(named_user, str) else named_user.name)
        url = f'/api/v1/assignments/{assignment.id}/submissions/'
        if extended:
            url += '?extended'
        test_client.req(
            'get', url, code, result=res if code == 200 else error_template
        )


# yapf: disable
@pytest.mark.parametrize(
    'named_user', ['Thomas Schaper',
                   http_err(error=403)('Stupid1')],
    indirect=True
)
@pytest.mark.parametrize(
    'filename,result', [
        (
            'correct.tar.gz', {
                'Stupid1': {
                        'entries': [{
                                    'name': 'Single file',
                                    'id': int
                                }, {
                                    'name': 'Tuple_file_1',
                                    'id': int
                                }],
                        'name': 'top',
                        'id': int,
                        'username': '0000001',
                },
                'New User': {
                        'entries': [{
                                    'name': 'Single file',
                                    'id': int
                                }, {
                                    'name': 'Tuple_file_3',
                                    'id': int
                                }],
                        'name': 'top',
                        'id': int,
                        'username': '0000003',
                },
                'Stupid2': {
                        'entries': [{
                                    'name': 'Single file',
                                    'id': int
                                }, {
                                    'name': 'Tuple_file_2',
                                    'id': int
                                }],
                        'name': 'top',
                        'id': int,
                        'username': '0000002',
                },
            }
        ),
        (
            'correct_difficult.tar.gz', {
                'Stupid1': {
                        'entries': [{
                                    'name': '__WARNING__',
                                    'id': int,
                                }, {
                                    'name': '__WARNING__ (User)',
                                    'id': int,
                                }, {
                                    'name': 'Single file',
                                    'id': int
                                }, {
                                    'name': 'Tuple_file_1',
                                    'id': int
                                }, {
                                    'name': 'wrong_archive.tar.gz',
                                    'id': int
                                }],
                        'name': 'top',
                        'id': int,
                        'username': '0000001',
                },
                'New User': {
                        'entries': [{
                                    'name': 'Single file',
                                    'id': int
                                }, {
                                    'name': 'Tuple_file_3',
                                    'id': int
                                }],
                        'name': 'top',
                        'id': int,
                        'username': 'GEEN_INT',
                },
                'Stupid2': {
                        'entries': [{
                                    'name': 'Single file',
                                    'id': int
                                }, {
                                    'name': 'tar_file',
                                    'id': int,
                                    'entries': list,
                                }, {
                                    'name': 'Tuple_file_2',
                                    'id': int
                                }],
                        'name': 'top',
                        'id': int,
                        'username': '0000002',
                },
                'Stupid3': {
                        'entries': [{
                                    'name': 'Comment',
                                    'id': int
                                }],
                        'name': 'top',
                        'id': int,
                        'username': '0000004',
                },
            }
        ),
        ('incorrect_date.tar.gz', False),
        ('incorrect_filename.tar.gz', False),
        ('incorrect_missing_files.tar.gz', False),
        ('incorrect_missing_index_files.tar.gz', False),
        ('incorrect_no_archive', False),
    ]
)
# yapf: enable
def test_upload_blackboard_zip(
    test_client, logged_in, named_user, assignment, filename, result,
    error_template, request, ta_user, session, stubmailer
):
    course_id = assignment.course_id

    def get_student_users():
        users = test_client.req(
            'get', f'/api/v1/courses/{course_id}/users/', 200, list
        )
        return set(
            u['User']['name'] for u in users
            if u['CourseRole']['name'] == 'Student'
        )

    marker = request.node.get_marker('http_err')
    with logged_in(named_user):
        if marker is not None:
            code = marker.kwargs['error']
        elif result:
            code = 204
        else:
            code = 400

        if code == 204:
            crole = m.CourseRole.query.filter_by(
                name='Student', course_id=course_id
            ).one()
            session.query(
                m.user_course,
            ).filter(m.user_course.c.course_id == crole.id).delete(False)
            session.commit()
            session.query(m.User).filter_by(name='Stupid1').update(
                {
                    'username': result['Stupid1']['username']
                }
            )
            assert get_student_users() == set()

        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submissions/',
            400 if marker is None else code,
            real_data={},
            result=error_template
        )
        if marker is None:
            assert res['message'].startswith('No file in HTTP')

        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submissions/',
            400 if marker is None else code,
            real_data={'err': (io.BytesIO(b'my file content'), 'ror')},
            result=error_template
        )
        if marker is None:
            assert res['message'].startswith('The parameter name should')

        filename = (
            f'{os.path.dirname(__file__)}/'
            f'../test_data/test_blackboard/{filename}'
        )
        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submissions/',
            code,
            real_data={'file': (filename, 'bb.tar.gz')},
            result=error_template if code != 204 else None
        )
        res = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
        )

        if marker is None and result:
            assert res
            assert len(res) == len(result)
            for item in res:
                assert item['user']['name'] in result
                name = item['user']['name']
                username = result[name]['username']
                del result[name]['username']
                test_client.req(
                    'get',
                    f'/api/v1/submissions/{item["id"]}/files/',
                    200,
                    result=result[name]
                )
                found_us = m.User.query.filter_by(name=name).all()
                assert any(u.username == username for u in found_us)

                with logged_in(ta_user):
                    student_users = get_student_users()
                    print(student_users, result)
                    assert student_users == set(result.keys())
        else:
            assert not res

    assert not stubmailer.called, (
        'As we never divided no users should have been mailed'
    )
    assert not m.AssignmentGraderDone.query.filter_by(
        assignment_id=assignment.id
    ).all(), 'Nobody should be done'


@pytest.mark.parametrize('with_works', [False], indirect=True)
def test_assigning_after_uploading(
    test_client, logged_in, assignment, error_template, ta_user
):
    for user in ['Stupid1', 'Stupid2', 'Stupid3']:
        with logged_in(m.User.query.filter_by(name=user).one()):
            test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/submission',
                201,
                real_data={
                    'file':
                        (
                            f'{os.path.dirname(__file__)}/../test_data/'
                            'test_submissions/multiple_dir_archive.zip',
                            f'single_file_work.zip'
                        )
                },
                result=dict,
            )
    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders':
                    {
                        i.id: 1
                        for i in m.User.query.
                        filter(m.User.name.in_(['Thomas Schaper', 'Robin']))
                    }
            }
        )
        assigs = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
        )
        counts = defaultdict(lambda: 0)
        for assig in assigs:
            counts[assig['assignee']['id']] += 1

    amounts = list(counts.values())
    assert max(amounts) == 2
    assert abs(amounts[0] - amounts[1]) == 1
    counts = defaultdict(lambda: 0)

    with logged_in(m.User.query.filter_by(name=u'Œlµo').one()):
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission',
            201,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../test_data/'
                        'test_submissions/multiple_dir_archive.zip',
                        f'single_file_work.zip'
                    )
            },
            result=dict,
        )

    with logged_in(ta_user):
        olmo_by = None
        for assig in assigs:
            counts[assig['assignee']['id']] += 1
            if assig['user']['name'] == 'Œlµo':
                olmo_by = assig['assignee']['id']

    amounts = list(counts.values())
    assert max(amounts) == 2
    assert abs(amounts[0] - amounts[1]) == 1

    with logged_in(m.User.query.filter_by(name=u'Œlµo').one()):
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission',
            201,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../test_data/'
                        'test_submissions/multiple_dir_archive.zip',
                        f'single_file_work.zip'
                    )
            },
            result=dict,
        )
    with logged_in(ta_user):
        for assig in assigs:
            if assig['user']['name'] == 'Œlµo':
                assert olmo_by == assig['assignee']['id']


@pytest.mark.parametrize('with_works', [False], indirect=True)
def test_reset_grader_status_after_upload(
    test_client, logged_in, assignment, error_template, ta_user, session,
    stubmailer, monkeypatch_celery
):
    graders_done_q = m.AssignmentGraderDone.query.filter_by(
        assignment_id=assignment.id
    )
    grader_done = session.query(m.User).filter_by(name='Robin').one().id

    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders': {
                    grader_done: 1
                }
            }
        )
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/graders/{grader_done}/done',
            204,
        )

    assert not stubmailer.called, 'No graders should have been notified now'
    assert len(graders_done_q.all()), 'But one should be done'
    stubmailer.reset()

    for user in session.query(m.User).filter(
        m.User.name.in_([
            'Œlµo',
            'Stupid1',
        ])
    ):
        with logged_in(user):
            test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/submission',
                201,
                real_data={
                    'file':
                        (
                            f'{os.path.dirname(__file__)}/../test_data/'
                            'test_submissions/multiple_dir_archive.zip',
                            f'single_file_work.zip'
                        )
                },
                result=dict,
            )

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/assignments/{assignment.id}/graders/',
            200,
        )
        for g in res:
            if g['id'] == grader_done:
                assert not g['done'], 'Grader should not be done anymore'
            else:
                assert not g['done'], 'Other grader should not be done anyway'

    assert stubmailer.called == 1, 'Grader should be notified once'
    stubmailer.reset()

    olmo = m.User.query.filter_by(name=u'Œlµo').one()
    with logged_in(olmo):
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission',
            201,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../test_data/'
                        'test_submissions/multiple_dir_archive.zip',
                        f'single_file_work.zip'
                    )
            },
            result=dict,
        )
    assert not stubmailer.called, """
    Grader was not done so no emails should be send
    """
    assert not graders_done_q.filter_by(
        user_id=olmo.id,
    ).all(), 'Olmo should not be assigned.'


@pytest.mark.parametrize('filename', [
    'large.tar.gz',
])
def test_assign_after_blackboard_zip(
    test_client,
    logged_in,
    assignment,
    filename,
    error_template,
    request,
    ta_user,
    stubmailer,
    monkeypatch_celery,
):
    graders_done_q = m.AssignmentGraderDone.query.filter_by(
        assignment_id=assignment.id
    )
    with logged_in(ta_user):
        graders = m.User.query.filter(
            m.User.name.in_(['Thomas Schaper', 'Robin'])
        ).order_by(m.User.name)
        grader_done = graders[0].id

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders': {i.id: j
                            for i, j in zip(graders, [1, 2])}
            }
        )
        test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/graders/{grader_done}/done',
            204
        )

        filename = (
            f'{os.path.dirname(__file__)}/'
            f'../test_data/test_blackboard/{filename}'
        )

        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submissions/',
            204,
            real_data={'file': (filename, 'bb.tar.gz')},
        )

        assert stubmailer.called == 1, """
        Only one grader was set as done, so only one should have been called
        """
        assert not graders_done_q.all(), 'Nobody should be done anymore'
        stubmailer.reset()

        res = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
        )
        amounts = defaultdict(lambda: 0)
        lookup = {}
        for sub in res:
            amounts[sub['assignee']['id']] += 1
            lookup[sub['user']['username']] = sub['assignee']['id']

        amounts_list = sorted(list(amounts.values()))
        assert amounts_list[1] / amounts_list[0] == 2

        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submissions/',
            204,
            real_data={'file': (filename, 'bb.tar.gz')},
        )

        assert not stubmailer.called, (
            'The grader_done should have already been reset to not done so '
            'no emails should have been send.'
        )

        res = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
        )
        for sub in res:
            print(sub['id'])
            assert lookup[sub['user']['username']] == sub['assignee']['id']


# yapf: disable
@pytest.mark.parametrize(
    'name,entries,dirname,exts,ignored,entries_delete', [
        (
            'multiple_dir_archive', [
                {
                    'id': int,
                    'name': 'dir',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }, {
                    'id': int,
                    'name': 'dir2',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }
            ],
            'multiple_dir_archive', ['.tar.gz', '.zip'],
            [
                    'dir2/single_file_work',
                    'dir2/single_file_work_copy',
                    'dir/single_file_work',
            ],
            {
                'name': 'dir',
                'id': int,
                'entries': [{'name': 'single_file_work_copy', 'id': int}]
            }
        ),
        (
            'gitignore_archive', [
                {
                    'id': int,
                    'name': 'bb[]',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }, {
                    'id': int,
                    'name': 'dir',
                    'entries': [{
                        'id': int,
                        'name': '\\wow'
                    }, {
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }, {
                        'id': int,
                        'name': 'something'
                    }, {
                        'id': int,
                        'name': 'wow\wowsers'
                    }]
                }, {
                    'id': int,
                    'name': 'sub',
                    'entries': [{
                        'id': int,
                        'name': 'dir',
                        'entries': [{
                            'id': int,
                            'name': 'file'
                        }, {
                            'id': int,
                            'name': 'file2'
                        }]
                    }]
                }, {
                    'id': int,
                    'name': 'dir2',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }, {
                    'id': int,
                    'name': 'dirl',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }, {
                    'id': int,
                    'name': 'la',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }, {
                    'id': int,
                    'name': 'za',
                    'entries': [{
                        'id': int,
                        'name': 'single_file_work'
                    }, {
                        'id': int,
                        'name': 'single_file_work_copy'
                    }]
                }
            ],
            'gitignore_archive', ['.tar.gz'],
            [
                'dir/\\wow',
                'dir2/single_file_work',
                'dir2/single_file_work_copy',
                'dirl/single_file_work',
                'dirl/single_file_work_copy',
                'za/single_file_work',
                'za/single_file_work_copy',
                'la/single_file_work',
                'la/single_file_work_copy',
                'dir/single_file_work',
                'dir/something',
                'dir/wow\\wowsers',
                'sub/dir/file',
                'sub/dir/file2',
                'bb[]/single_file_work',
                'bb[]/single_file_work_copy',
            ],
            {'name': 'gitignore_archive',
             'id': int,
             'entries': [{
                 'name': 'dir',
                 'id': int,
                 'entries': [{'name': 'single_file_work_copy', 'id': int}]
             }, {
                 'name': 'sub',
                 'id': int,
                 'entries': [{'name': 'dir', 'id': int, 'entries': []}]
             }]}
        )
    ]
)
@pytest.mark.parametrize('named_user', ['Stupid1'],
                         indirect=True)
# yapf: enable
def test_ignored_upload_files(
    named_user, exts, test_client, logged_in, assignment, name, entries,
    dirname, error_template, ta_user, ignored, entries_delete
):
    entries.sort(key=lambda a: a['name'])

    with logged_in(ta_user):
        assig = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}', 200
        )
        assert assig['cgignore'] is None

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}',
            204,
            data={
                'ignore':
                    '# single_file_work_copy\n'
                    '/dir[l2]/ \n'
                    'single_file_work*\n'
                    '[^dbs]*/\n'
                    '[!dsb]*/\n'
                    'somethin?\n'
                    'wow\\wowsers\n'
                    '!*copy\n'
                    'bb[]/\n'
                    '**/file\n'
                    'sub/**/file2\n'
                    '\\\\wow\n'
            }
        )
        assig = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}', 200
        )
        assert isinstance(assig['cgignore'], str)

    for ext in exts:
        with logged_in(named_user):
            res = test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/submission?'
                'ignored_files=error',
                400,
                real_data={
                    'file':
                        (
                            f'{os.path.dirname(__file__)}/../test_data/'
                            f'test_submissions/{name}{ext}', f'{name}{ext}'
                        )
                },
                result={
                    'code': 'INVALID_FILE_IN_ARCHIVE',
                    'message': str,
                    'description': str,
                    'invalid_files': list
                }
            )
            assert set(ignored) == set(r[0] for r in res['invalid_files'])

            res = test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/submission?'
                'ignored_files=ignore',
                201,
                real_data={
                    'file':
                        (
                            f'{os.path.dirname(__file__)}/../test_data/'
                            f'test_submissions/{name}{ext}', f'{name}{ext}'
                        )
                },
            )
            test_client.req(
                'get',
                f'/api/v1/submissions/{res["id"]}/files/',
                200,
                result={
                    'entries': entries,
                    'id': int,
                    'name': f'{dirname}'
                }
            )

            res = test_client.req(
                'post',
                f'/api/v1/assignments/{assignment.id}/submission?'
                'ignored_files=delete',
                201,
                real_data={
                    'file':
                        (
                            f'{os.path.dirname(__file__)}/../test_data/'
                            f'test_submissions/{name}{ext}', f'{name}{ext}'
                        )
                },
            )
            test_client.req(
                'get',
                f'/api/v1/submissions/{res["id"]}/files/',
                200,
                result=entries_delete
            )

    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}',
            204,
            data={
                'ignore': '*'
            }
        )

    with logged_in(named_user):
        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission?'
            'ignored_files=delete',
            400,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../test_data/'
                        f'test_submissions/{name}{ext}', f'{name}{ext}'
                    )
            },
        )

    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}',
            204,
            data={
                'ignore': '*\n!dir/'
            }
        )

    with logged_in(named_user):
        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission?'
            'ignored_files=delete',
            201,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../test_data/'
                        f'test_submissions/{name}{ext}', f'{name}{ext}'
                    )
            },
        )
        test_client.req(
            'get',
            f'/api/v1/submissions/{res["id"]}/files/',
            200,
            result={'name': 'dir',
                    'id': int,
                    'entries': list},
        )

    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}',
            204,
            data={
                'ignore': '*'
            }
        )

    with logged_in(named_user):
        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission?'
            'ignored_files=error',
            400,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../test_data/'
                        f'test_submissions/{name}{ext}', f'{name}'
                    )
            },
            result={
                'code': 'INVALID_FILE_IN_ARCHIVE',
                'message': str,
                'description': str,
                'invalid_files': list
            }
        )
        assert set([f'{name}']) == set(r[0] for r in res['invalid_files'])

        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission?'
            'ignored_files=delete',
            400,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../test_data/'
                        f'test_submissions/{name}{ext}', f'{name}'
                    )
            },
            result={
                'code': 'NO_FILES_SUBMITTED',
                'message': str,
                'description': str,
            }
        )

    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}',
            204,
            data={
                'ignore': '# Nothing'
            }
        )

    with logged_in(named_user):
        res = test_client.req(
            'post',
            f'/api/v1/assignments/{assignment.id}/submission?'
            'ignored_files=error',
            201,
            real_data={
                'file':
                    (
                        f'{os.path.dirname(__file__)}/../test_data/'
                        f'test_submissions/{name}{ext}', f'{name}'
                    )
            },
        )
        test_client.req(
            'get',
            f'/api/v1/submissions/{res["id"]}/files/',
            200,
            result={'name': 'top',
                    'id': int,
                    'entries': list},
        )


@pytest.mark.parametrize('with_works', [True], indirect=True)
def test_warning_grader_done(
    test_client, logged_in, request, assignment, ta_user, session,
    monkeypatch_celery
):
    assig_id = assignment.id

    def get_graders():
        with logged_in(ta_user):
            return test_client.req(
                'get',
                f'/api/v1/assignments/{assig_id}/graders/',
                200,
                result=list
            )

    graders = get_graders()
    random.shuffle(graders)
    grader_done = graders[-1]["id"]

    with logged_in(ta_user):
        _, rv = test_client.req(
            'post',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            204,
            result=None,
            include_response=True
        )
        assert 'Warning' not in rv.headers

        test_client.req(
            'delete',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            204,
            result=None,
            include_response=True
        )

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assig_id}/divide',
            204,
            result=None,
            data={
                'graders': {
                    grader_done: 1
                }
            }
        )

        _, rv = test_client.req(
            'post',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            204,
            result=None,
            include_response=True
        )
        assert 'Warning' in rv.headers

        test_client.req(
            'delete',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            204,
            result=None,
            include_response=True
        )

        session.query(m.Work).filter_by(
            assigned_to=grader_done, assignment_id=assig_id
        ).update({
            '_grade': 6
        })
        session.commit()
        _, rv = test_client.req(
            'post',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            204,
            result=None,
            include_response=True
        )
        assert 'Warning' not in rv.headers


@pytest.mark.parametrize(
    'named_user,toggle_self', [
        http_err(error=403)(('admin', None)),
        http_err(error=401)(('NOT_LOGGED_IN', None)),
        ('Devin Hillenius', True),
        ('Devin Hillenius', False),
        http_err(error=403)(('Stupid1', None)),
    ],
    indirect=['named_user']
)
def test_grader_done(
    named_user, error_template, test_client, logged_in, request, assignment,
    ta_user, session, stubmailer, toggle_self, monkeypatch_celery,
    stub_function_class, monkeypatch
):
    # Please note that we DO NOT monkey patch celery away here. This is because
    # some logic might be implemented in the celery task (this has already
    # happened a few times during development). We simply make sure the mailer
    # is called.
    stubtask = stub_function_class(
        ret_func=psef.tasks.send_grader_status_mail, with_args=True
    )
    monkeypatch.setattr(psef.tasks, 'send_grader_status_mail', stubtask)

    def assert_remind_email(called):
        assert stubmailer.called == called, (
            'Email should{}have been called'.format(
                ' not ' if not called else ' ',
            )
        )
        # Make sure the task is only called when the email should be send
        assert stubtask.called == called, (
            'Celery task should{}have been called'.format(
                ' not ' if not called else ' ',
            )
        )

        if called:
            assert len(stubtask.args) == 1, 'Task should be called once only'

        stubmailer.reset()
        stubtask.reset()

    assig_id = assignment.id
    course_id = assignment.course_id

    code = 204
    marker = request.node.get_marker('http_err')
    if marker is not None:
        code = marker.kwargs['error']

    err = code >= 400

    def get_graders():
        with logged_in(ta_user):
            return test_client.req(
                'get',
                f'/api/v1/assignments/{assig_id}/graders/',
                200,
                result=list
            )

    graders = get_graders()
    random.shuffle(graders)

    assert len(graders) > 1, 'We need at least 2 graders for this test'

    if not isinstance(named_user, str):
        if graders[-1]['id'] == named_user.id:
            graders[-1], graders[0] = graders[0], graders[-1]

    assert all(not g['done'] for g in graders
               ), 'Make sure all graders are not done by default'
    if toggle_self:
        grader_done = named_user.id
    else:
        grader_done = graders[-1]["id"]

    with logged_in(named_user):
        test_client.req(
            'post',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            code,
            result=error_template if err else None
        )

    graders = get_graders()
    if err:
        assert all(not g['done'] for g in graders
                   ), 'Make sure all graders are still not done'
    else:
        assert all(g['done'] == (g['id'] == grader_done)
                   for g in graders), 'Make sure only changed grader is done'
        with logged_in(named_user):
            # Make sure you cannot reset this grader to done
            test_client.req(
                'post',
                f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
                400,
                result=error_template,
            )

    with logged_in(named_user):
        test_client.req(
            'delete',
            f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
            code,
            result=error_template if err else None
        )

    if not err:
        # Make sure an email was send if and only if we did not toggle
        # ourselves
        assert_remind_email(called=not toggle_self)

        with logged_in(named_user):
            # Make sure you cannot reset this grader to not done
            test_client.req(
                'delete',
                f'/api/v1/assignments/{assig_id}/graders/{grader_done}/done',
                400,
                result=error_template,
            )
        # When an error occurs we should not notify anybody
        assert_remind_email(False)
    else:
        # When an error occurred we should not send emails
        assert_remind_email(False)

    graders = get_graders()
    assert all(not g['done']
               for g in graders), 'Make sure all graders are again not done'

    if not err:
        new_user = m.User.query.filter_by(name='Stupid1').first()
        perm = m.Permission.query.filter_by(name='can_grade_work').first()
        new_user.courses[course_id].set_permission(perm, True)
        session.commit()

        with logged_in(new_user):
            # This should be the case for adding and deleting permissions
            for meth in ['post', 'delete']:
                # This user cannot set other users
                test_client.req(
                    meth,
                    f'/api/v1/assignments/{assig_id}/graders'
                    f'/{grader_done}/done',
                    403,
                    result=error_template,
                )
                # But this user can set his own perms
                test_client.req(
                    meth,
                    f'/api/v1/assignments/{assig_id}/graders'
                    f'/{new_user.id}/done',
                    204,
                    result=None,
                )

            # Errors should not trigger emails and neither should toggling
            # yourself
            assert_remind_email(False)


@pytest.mark.parametrize(
    'named_user', [
        http_err(error=403)('admin'),
        http_err(error=401)('NOT_LOGGED_IN'),
        'Devin Hillenius',
        http_err(error=403)('Stupid1'),
    ],
    indirect=True
)
@pytest.mark.parametrize(
    'with_type,with_time', [
        (True, True),
        (False, True),
        (True, False),
        (True, 'wrong'),
        ('wrong', True),
    ]
)
@pytest.mark.parametrize('with_works', [True], indirect=True)
def test_reminder_email(
    test_client, session, error_template, ta_user, monkeypatch, app,
    stub_function_class, assignment, named_user, with_type, with_time, request,
    logged_in
):
    assig_id = assignment.id

    all_graders = m.User.query.filter(
        m.User.name.in_([
            'Thomas Schaper',
            'Devin Hillenius',
            'Robin',
            'b',
        ])
    ).all()
    graders = all_graders[2:4]
    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            result=None,
            data={
                'graders': {u.id: 1
                            for u in graders}
            }
        )

        sub = assignment.get_all_latest_submissions()[0]
        test_client.req(
            'patch',
            f'/api/v1/submissions/{sub.id}/grader',
            204,
            data={'user_id': all_graders[0].id},
        )
    graders.append(all_graders[0])

    # Monkeypatch the actual mailer away as we don't really want to send emails
    mailer = stub_function_class()

    def test_mail(users):
        psef.tasks._send_reminder_mail_1(assig_id)

        user_mails = [u.email for u in users]
        user_mails.sort()

        for body, subject, recipients, conn in mailer.args:
            assert body, 'A non empty body is required'
            assert subject, 'A non empty subject is required'
            assert len(recipients) == 1, (
                'Make sure only one recipients '
                'is used per email'
            )
            assert conn, 'Make sure a connection was passed'

        assert sorted(
            [arg[2][0] for arg in mailer.args]
        ) == user_mails, ('Make sure only the correct'
                          ' users were emailed')

    monkeypatch.setattr(psef.mail, '_send_mail', mailer)

    class StubTask:
        def __init__(self, id):
            self.id = id

    # Monkey patch celery away as an ETA task will block the test for a long
    # time.
    task = stub_function_class(lambda: StubTask(str(uuid.uuid4())))
    monkeypatch.setattr(psef.tasks, 'send_reminder_mails', task)
    revoker = stub_function_class()
    monkeypatch.setattr(psef.tasks.celery.control, 'revoke', revoker)

    time = datetime.datetime.utcnow() + datetime.timedelta(days=1)
    data = {
        'reminder_type': 'assigned_only',
        'reminder_time': time.isoformat(),
    }
    code = 204

    if not with_type:
        del data['reminder_type']
        code = 400
    if not with_time:
        del data['reminder_time']
        code = 400
    if with_type == 'wrong':
        data['reminder_type'] = 'WRONG_TYPE'
        code = 400
    if with_time == 'wrong':
        data['reminder_time'] = 'WRONG_TIME'
        code = 400

    marker = request.node.get_marker('http_err')
    if marker is not None:
        code = marker.kwargs['error']

    err = code >= 400

    def check_assig_state():
        with logged_in(ta_user):
            assig = test_client.req(
                'get', f'/api/v1/assignments/{assig_id}', 200, result=dict
            )
            assert assig['reminder_type'] == data[
                'reminder_type'
            ], 'Make sure state is the same as in the data send'
            assert assig['reminder_time'] == data[
                'reminder_time'
            ], 'Make sure time is the same as in the data send'

    with logged_in(named_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assig_id}',
            code,
            data=data,
            result=error_template if err else None
        )

        assert not revoker.called, 'No task should have been revoked'
        assert not mailer.called, 'The mailer should not be called directly'
        assert task.called != err, "Schedule the task if no there's no error"

        if err:
            return
        check_assig_state()
        test_mail(graders)

        assert task.args == [((assig_id, ), )
                             ], 'The correct task should be scheduled.'
        assert task.kwargs == [{
            'eta': time
        }], 'The time should be preserved directly.'
        task_id = task.rets[-1].id

        revoker.reset()
        task.reset()
        mailer.reset()

        data['reminder_type'] = 'none'

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assig_id}',
            code,
            data=data,
            result=None
        )

        check_assig_state()
        assert revoker.called, 'The previous task should be revoked'
        assert not mailer.called, 'The mailer should not be called directly'
        assert not task.called, (
            'Nothing should be scheduled as the type '
            'was none'
        )

        assert revoker.args == [(task_id, )
                                ], 'Assert the correct task was revoked'

        test_mail([])

        revoker.reset()
        task.reset()
        mailer.reset()

        data['reminder_type'] = 'all_graders'

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assig_id}',
            code,
            data=data,
            result=None
        )
        check_assig_state()
        assert not revoker.called, (
            'The previous task should be not be revoked '
            'as the type was none'
        )
        assert not mailer.called, 'The mailer should not be called'
        assert task.called, 'A new task should be scheduled '
        test_mail(all_graders)

        mailer.reset()

        test_client.req(
            'post',
            (
                f'/api/v1/assignments/{assig_id}/'
                f'graders/{all_graders[-1].id}/done'
            ),
            204,
            result=None,
        )
        # Make sure done grader will not get an email.
        test_mail(all_graders[:-1])

        # This date is not far enough in the future so it should error
        data['reminder_time'] = datetime.datetime.utcnow().isoformat()
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assig_id}',
            400,
            data=data,
            result=error_template
        )

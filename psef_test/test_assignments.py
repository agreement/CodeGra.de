import io
import os
import copy
import json
import datetime
from collections import defaultdict
from functools import reduce

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
                'course': dict,
                'whitespace_linter': False,
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
        is_logged_in = isinstance(named_user, m.User)
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
    'item_description', [err400(None), 'new idesc',
                         err400(5)]
)
@pytest.mark.parametrize('item_header', [err400(None), 'new ihead', err400(5)])
@pytest.mark.parametrize('item_points', [err400(None), 5.3, 11, err400('Wow')])
@pytest.mark.parametrize(
    'row_description', [err400(None), 'new rdesc',
                        err400(5)]
)
@pytest.mark.parametrize(
    'row_header', [err400(None), 'new rheader',
                   err400(5)]
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
    'item_description', [err400(None), 'new idesc',
                         err400(5)]
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
    'item_description', [err400(None), 'You did well',
                         err400(5)]
)
@pytest.mark.parametrize(
    'item_header', [err400(None), 'You very well',
                    err400(5)]
)
@pytest.mark.parametrize(
    'item_points', [err400(None), 5.3, 5, 11,
                    err400('Wow')]
)
@pytest.mark.parametrize(
    'row_description', [err400(None), 'A row desc',
                        err400(5)]
)
@pytest.mark.parametrize(
    'row_header', [err400(None), 'A row header',
                   err400(5)]
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
                data={'rows': [row]}
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
            data={'rows': [rubric]}
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
            data={'rows': [rubric]}
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
                false_val = False if named_user.name == 'Stupid1' else None
                res = test_client.req(
                    'post',
                    f'/api/v1/assignments/{assignment.id}/submission',
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
                        'assignee': false_val,
                        'grade': false_val,
                        'comment': false_val,
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
                    data={'graders': d}
                )

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            code,
            result=res,
            data={'graders': {i: 1
                              for i in grader_ids}}
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
                len(grader_assigs[grader_ids[0]]) ==
                len(grader_assigs[grader_ids[1]])
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
            assert grader_assigs[grader_ids[0]
                                 ].issuperset(grader_assigs2[grader_ids[0]])
            assert grader_assigs[grader_ids[1]
                                 ].issubset(grader_assigs2[grader_ids[1]])
            test_client.req(
                'patch',
                f'/api/v1/assignments/{assignment.id}/divide',
                code,
                result=res,
                data={'graders': {i: j
                                  for i, j in zip(grader_ids, [1.5, 3])}}
            )
            assert assigs == test_client.req(
                'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
            )

        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={'graders': {}}
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
            data={'graders': {g: 1
                              for g in graders}}
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
                },
                {
                    'name': 'Devin Hillenius',
                    'id': int,
                    'weight': float('Devin Hillenius' in with_assignees)
                },
                {
                    'name': 'Robin',
                    'id': int,
                    'weight': 0,
                },
                {
                    'name': 'Thomas Schaper',
                    'id': int,
                    'weight': int('Thomas Schaper' in with_assignees)
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
        pytest.mark.
        no_grade(pytest.mark.no_others(pytest.mark.no_hidden('Stupid1'))),
    ],
    indirect=True
)
def test_get_all_submissions(
    with_works, state_is_hidden, named_user, logged_in, test_client, request,
    assignment, error_template
):
    marker = request.node.get_marker('http_err')
    no_hide = request.node.get_marker('no_hidden')
    no_grade = request.node.get_marker('no_grade')

    with logged_in(named_user):
        if no_hide and state_is_hidden:
            code = 403
        elif marker is None:
            code = 200
            res = m.Work.query.filter_by(assignment_id=assignment.id)
            if request.node.get_marker('no_others') is not None:
                res = res.filter_by(user_id=named_user.id)

            res = [
                {
                    'assignee': False if no_hide else r.assignee,
                    'grade': False if no_grade else r.grade,
                    'comment': False if no_grade else r.comment,
                    'id': r.id,
                    'user': dict,
                    'created_at': r.created_at.isoformat(),
                }
                for r in
                sorted(res.all(), key=lambda el: el.created_at, reverse=True)
            ]
        else:
            code = marker.kwargs['error']

        print(named_user if isinstance(named_user, str) else named_user.name)
        test_client.req(
            'get',
            f'/api/v1/assignments/{assignment.id}/submissions/',
            code,
            result=res if code == 200 else error_template
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
                                    'name': 'Single file',
                                    'id': int
                                }, {
                                    'name': 'Tuple_file_1',
                                    'id': int
                                }, {
                                    'name': '__WARNING__',
                                    'id': int,
                                }, {
                                    'name': '__WARNING__ (User)',
                                    'id': int,
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
                        'username': '0000003',
                },
                'Stupid2': {
                        'entries': [{
                                    'name': 'Single file',
                                    'id': int
                                }, {
                                    'name': 'Tuple_file_2',
                                    'id': int
                                }, {
                                    'name': 'tar_file',
                                    'id': int,
                                    'entries': list,
                                }],
                        'name': 'top',
                        'id': int,
                        'username': '0000002',
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
    error_template, request
):
    marker = request.node.get_marker('http_err')
    with logged_in(named_user):
        if marker is not None:
            code = marker.kwargs['error']
        elif result:
            code = 204
        else:
            code = 400

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
        else:
            assert not res


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
):
    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/assignments/{assignment.id}/divide',
            204,
            data={
                'graders':
                    {
                        i.id: j
                        for i, j in zip(
                            m.User.query.filter(
                                m.User.name.in_(['Thomas Schaper', 'Robin'])
                            ).order_by(m.User.name), [1, 2]
                        )
                    }
            }
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
        res = test_client.req(
            'get', f'/api/v1/assignments/{assignment.id}/submissions/', 200
        )
        for sub in res:
            print(sub['id'])
            assert lookup[sub['user']['username']] == sub['assignee']['id']

import io
import zipfile

import pytest

import psef.models as m

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error


@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=401)('NOT_LOGGED_IN'),
        perm_error(error=403)('admin'),
        perm_error(error=403)('Stupid1'),
    ],
    indirect=True
)
@pytest.mark.parametrize(
    'grade', [
        data_error(-1),
        data_error(11),
        data_error('err'),
        data_error(None),
        4,
    ]
)
@pytest.mark.parametrize(
    'feedback', [
        data_error(1),
        data_error(None),
        'Goed gedaan!',
    ]
)
def test_patch_submission(
    assignment_real_works, named_user, test_client, logged_in, request, grade,
    feedback, ta_user, error_template
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif data_err:
        error = 400
    else:
        error = False

    data = {}
    if grade is not None:
        data['grade'] = grade
    if feedback is not None:
        data['feedback'] = feedback

    with logged_in(named_user):
        test_client.req(
            'patch',
            f'/api/v1/submissions/{work_id}',
            error or 204,
            data=data,
            result=error_template if error else None,
        )

    with logged_in(ta_user):
        test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}',
            200,
            result={
                'id': work_id,
                'assignee': None,
                'user': dict,
                'created_at': str,
                'grade': None if error else grade,
                'comment': None if error else feedback,
            }
        )


def test_patch_non_existing_submission(
    ta_user, test_client, logged_in, error_template
):
    with logged_in(ta_user):
        test_client.req(
            'patch',
            f'/api/v1/submissions/0',
            404,
            data={'grade': 4,
                  'feedback': 'wow!'},
            result=error_template
        )


@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=401)('NOT_LOGGED_IN'),
        perm_error(error=403)('admin'),
        perm_error(error=403, can_get=True)('Stupid1'),
    ],
    indirect=True
)
def test_selecting_rubric(
    named_user, request, test_client, logged_in, error_template, ta_user,
    assignment_real_works, session
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
        can_get_rubric = perm_err.kwargs.get('can_get', False)
    else:
        can_get_rubric = True
        error = False

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
            'description': 'My description2',
            'items': [{
                'description': '1points',
                'points': 1
            }, {
                'description': '2points',
                'points': 2,
            }]
        }]
    }  # yapf: disable
    max_points = 12

    with logged_in(ta_user):
        rubric = test_client.req(
            'put',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            204,
            data=rubric
        )
        rubric = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/rubrics/',
            200,
            result={
                'rubrics': list,
                'selected': [],
                'points': {
                    'max': max_points,
                    'selected': 0
                }
            }
        )['rubrics']

    def get_rubric_item(head, desc):
        for row in rubric:
            if row['header'] == head:
                for item in row['items']:
                    if item['description'] == desc:
                        return item

    with logged_in(named_user):
        to_select = [
            get_rubric_item('My header', '10points'),
            get_rubric_item('My header', '5points'),
            get_rubric_item('My header2', '2points')
        ]
        points = [10, 5, 5 + 2]
        result_point = points[-1]
        for item, point in zip(to_select, points):
            test_client.req(
                'patch',
                f'/api/v1/submissions/{work_id}/rubricitems/{item["id"]}',
                error if error else 201,
                result=error_template if error else {
                    'rubrics': rubric,
                    'selected': list,
                    'points': {
                        'max': max_points,
                        'selected': point
                    }
                }
            )

        res = {'rubrics': rubric}
        if not error:
            res.update(
                {
                    'selected': list,
                    'points': {
                        'max': max_points,
                        'selected': result_point
                    }
                }
            )

        test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/rubrics/',
            200 if can_get_rubric else error,
            result=res if can_get_rubric else error_template
        )

        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}',
            200 if can_get_rubric else error,
        )
        if not error:
            assert res['grade'] == pytest.approx(
                result_point / max_points * 10
            )


@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
def test_selecting_wrong_rubric(
    request,
    test_client,
    logged_in,
    error_template,
    ta_user,
    assignment_real_works,
    session,
    course_name,
):
    assignment, work = assignment_real_works
    work_id = work['id']
    course = m.Course.query.filter_by(name=course_name).one()

    other_assignment = m.Assignment(name='OTHER ASSIGNMENT', course=course)
    other_work = m.Work(assignment=other_assignment)
    session.add(other_assignment)
    session.add(other_work)
    session.commit()
    other_work_id = other_work.id

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
        }]
    }  # yapf: disable

    with logged_in(ta_user):
        rubric = test_client.req(
            'put',
            f'/api/v1/assignments/{assignment.id}/rubrics/',
            204,
            data=rubric
        )
        rubric = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/rubrics/',
            200,
        )['rubrics']

        test_client.req(
            'patch',
            f'/api/v1/submissions/{other_work_id}/'
            f'rubricitems/{rubric[0]["items"][0]["id"]}',
            400,
            result=error_template
        )


@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        'Stupid1',
        perm_error(error=403)('Stupid2'),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=True
)
@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
def test_get_dir_contents(
    request, test_client, logged_in, named_user, error_template,
    assignment_real_works
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            error or 200,
            result=error_template if error else {
                'entries': [{
                    'id': int,
                    'name': 'test.py'
                }],
                'id': int,
                'name': 'test_flake8'
            }
        )
        if not error:
            test_client.req(
                'get',
                f'/api/v1/submissions/{work_id}/files/',
                200,
                query={'file_id': res["id"]},
                result=res,
            )

            test_client.req(
                'get',
                f'/api/v1/submissions/{work_id}/files/',
                400,
                query={'file_id': res["entries"][0]["id"]},
                result=error_template
            )

            test_client.req(
                'get',
                f'/api/v1/submissions/{work_id}/files/',
                404,
                query={'file_id': -1},
                result=error_template
            )


@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        'Stupid1',
        perm_error(error=401)('NOT_LOGGED_IN'),
        perm_error(error=403)('admin'),
        perm_error(error=403)('Stupid3'),
    ],
    indirect=True
)
@pytest.mark.parametrize(
    'filename', ['../test_submissions/multiple_dir_archive.zip'],
    indirect=True
)
def test_get_zip_file(
    test_client, logged_in, assignment_real_works, error_template, named_user,
    request
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        res = test_client.get(
            f'/api/v1/submissions/{work_id}',
            query_string={'type': 'zip'},
        )
        if error:
            res = test_client.req(
                'get',
                f'/api/v1/submissions/{work_id}',
                error,
                result=error_template,
                query={'type': 'zip'},
            )
        else:
            res.status_code == 200
            files = zipfile.ZipFile(io.BytesIO(res.get_data())).infolist()
            files = set(f.filename for f in files)
            assert files == set(
                [
                    'multiple_dir_archive/dir/single_file_work',
                    'multiple_dir_archive/dir/single_file_work_copy',
                    'multiple_dir_archive/dir2/single_file_work',
                    'multiple_dir_archive/dir2/single_file_work_copy',
                ]
            )

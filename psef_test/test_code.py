import datetime

import pytest

import psef.models as m

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error
late_error = pytest.mark.late_error


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
@pytest.mark.parametrize('filename', ['test_flake8.tar.gz'], indirect=True)
def test_get_code_metadata(
    named_user, assignment_real_works, test_client, request, error_template,
    ta_user, logged_in
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': [{
                    'id': int,
                    'name': 'test.py'
                }],
                'id': int,
                'name': 'test_flake8'
            }
        )

    with logged_in(named_user):
        test_client.req(
            'get',
            f'/api/v1/code/{res["id"]}',
            error if error else 200,
            result=error_template if error else {
                'name': 'test_flake8',
                'extension': '',
                'is_directory': True,
                'id': int,
            },
            query={'type': 'metadata'}
        )

        test_client.req(
            'get',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            error if error else 200,
            result=error_template if error else {
                'name': 'test',
                'extension': 'py',
                'is_directory': False,
                'id': int,
            },
            query={'type': 'metadata'}
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
    'filename,content', [
        ('test_flake8.tar.gz', 'def a(b):\n\tprint ( 5 )\n'),
        data_error(error=410)(
            (
                '../test_submissions/single_symlink_archive.tar.gz',
                'SHOULD ERROR!'
            )
        ),
        data_error(error=400)(
            ('../test_submissions/nested_dir_archive.tar.gz', 'SHOULD ERROR!')
        ),
        data_error(error=400)(
            ('../test_submissions/pdf_in_dir_archive.tar.gz', 'SHOULD ERROR!')
        )
    ],
    indirect=['filename']
)
def test_get_code_plaintext(
    named_user, assignment_real_works, test_client, request, error_template,
    ta_user, logged_in, content
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif data_err:
        error = data_err.kwargs['error']
    else:
        error = False

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )

    with logged_in(named_user):
        if error:
            test_client.req(
                'get',
                f'/api/v1/code/{res["entries"][0]["id"]}',
                error,
                result=error_template
            )
        else:
            res = test_client.get(f'/api/v1/code/{res["entries"][0]["id"]}')
            assert res.status_code == 200
            assert res.get_data(as_text=True) == content


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
    'filename', [
        '../test_submissions/pdf_in_dir_archive.tar.gz',
    ],
    indirect=['filename']
)
def test_get_pdf(
    named_user, assignment_real_works, test_client, request, error_template,
    ta_user, logged_in
):
    assignment, work = assignment_real_works
    work_id = work['id']

    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )

    with logged_in(named_user):
        if error:
            test_client.req(
                'get',
                f'/api/v1/code/{res["entries"][0]["id"]}',
                error,
                query={'type': 'pdf'},
                result=error_template
            )
        else:
            res = test_client.get(
                f'/api/v1/code/{res["entries"][0]["id"]}',
                query_string={'type': 'pdf'}
            )
            assert res.status_code == 200
            assert res.headers['Content-Type'] == 'application/pdf'
            assert res.headers['Content-Disposition'].startswith('inline')


@pytest.mark.parametrize(
    'filename', ['../test_submissions/single_dir_archive.zip'], indirect=True
)
def test_delete_code_as_ta(
    assignment_real_works, test_client, request, error_template, ta_user,
    logged_in, session
):
    assignment, work = assignment_real_works
    work_id = work['id']

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )
        assert len(res['entries']) == 2

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            403,
            result=error_template,
        )

        assignment.deadline = datetime.datetime.utcnow() - datetime.timedelta(
            days=1
        )
        session.commit()

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']
        assert len(ents) == 2, 'It should not delete after an error'

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            204,
            result=None,
        )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
        )['entries']

        assert len(ents) == 2, 'Only teacher files should be affected'

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']

        assert len(ents) == 1, 'The teacher files should have a file less'


@pytest.mark.parametrize(
    'filename', ['../test_submissions/single_dir_archive.zip'], indirect=True
)
def test_delete_code_as_student(
    assignment_real_works,
    test_client,
    request,
    error_template,
    ta_user,
    logged_in,
    session,
    student_user,
):
    assignment, work = assignment_real_works
    work_id = work['id']

    with logged_in(student_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )
        assert len(res['entries']) == 2

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            204,
            result=None,
        )

        assignment.state = m._AssignmentStateEnum.done
        session.commit()

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            403,
            result=error_template,
        )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
        )['entries']

        assert len(ents) == 1

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']

        assert len(ents) == 2

        with logged_in(ta_user):
            test_client.req(
                'delete',
                f'/api/v1/code/{res["entries"][0]["id"]}',
                204,
                result=None,
            )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']
        assert len(ents) == 1


@pytest.mark.parametrize(
    'filename', ['../test_submissions/single_dir_archive.zip'], indirect=True
)
def test_delete_code_twice(
    assignment_real_works, test_client, request, error_template, ta_user,
    logged_in, session
):
    assignment, work = assignment_real_works
    work_id = work['id']

    with logged_in(ta_user):
        res = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )
        assert len(res['entries']) == 2

        assignment.deadline = datetime.datetime.utcnow() - datetime.timedelta(
            days=1
        )
        session.commit()

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            204,
            result=None,
        )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']

        assert len(ents) == 1, 'The teacher files should have a file less'

        test_client.req(
            'delete',
            f'/api/v1/code/{res["entries"][0]["id"]}',
            403,
            result=error_template,
        )

        ents = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            query={'owner': 'teacher'},
        )['entries']

        assert len(ents) == 1, 'The teacher files should have a file less'


@pytest.mark.parametrize(
    'filename', ['../test_submissions/single_dir_archive.zip'], indirect=True
)
def test_update_code(
    assignment_real_works, test_client, request, error_template, ta_user,
    logged_in, session, student_user
):
    assignment, work = assignment_real_works
    work_id = work['id']

    with logged_in(ta_user):
        code_id = test_client.req(
            'get',
            f'/api/v1/submissions/{work_id}/files/',
            200,
            result={
                'entries': list,
                'id': int,
                'name': str,
            }
        )['entries'][0]['id']

    with logged_in(student_user):
        new_id = test_client.req(
            'patch', f'/api/v1/code/{code_id}', 200, real_data='NEW_CON'
        )['id']
        assert new_id == code_id
        assert 'NEW_CON' == test_client.get(f'/api/v1/code/{new_id}').get_data(
            as_text=True
        )

        new_id = test_client.req(
            'patch', f'/api/v1/code/{code_id}', 200, real_data='NEW_CON!'
        )['id']
        assert new_id == code_id
        assert 'NEW_CON!' == test_client.get(f'/api/v1/code/{new_id}'
                                             ).get_data(as_text=True)

        m.Assignment.query.filter_by(id=assignment.id).update(
            {
                'state': m._AssignmentStateEnum.done
            }
        )
        test_client.req(
            'patch', f'/api/v1/code/{code_id}', 403, real_data='NEW_CON!'
        )

    with logged_in(ta_user):
        new_id = test_client.req(
            'patch', f'/api/v1/code/{code_id}', 200, real_data='TA_CON'
        )['id']
        assert new_id != code_id
        assert 'NEW_CON!' == test_client.get(f'/api/v1/code/{code_id}'
                                             ).get_data(as_text=True)
        assert 'TA_CON' == test_client.get(f'/api/v1/code/{new_id}').get_data(
            as_text=True
        )

        test_client.req(
            'patch', f'/api/v1/code/{code_id}', 403, real_data='NEW_CON!'
        )

        newest_id = test_client.req(
            'patch', f'/api/v1/code/{new_id}', 200, real_data='TA_CON!'
        )['id']
        assert newest_id == new_id
        assert 'TA_CON!' == test_client.get(f'/api/v1/code/{new_id}').get_data(
            as_text=True
        )

    with logged_in(student_user):
        test_client.req(
            'patch', f'/api/v1/code/{new_id}', 403, real_data='AAH_CON'
        )

    m.Assignment.query.filter_by(id=assignment.id).update(
        {
            'state': m._AssignmentStateEnum.open
        }
    )
    with logged_in(student_user):
        test_client.req(
            'patch', f'/api/v1/code/{new_id}', 403, real_data='AAH_CON'
        )

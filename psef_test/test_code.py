import pytest

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error


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

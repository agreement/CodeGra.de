import pytest

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error


@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        'Student1',
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=True
)
@pytest.mark.parametrize('size', [10, data_error(int(1.5 * 2 ** 20))])
def test_get_code_metadata(
    named_user, test_client, request, error_template, logged_in, size
):
    filestr = 'a' * size

    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif data_err:
        error = 400
    else:
        error = False

    with logged_in(named_user):
        res = test_client.req(
            'post',
            '/api/v1/files/',
            error or 201,
            real_data=filestr,
            result=error_template if error else str,
        )
        fname = error or res

        if not data_err:
            if error:
                test_client.req(
                    'get',
                    f'/api/v1/files/{fname}',
                    404,
                    result=error_template,
                )
            else:
                res = test_client.get(f'/api/v1/files/{fname}')
                assert res.status_code == 200

                assert res.get_data(as_text=True) == filestr

                res = test_client.get(f'/api/v1/files/{fname}')
                assert res.status_code == 404

import pytest

import psef as p
import psef.errors as e
import psef.models as m

perm_error = pytest.mark.perm_error
http_error = pytest.mark.http_error


@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        'Stupid1',
        perm_error(error=401)('NOT_LOGGED_IN'),
        'admin',
    ],
    indirect=True
)
@pytest.mark.parametrize(
    'q,users',
    [
        ('tuPId', ['stupid{}'.format(i) for i in range(1, 5)]),
        ('s chap', ['thomas']),
        ('s%chap', []),
        http_error(error=400)(('ko', []))  # Too short
    ]
)
def test_searching_users(
    named_user, error_template, logged_in, test_client, q, users, request
):
    perm_marker = request.node.get_marker('perm_error')
    http_marker = request.node.get_marker('http_error')

    code = 200 if http_marker is None else http_marker.kwargs['error']
    code = code if perm_marker is None else perm_marker.kwargs['error']

    with logged_in(named_user):
        res = test_client.req(
            'get',
            f'/api/v1/users/?q={q}',
            code,
            result=error_template if code >= 400 else list
        )
        if code < 400:
            assert sorted(i['username'] for i in res) == sorted(users)


def test_searching_users_rate_limit(
    ta_user, error_template, logged_in, test_client, app
):
    # Multiple `app.app_context` calls are used to make sure the `g` object
    # from flask is reset. This is necessary as our rate limiter only checks
    # the limit once per request and does this using this `g` object.
    with logged_in(ta_user):
        with app.app_context():
            res = test_client.req(
                'get',
                f'/api/v1/users/?q=query',
                200,
                result=list,
            )
        with app.app_context():
            # We should be hitting the limit now.
            res = test_client.req(
                'get', f'/api/v1/users/?q=query', 429, result=error_template
            )
            assert res['code'] == e.APICodes.RATE_LIMIT_EXCEEDED.name

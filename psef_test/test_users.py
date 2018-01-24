import pytest

import psef as p
import psef.errors as e
import psef.models as m

perm_error = pytest.mark.perm_error
http_error = pytest.mark.http_error
data_error = pytest.mark.data_error


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


@pytest.mark.parametrize(
    'username', [
        data_error(error=400)('thomas'),
        'NOT TAKEN',
        data_error(error=400)(''),
        data_error(error=400)(None),
    ]
)
@pytest.mark.parametrize(
    'email', [
        data_error(error=400)('ERR'),
        data_error(error=400)(''),
        data_error(error=400)(None),
        'good@email',
    ]
)
@pytest.mark.parametrize(
    'name', [
        data_error(error=400)(''),
        data_error(error=400)(None),
        'good',
    ]
)
@pytest.mark.parametrize(
    'password', [
        data_error(error=400)(''),
        data_error(error=400)(None),
        'good',
    ]
)
def test_register_user(
    username, test_client, error_template, name, password, email, request, app,
    session
):
    data_err = request.node.get_marker('data_error')
    code = 200 if data_err is None else data_err.kwargs['error']

    data = {}
    if name is not None:
        data['name'] = name
    if username is not None:
        data['username'] = username
    if password is not None:
        data['password'] = password
    if email is not None:
        data['email'] = email

    res = test_client.req(
        'post',
        '/api/v1/user',
        code,
        data=data,
        result=error_template if code >= 400 else {
            'access_token': str
        }
    )

    if code < 400:
        access_token = res['access_token']
        # Make sure we can log in with the newly given token
        test_client.req(
            'get',
            '/api/v1/login',
            200,
            headers={
                'Authorization': f'Bearer {access_token}'
            }
        )

        new_user = m.User.query.filter_by(username=username).one()
        assert new_user.name == name, 'The given name should be used'
        assert new_user.email == email, 'The given email should be used'

        # Make sure we can log in with the given password
        test_client.req(
            'post',
            '/api/v1/login',
            200,
            data={
                'username': username,
                'password': password,
            }
        )

    elif username != 'thomas':
        assert session.query(m.User).filter_by(username=username).first(
        ) is None, ('The new user should not have been created')
    else:
        assert session.query(
            m.User
        ).filter_by(username=username
                    ).one().name != name, ('The old user should be preserved')

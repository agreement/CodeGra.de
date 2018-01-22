import copy

import pytest

import psef
import psef.models as m

data_error = pytest.mark.data_error
perm_error = pytest.mark.perm_error
missing_error = pytest.mark.missing_error
password_error = pytest.mark.password_error
does_have_permission = pytest.mark.does_have_permission
needs_password = pytest.mark.needs_password


@pytest.mark.parametrize('active', [True, False])
@pytest.mark.parametrize(
    'password', [
        data_error(None),
        data_error(5),
        'a',
        data_error(wrong=True)('b-the-wrong-password'),
    ]
)
@pytest.mark.parametrize(
    'username', [
        data_error(None),
        data_error(5),
        'a-the-a-er',
        data_error('b@b.nl'),
        data_error(wrong=True)('b'),
    ]
)
def test_login(
    test_client, session, error_template, password, request, active, app,
    username
):
    new_user = m.User(
        name='NEW_USER',
        email='a@a.nl',
        password='a',
        active=active,
        username='a-the-a-er'
    )
    session.add(new_user)
    session.commit()

    data_err = request.node.get_marker('data_error')
    if data_err:
        error = 400
        if data_err.kwargs.get('wrong'):
            error_template = copy.deepcopy(error_template)
            error_template['message'
                           ] == 'The supplied email or password is wrong.'
    elif not active:
        error = 403
    else:
        error = False

    data = {}
    if password is not None:
        data['password'] = password
    if username is not None:
        data['username'] = username

    res = test_client.req(
        'post',
        f'/api/v1/login',
        error or 200,
        data=data,
        result=error_template if error else {
            'user':
                {
                    'email': 'a@a.nl',
                    'id': int,
                    'name': 'NEW_USER',
                    'username': 'a-the-a-er',
                    'hidden': False,
                },
            'access_token': str
        }
    )
    access_token = '' if error else res['access_token']

    with app.app_context():
        test_client.req(
            'get',
            '/api/v1/login',
            401 if error else 200,
            headers={
                'Authorization': f'Bearer {access_token}'
            }
        )

    test_client.req('get', '/api/v1/login', 401)


@pytest.mark.parametrize(
    'named_user', [
        does_have_permission('Thomas Schaper'),
        'Stupid1',
    ],
    indirect=True
)
def test_extended_get_login(test_client, named_user, logged_in, request):
    perm_true = bool(request.node.get_marker('does_have_permission'))

    with logged_in(named_user):
        test_client.req(
            'get',
            '/api/v1/login',
            200,
            query={'type': 'extended'},
            result={
                'name': str,
                'id': int,
                'email': str,
                'hidden': perm_true,
                'username': str,
            }
        )


@pytest.mark.parametrize(
    'named_user,roles',
    [
        ('Thomas Schaper', ['Student', 'TA', 'TA', None]),
        ('Stupid1', [None, None, 'Student', 'Student']),
        ('admin', [None, None, None, None]),
    ],
    indirect=['named_user'],
)
def test_get_roles(
    test_client, named_user, logged_in, pse_course, bs_course, prog_course,
    inprog_course, roles
):
    result = {}
    for course, role in zip(
        [pse_course, bs_course, prog_course, inprog_course], roles
    ):
        if role is not None:
            result[str(course.id)] = role

    with logged_in(named_user):
        test_client.req(
            'get',
            '/api/v1/login',
            200,
            query={'type': 'roles'},
            result=result,
        )


def test_login_duplicate_email(
    test_client, session, error_template, request, app
):
    new_users = [
        m.User(
            name='NEW_USER',
            email='a@a.nl',
            password='a',
            active=True,
            username='a-the-awesome'
        ),
        m.User(
            name='NEW_USER',
            email='a@a.nl',
            password='a',
            active=True,
            username='a-the-a-er'
        )
    ]
    for new_user in new_users:
        session.add(new_user)
    session.commit()

    for user_id in [u.id for u in new_users]:
        user = m.User.query.get(user_id)

        res = test_client.req(
            'post',
            f'/api/v1/login',
            200,
            data={'username': user.username,
                  'password': 'a'},
            result={
                'user':
                    {
                        'email': 'a@a.nl',
                        'id': int,
                        'name': 'NEW_USER',
                        'username': user.username,
                        'hidden': False,
                    },
                'access_token': str
            }
        )
        access_token = res['access_token']

        with app.app_context():
            test_client.req(
                'get',
                '/api/v1/login',
                200,
                headers={'Authorization': f'Bearer {access_token}'},
                result={
                    'username': user.username,
                    'id': int,
                    'email': user.email,
                    'name': user.name,
                }
            )

        test_client.req('get', '/api/v1/login', 401)


@pytest.mark.parametrize(
    'new_password',
    [needs_password('wow'), '', missing_error(None)]
)
@pytest.mark.parametrize(
    'email', [
        needs_password('a-the@a.nl'), 'a@a.nl',
        data_error('wrong_email'),
        missing_error(None)
    ]
)
@pytest.mark.parametrize('name', ['Wow', data_error(''), missing_error(None)])
@pytest.mark.parametrize(
    'old_password', [
        'a',
        '',
        password_error('wrong'),
        missing_error(None),
    ]
)
@pytest.mark.parametrize('role', ['Admin', perm_error('Nobody')])
def test_update_user_info(
    logged_in, test_client, session, new_password, email, name, old_password,
    error_template, request, role
):
    user = m.User(
        name='NEW_USER',
        email='a@a.nl',
        password='a',
        active=True,
        username='a-the-a-er',
        role=m.Role.query.filter_by(name=role).one(),
    )
    session.add(user)
    session.commit()
    user_id = user.id

    missing_err = request.node.get_marker('missing_error')
    data_err = request.node.get_marker('data_error')
    perm_err = request.node.get_marker('perm_error')
    password_err = request.node.get_marker('password_error')
    needs_pw = request.node.get_marker('needs_password')
    if missing_err:
        error = 400
    elif perm_err:
        error = 403
    elif password_err:
        error = 403
    elif data_err:
        error = 400
    elif needs_pw and old_password != 'a':
        error = 403
    else:
        error = False

    data = {}
    if new_password is not None:
        data['new_password'] = new_password
    if old_password is not None:
        data['old_password'] = old_password
    if email is not None:
        data['email'] = email
    if name is not None:
        data['name'] = name

    with logged_in(user):
        test_client.req(
            'patch',
            '/api/v1/login',
            error or 204,
            data=data,
            result=error_template if error else None
        )
        new_user = m.User.query.get(user_id)
        if not error:
            assert new_user.name == name
            assert new_user.email == email
        else:
            assert new_user.name != name


def test_update_user_info_permissions(
    logged_in, test_client, session, error_template, request
):
    new_role = m.Role(name='NEW_ROLE')
    info_perm = m.Permission.query.filter_by(name='can_edit_own_info').one()
    pw_perm = m.Permission.query.filter_by(name='can_edit_own_password').one()
    new_role.set_permission(info_perm, False)
    new_role.set_permission(pw_perm, False)

    session.add(new_role)
    user = m.User(
        name='NEW_USER',
        email='a@a.nl',
        password='a',
        active=True,
        username='a-the-a-er',
        role=new_role,
    )
    session.add(user)

    session.commit()
    user_id = user.id

    data = {}
    data['new_password'] = 'new_pw'
    data['old_password'] = 'a'
    data['email'] = 'new_email@email.com'
    data['name'] = 'new_name'

    with logged_in(user):
        # This user has no permissions so it should not be possible to do this.
        test_client.req(
            'patch',
            '/api/v1/login',
            403,
            data=data,
            result=error_template,
        )

        pw_perm = m.Permission.query.filter_by(name='can_edit_own_password'
                                               ).one()
        m.User.query.get(user_id).role.set_permission(pw_perm, True)
        session.commit()

        # This user does not have the permission to change the name, so it
        # should fail
        test_client.req(
            'patch',
            '/api/v1/login',
            403,
            data=data,
            result=error_template,
        )
        # However only password should be good
        test_client.req(
            'patch',
            '/api/v1/login',
            204,
            data={
                'name': 'NEW_USER',
                'email': 'a@a.nl',
                'old_password': 'a',
                'new_password': 'b'
            },
        )

        pw_perm = m.Permission.query.filter_by(name='can_edit_own_password'
                                               ).one()
        info_perm = m.Permission.query.filter_by(name='can_edit_own_info'
                                                 ).one()
        m.User.query.get(user_id).role.set_permission(pw_perm, False)
        m.User.query.get(user_id).role.set_permission(info_perm, True)
        session.commit()

        # This user does not have the permission to change the pw, so it
        # should fail
        test_client.req(
            'patch',
            '/api/v1/login',
            403,
            data=data,
            result=error_template,
        )
        # However only name should be good
        test_client.req(
            'patch',
            '/api/v1/login',
            204,
            data={
                'name': 'new_name1',
                'email': 'a@a.nl',
                'old_password': '',
                'new_password': '',
            },
        )

        pw_perm = m.Permission.query.filter_by(name='can_edit_own_password'
                                               ).one()
        m.User.query.get(user_id).role.set_permission(pw_perm, True)
        session.commit()

        # It now has both so this should work.
        test_client.req(
            'patch',
            '/api/v1/login',
            403,
            data=data,
            result=error_template,
        )


@pytest.mark.parametrize('to_null', [True, False])
def test_reset_password(
    test_client,
    session,
    error_template,
    ta_user,
    monkeypatch,
    app,
    to_null,
    stubmailer,
):
    stubmailer.do_raise = True

    test_client.req(
        'patch',
        f'/api/v1/login?type=reset_email',
        500,
        data={'username': ta_user.username},
        result=error_template,
    )

    if to_null:
        ta_user.password = None
        session.commit()

    stubmailer.do_raise = False

    test_client.req(
        'patch',
        f'/api/v1/login?type=reset_email',
        204,
        data={
            'username': ta_user.username
        }
    )
    assert stubmailer.called
    msg = str(stubmailer.msg)
    start_id = msg.find('user=') + len('user=')
    end_id = msg[start_id:].find('&token=') + start_id
    print(msg, start_id, end_id)
    user_id = int(msg[start_id:end_id])

    start_token = end_id + len('&token=')
    end_token = msg[start_token:].find('\r\n') + start_token
    token = msg[start_token:end_token]
    stubmailer.called = False

    test_client.req(
        'patch',
        f'/api/v1/login?type=reset_password',
        400,
        data={'user_id': user_id,
              'new_password': '',
              'token': token},
        result=error_template,
    )
    test_client.req(
        'patch',
        f'/api/v1/login?type=reset_password',
        403,
        data={'user_id': user_id,
              'new_password': 's',
              'token': token + 's'},
        result=error_template,
    )
    test_client.req(
        'patch',
        f'/api/v1/login?type=reset_password',
        403,
        data={'user_id': user_id + 1,
              'new_password': 's',
              'token': token},
        result=error_template,
    )
    atoken = test_client.req(
        'patch',
        f'/api/v1/login?type=reset_password',
        200,
        data={'user_id': user_id,
              'new_password': '2o2',
              'token': token},
        result={'access_token': str},
    )['access_token']
    test_client.req(
        'patch',
        f'/api/v1/login?type=reset_password',
        403,
        data={'user_id': user_id,
              'new_password': 'wow',
              'token': token},
        result=error_template,
    )

    with app.app_context():
        test_client.req(
            'get',
            '/api/v1/login',
            200,
            headers={
                'Authorization': f'Bearer {atoken}'
            }
        )

    test_client.req(
        'patch',
        f'/api/v1/login?type=reset_password',
        403,
        data={'user_id': user_id,
              'new_password': '2o2',
              'token': token},
        result=error_template,
    )

    assert not stubmailer.called

    test_client.req(
        'post',
        f'/api/v1/login',
        200,
        data={
            'username': ta_user.username,
            'password': '2o2',
        }
    )


@pytest.mark.parametrize(
    'named_user',
    [
        ('Thomas Schaper'),
        ('Stupid1'),
        ('admin'),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=['named_user'],
)
def test_reset_email_on_lti(
    session, named_user, error_template, logged_in, test_client, request
):
    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        code = perm_err.kwargs['error']
    else:
        code = 204

    with logged_in(named_user):
        test_client.req(
            'patch',
            '/api/v1/login?type=reset_on_lti',
            code,
            result=error_template if code >= 400 else None
        )
        if code <= 400:
            assert m.User.query.get(
                named_user.id
            ).reset_email_on_lti, """
            Property should be set.
            """

            # Multiple times should be possible without error
            test_client.req('patch', '/api/v1/login?type=reset_on_lti', 204)

            assert m.User.query.get(
                named_user.id
            ).reset_email_on_lti, """
            Property should still be set
            """

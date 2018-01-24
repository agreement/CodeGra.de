import pytest

import psef.models as m

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error
missing_error = pytest.mark.missing_error


@pytest.mark.parametrize(
    'named_user', [
        ('admin'),
        perm_error(error=403)(('Stupid1')),
        perm_error(error=403)(('Thomas Schaper')),
        perm_error(error=401)(('NOT_LOGGED_IN')),
    ],
    indirect=['named_user']
)
def test_get_roles(
    logged_in,
    named_user,
    test_client,
    request,
    session,
    error_template,
):
    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        res = test_client.req(
            'get',
            '/api/v1/roles/',
            error or 200,
            result=error_template if error else list
        )
        if not error:
            all_roles = {r.name: r for r in m.Role.query.all()}

            for item in res:
                assert 'name' in item
                assert item['name'] in all_roles
                assert 'id' in item
                assert all_roles[item['name']].id == item['id']
                assert 'perms' in item
                assert 'own' in item
                assert item['own'] == (item['name'] == 'Admin')

                del all_roles[item['name']]

            # Make sure we have seen all roles
            assert not all_roles


@pytest.mark.parametrize(
    'named_user', [
        'admin',
        perm_error(error=403)(('Stupid1')),
        perm_error(error=403)(('Thomas Schaper')),
        perm_error(error=401)(('NOT_LOGGED_IN')),
    ],
    indirect=['named_user']
)
@pytest.mark.parametrize(
    'role_name', [
        'Staff',
        'Student',
        'Admin',
        data_error(error=404)(1000),
    ]
)
@pytest.mark.parametrize(
    'perm_value', [True, False, missing_error(error=400)(None)]
)
@pytest.mark.parametrize(
    'perm_name', [
        missing_error(error=400)(5),
        missing_error(error=400)(None),
        'can_edit_own_info',
        'can_manage_site_users',
        data_error(error=404)('can_grade_work'),
    ]
)
def test_update_global_roles(
    logged_in, named_user, test_client, request, session, error_template,
    role_name, perm_value, perm_name, admin_user
):
    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    missing_err = request.node.get_marker('missing_error')

    if perm_err:
        error = perm_err.kwargs['error']
    elif missing_err:
        error = missing_err.kwargs['error']
    elif data_err:
        error = data_err.kwargs['error']
    elif 'Admin' == role_name and perm_name == 'can_manage_site_users':
        error = 403
    else:
        error = False

    if isinstance(role_name, str):
        role_id = session.query(m.Role).filter_by(name=role_name, ).one().id
    else:
        role_id = role_name

    with logged_in(named_user):
        data = {}

        if perm_value is not None:
            data['value'] = perm_value
        if perm_name is not None:
            data['permission'] = perm_name

        test_client.req(
            'patch',
            f'/api/v1/roles/{role_id}',
            error or 204,
            data=data,
            result=error_template if error else None
        )

        if not error:
            with logged_in(admin_user):
                res = test_client.req(
                    'get',
                    f'/api/v1/roles/',
                    200,
                )
                item = [r for r in res if r['name'] == role_name]
                assert len(item) == 1
                item = item[0]
                assert item['perms'][perm_name] == perm_value

import pytest

import psef.models as m

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error
missing_error = pytest.mark.missing_error


@pytest.mark.parametrize(
    'named_user,expected', [
        (
            'Thomas Schaper', [
                ('Project Software Engineering', 'Student'),
                ('Besturingssystemen', 'TA'), ('Programmeertalen', 'TA')
            ]
        ),
        (
            'Stupid1', [
                ('Programmeertalen', 'Student'),
                ('Inleiding Programmeren', 'Student')
            ]
        ),
        ('admin', []),
        perm_error(error=401)(('NOT_LOGGED_IN', 'ERROR!')),
    ],
    indirect=['named_user']
)
def test_get_all_courses(
    named_user, test_client, logged_in, request, expected, error_template
):
    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        res = test_client.req(
            'get',
            f'/api/v1/courses/',
            error or 200,
            result=error_template if error else list
        )

        if not error:
            found = set()
            for item in res:
                exp = [ex for ex in expected if ex[0] == item['name']]
                assert len(exp) == 1
                exp = exp[0]
                assert exp[1] == item['role']
                found.add(exp)

            assert len(found) == len(res) == len(expected)


@pytest.mark.parametrize(
    'named_user,course_name,role', [
        ('Thomas Schaper', 'Programmeertalen', 'TA'),
        ('Thomas Schaper', 'Project Software Engineering', 'Student'),
        ('Stupid1', 'Programmeertalen', 'Student'),
        data_error(('Stupid1', 'Project Software Engineering', 'Student')),
        data_error(('admin', 'Project Software Engineering', 'Student')),
        perm_error(error=401)(
            ('NOT_LOGGED_IN', 'Project Software Engineering', 'Student')
        ),
    ],
    indirect=['named_user']
)
def test_get_course_data(
    error_template, request, logged_in, test_client, named_user, course_name,
    role, session
):
    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif data_err:
        error = 404
    else:
        error = False

    with logged_in(named_user):
        course = session.query(m.Course).filter_by(name=course_name).one()
        test_client.req(
            'get',
            f'/api/v1/courses/{course.id}',
            error or 200,
            result=error_template
            if error else {'role': role,
                           'id': course.id,
                           'name': course_name}
        )


@pytest.mark.parametrize(
    'named_user', [
        perm_error(error=403)('Stupid1'),
        'admin',
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=['named_user']
)
@pytest.mark.parametrize('name', [data_error(None), data_error(5), 'str'])
def test_add_course(
    request, named_user, test_client, logged_in, name, error_template
):
    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif data_err:
        error = 400
    else:
        error = False

    with logged_in(named_user):
        data = {}
        if name is not None:
            data['name'] = name

        course = test_client.req(
            'post',
            f'/api/v1/courses/',
            error or 200,
            data=data,
            result=error_template if error else {'id': int,
                                                 'name': name}
        )

        if not error:
            test_client.req(
                'get',
                f'/api/v1/courses/{course["id"]}',
                200,
                result={'role': 'Teacher',
                        'id': course['id'],
                        'name': name}
            )


@pytest.mark.parametrize(
    'named_user,expected', [
        ('Stupid1', ['Haskell', 'Shell', 'Python', 'Go']),
        ('Thomas Schaper', ['Haskell', 'Shell', 'Python', 'Go', 'Erlang']),
        perm_error(error=403)(('admin', [])),
        perm_error(error=401)(('NOT_LOGGED_IN', [])),
    ],
    indirect=['named_user']
)
def test_get_course_assignments(
    prog_course, named_user, test_client, error_template, session, request,
    logged_in, expected
):
    course = session.query(m.Course).filter_by(name='Programmeertalen').one()

    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        res = test_client.req(
            'get',
            f'/api/v1/courses/{course.id}/assignments/',
            error or 200,
            result=error_template if error else list
        )
        if not error:
            found = set()
            for got in res:
                item = [item for item in expected if item == got['name']]
                assert len(item) == 1
                found.add(item[0])

            assert len(expected) == len(res) == len(found)


@pytest.mark.parametrize(
    'course_n,users',
    [
        (
            'Programmeertalen', [
                'Thomas Schaper', 'Devin Hillenius', 'Stupid1', 'Stupid2',
                'Stupid3', 'Stupid4', 'b'
            ]
        )
    ],
)
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=401)('NOT_LOGGED_IN'),
        perm_error(error=403)('Stupid1'),
    ],
    indirect=['named_user']
)
def test_get_course_users(
    named_user, logged_in, test_client, request, error_template, session,
    course_n, users
):
    course = session.query(m.Course).filter_by(name=course_n).one()
    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        res = test_client.req(
            'get',
            f'/api/v1/courses/{course.id}/users/',
            error or 200,
            result=error_template if error else list
        )
        if not error:
            assert len(users) == len(res)
            for got, expected in zip(res, sorted(users)):
                assert 'CourseRole' in got
                assert got['User']['name'] == expected


@pytest.mark.parametrize('course_n', ['Programmeertalen'])
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=403)('Stupid1'),
        perm_error(error=403)('admin'),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=['named_user']
)
@pytest.mark.parametrize(
    'to_add', [
        data_error(error=400)('thomas_schaper@example.com'),
        data_error(error=400)('stupid1@example.com'),
        data_error(error=404)('non_existing'),
        data_error(error=404)('non_existing@example.com'),
        data_error(error=400)(1),
        ('admin@example.com'),
    ]
)
@pytest.mark.parametrize('role_n', ['Student', 'Teacher'])
@pytest.mark.parametrize('include_role', [True, missing_error(False)])
@pytest.mark.parametrize('include_email', [True, missing_error(False)])
def test_add_user_to_course(
    named_user, test_client, logged_in, request, session, course_n, role_n,
    include_role, include_email, to_add, error_template
):
    course = session.query(m.Course).filter_by(name=course_n).one()
    role = session.query(m.CourseRole).filter_by(
        name=role_n, course=course
    ).one()

    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    missing_err = request.node.get_marker('missing_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif missing_err:
        error = 400
    elif data_err:
        error = data_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        data = {}
        if include_email:
            data['user_email'] = to_add
        if include_role:
            data['role_id'] = role.id

        test_client.req(
            'put',
            f'/api/v1/courses/{course.id}/users/',
            error or 201,
            data=data,
            result=error_template if error else {
                'User': dict,
                'CourseRole': dict,
            }
        )

        if not error:
            res = test_client.req(
                'get',
                f'/api/v1/courses/{course.id}/users/',
                200,
            )
            res = [r for r in res if r['User']['email'] == to_add]
            assert len(res) == 1
            assert res[0]['CourseRole']['name'] == role_n


@pytest.mark.parametrize('course_n', ['Programmeertalen'])
@pytest.mark.parametrize(
    'named_user', [
        'Thomas Schaper',
        perm_error(error=403)('Stupid1'),
        perm_error(error=403)('admin'),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=['named_user']
)
@pytest.mark.parametrize(
    'to_update', [
        data_error(error=403)('thomas_schaper@example.com'),
        ('stupid1@example.com'),
        ('admin@example.com'),
        data_error(error=404)(-1),
        data_error(error=400)(True),
        data_error(error=400)(None),
    ]
)
@pytest.mark.parametrize('role_n', ['Student', 'Teacher'])
@pytest.mark.parametrize('include_role', [True, missing_error(False)])
@pytest.mark.parametrize('include_user_id', [True, missing_error(False)])
def test_update_user_in_course(
    logged_in, named_user, test_client, request, session, course_n, role_n,
    include_user_id, include_role, error_template, to_update
):
    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    missing_err = request.node.get_marker('missing_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif missing_err:
        error = 400
    elif data_err:
        error = data_err.kwargs['error']
    else:
        error = False

    course = session.query(m.Course).filter_by(name=course_n).one()
    role = session.query(m.CourseRole).filter_by(
        name=role_n, course=course
    ).one()

    if isinstance(to_update, str):
        user_id = session.query(m.User).filter_by(email=to_update).one().id
    else:
        user_id = to_update

    with logged_in(named_user):
        data = {}
        if include_user_id:
            data['user_id'] = user_id
        if include_role:
            data['role_id'] = role.id

        test_client.req(
            'put',
            f'/api/v1/courses/{course.id}/users/',
            error or 204,
            result=error_template if error else None,
            data=data,
        )


@pytest.mark.parametrize('course_n', ['Programmeertalen'])
@pytest.mark.parametrize(
    'named_user,role', [
        ('Thomas Schaper', 'TA'),
        perm_error(error=403)(('Stupid1', 'Student')),
        perm_error(error=403)(('admin', None)),
        perm_error(error=401)(('NOT_LOGGED_IN', None)),
    ],
    indirect=['named_user']
)
@pytest.mark.parametrize('extended', [True, False])
def test_get_courseroles(
    logged_in, named_user, test_client, request, session, error_template,
    course_n, extended, role
):
    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    course = session.query(m.Course).filter_by(name=course_n).one()
    course_roles = sorted(
        m.CourseRole.query.filter_by(course_id=course.id).all(),
        key=lambda item: item.name
    )

    with logged_in(named_user):
        result = []
        for crole in course_roles:
            item = {
                'name': crole.name,
                'id': int,
                'course': {
                    'name': course_n,
                    'id': int
                }
            }
            if extended:
                item['perms'] = dict
                item['own'] = crole.name == role
            result.append(item)

        test_client.req(
            'get',
            f'/api/v1/courses/{course.id}/roles/',
            error or 200,
            query={'with_roles': 'true'} if extended else {},
            result=error_template if error else result
        )


@pytest.mark.parametrize('course_n', ['Programmeertalen'])
@pytest.mark.parametrize(
    'named_user', [
        ('Thomas Schaper'),
        perm_error(error=403)(('Stupid1')),
        perm_error(error=403)(('admin')),
        perm_error(error=401)(('NOT_LOGGED_IN')),
    ],
    indirect=['named_user']
)
@pytest.mark.parametrize(
    'role_name', [
        'NEW_ROLE',
        data_error('Student'),
        data_error(None),
        data_error(5),
        data_error(True),
    ]
)
def test_add_courseroles(
    logged_in,
    named_user,
    test_client,
    request,
    session,
    error_template,
    course_n,
    role_name,
):
    perm_err = request.node.get_marker('perm_error')
    data_err = request.node.get_marker('data_error')
    if perm_err:
        error = perm_err.kwargs['error']
    elif data_err:
        error = 400
    else:
        error = False

    course = session.query(m.Course).filter_by(name=course_n).one()

    with logged_in(named_user):
        data = {}
        if role_name is not None:
            data['name'] = role_name
        test_client.req(
            'post',
            f'/api/v1/courses/{course.id}/roles/',
            error or 204,
            data=data,
            result=error_template if error else None
        )

        if not error:
            roles = test_client.req(
                'get',
                f'/api/v1/courses/{course.id}/roles/',
                200,
                query={'with_roles': 'true'}
            )

            found_amount = 0
            for role in roles:
                if role['name'] == role_name:
                    found_amount += 1
                    assert (
                        len(role['perms']) == len(
                            session.query(m.Permission)
                            .filter_by(course_permission=True).all()
                        )
                    )
                    for perm_n, value in role['perms'].items():
                        perm = session.query(m.Permission).filter_by(
                            name=perm_n
                        ).one()
                        assert perm.default_value == value
                        assert perm.course_permission

            assert found_amount == 1


@pytest.mark.parametrize('course_n', ['Programmeertalen'])
@pytest.mark.parametrize(
    'named_user,user_role', [
        ('Thomas Schaper', 'TA'),
        perm_error(error=403)(('Stupid1', 'Student')),
        perm_error(error=403)(('admin', None)),
        perm_error(error=401)(('NOT_LOGGED_IN', None)),
    ],
    indirect=['named_user']
)
@pytest.mark.parametrize(
    'role_name', [
        'TA',
        'Student',
        data_error(error=404)(1000),
    ]
)
@pytest.mark.parametrize(
    'perm_value', [True, False, missing_error(error=400)(None)]
)
@pytest.mark.parametrize(
    'perm_name', [
        missing_error(error=400)(5),
        'can_manage_course',
        missing_error(error=400)(None),
        'can_grade_work',
        data_error(error=404)('non_existing'),
    ]
)
def test_update_courseroles(
    logged_in, named_user, test_client, request, session, error_template,
    course_n, role_name, user_role, perm_value, perm_name
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
    elif user_role == role_name and perm_name == 'can_manage_course':
        error = 403
    else:
        error = False

    course = session.query(m.Course).filter_by(name=course_n).one()
    if isinstance(role_name, str):
        role_id = session.query(m.CourseRole).filter_by(
            name=role_name, course=course
        ).one().id
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
            f'/api/v1/courses/{course.id}/roles/{role_id}',
            error or 204,
            data=data,
            result=error_template if error else None
        )


@pytest.mark.parametrize('course_n', ['Programmeertalen'])
@pytest.mark.parametrize(
    'named_user', [
        ('Thomas Schaper'),
        perm_error(error=403)(('Stupid1')),
        perm_error(error=403)(('admin')),
        perm_error(error=401)(('NOT_LOGGED_IN')),
    ],
    indirect=['named_user']
)
@pytest.mark.parametrize(
    'role_name', [
        'Observer',
        data_error(error=400)('TA'),
        data_error(error=400)('Student'),
        data_error(error=404, skip_check=True)(1000),
    ]
)
def test_delete_courseroles(
    logged_in, named_user, test_client, request, session, error_template,
    course_n, role_name, ta_user
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
    else:
        error = False

    course = session.query(m.Course).filter_by(name=course_n).one()
    if isinstance(role_name, str):
        role_id = session.query(m.CourseRole).filter_by(
            name=role_name, course=course
        ).one().id
    else:
        role_id = role_name

    with logged_in(ta_user):
        orig_roles = test_client.req(
            'get',
            f'/api/v1/courses/{course.id}/roles/',
            200,
        )

    with logged_in(named_user):
        test_client.req(
            'delete',
            f'/api/v1/courses/{course.id}/roles/{role_id}',
            error or 204,
            result=error_template if error else None,
        )

    with logged_in(ta_user):
        new_roles = test_client.req(
            'get',
            f'/api/v1/courses/{course.id}/roles/',
            200,
        )

        assert (new_roles == orig_roles) == bool(error)
        if not error:
            assert not any(role_name == r['name'] for r in new_roles)


@pytest.mark.parametrize('course_n', ['Programmeertalen'])
@pytest.mark.parametrize(
    'role_name', [
        data_error(error=403)('Student'),
        'Observer',
        'NEW_ROLE',
    ]
)
def test_delete_lti_courseroles(
    role_name, ta_user, course_n, session, test_client, logged_in, request,
    error_template
):
    data_err = request.node.get_marker('data_error')

    if data_err:
        error = data_err.kwargs['error']
    else:
        error = False

    course = session.query(m.Course).filter_by(name=course_n).one()
    course.lti_provider = m.LTIProvider()
    session.commit()

    with logged_in(ta_user):
        test_client.req(
            'post',
            f'/api/v1/courses/{course.id}/roles/',
            204,
            data={'name': 'NEW_ROLE'},
        )

        role_id = session.query(m.CourseRole).filter_by(
            name=role_name, course=course
        ).one().id

        orig_roles = test_client.req(
            'get',
            f'/api/v1/courses/{course.id}/roles/',
            200,
        )

        test_client.req(
            'delete',
            f'/api/v1/courses/{course.id}/roles/{role_id}',
            error or 204,
            result=error_template if error else None,
        )

        new_roles = test_client.req(
            'get',
            f'/api/v1/courses/{course.id}/roles/',
            200,
        )

        assert (new_roles == orig_roles) == bool(error)
        if not error:
            assert not any(role_name == r['name'] for r in new_roles)

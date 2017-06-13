# -*- py-isort-options: '("-sg *"); -*-
import pytest
import os
import sys
import json

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + '/../')

import psef.models as m
import psef.auth as a
from psef.errors import APIException, APICodes


@pytest.fixture(scope='module')
def perms(session):
    perms = []
    perms.append(
        m.Permission(
            name='edit_name', default_value=True, course_permission=False))
    perms.append(
        m.Permission(
            name='edit_email', default_value=False, course_permission=False))
    perms.append(
        m.Permission(
            name='add_user', default_value=False, course_permission=False))

    perms.append(
        m.Permission(
            name='add_own_work', default_value=True, course_permission=True))
    perms.append(
        m.Permission(
            name='add_others_work',
            default_value=False,
            course_permission=True))
    perms.append(
        m.Permission(
            name='remove_course', default_value=False, course_permission=True))

    for perm in perms:
        session.add(perm)
    session.commit()
    yield perms


@pytest.fixture(scope='module')
def student_role(session, perms):
    role = m.Role(name='student', _permissions={perms[1].name: perms[1]})
    session.add(role)
    session.commit()
    yield role


@pytest.fixture(scope='module')
def fixed_role(session, perms):
    role = m.Role(name='fixed', _permissions={})
    session.add(role)
    session.commit()
    yield role


@pytest.fixture(scope='module')
def admin_role(session, perms):
    role = m.Role(
        name='admin',
        _permissions={p.name: p
                      for p in perms if not p.default_value})
    session.add(role)
    session.commit()
    yield role


@pytest.fixture(scope='module')
def pse_course(session):
    pse = m.Course(name='Project Software Engineering')
    session.add(pse)
    session.commit()
    yield pse


@pytest.fixture(scope='module')
def bs_course(session):
    bs = m.Course(name='Besturingssystemen')
    session.add(bs)
    session.commit()
    yield bs


@pytest.fixture(scope='module')
def aco_course(session):
    aco = m.Course(name='Architectuur en Computerarchitectuur')
    session.add(aco)
    session.commit()
    yield aco


@pytest.fixture(scope='module')
def ta_crole(session, bs_course, perms):
    ta = m.CourseRole(
        name='TA',
        course=bs_course,
        _permissions={p.name: p
                      for p in perms[3:5]})
    ta2 = m.CourseRole(name='TA', course=None, _permissions={})
    session.add(ta)
    session.add(ta2)
    session.commit()
    yield ta


@pytest.fixture(scope='module')
def student_crole(session, pse_course):
    student = m.CourseRole(name='student', course=pse_course)
    session.add(student)
    session.commit()
    yield student


@pytest.fixture(scope='module')
def thomas(session, perms, student_role, bs_course, student_crole, pse_course,
           ta_crole):
    thomas = m.User(
        name='Thomas Schaper',
        password='',
        email='th',
        role=student_role,
        courses={bs_course.id: ta_crole,
                 pse_course.id: student_crole})

    session.add(thomas)
    session.commit()
    yield m.User.query.filter_by(name='Thomas Schaper').first()


@pytest.fixture(scope='module')
def superuser(session, admin_role):
    suser = m.User(name='Super User', role=admin_role, password='', email='su')
    session.add(suser)
    session.commit()
    yield m.User.query.filter_by(name='Super User').first()


@pytest.fixture(scope='module')
def fixed(session, fixed_role):
    suser = m.User(name='Fixed', role=fixed_role, password='', email='f')
    session.add(suser)
    session.commit()
    yield m.User.query.filter_by(name='Fixed').first()


@pytest.mark.parametrize('perm,vals', [('add_own_work', (
    False, True, False)), ('add_others_work', (True, False, False)), (
        'remove_course', (False, False, False)), ('add_user', (False, False,
                                                               False))])
def test_course_permissions(thomas, bs_course, pse_course, aco_course, perm,
                            vals, login_endpoint, test_client):
    with test_client:
        login_endpoint(thomas.id)
        for course, val in zip([bs_course, pse_course, aco_course], vals):
            assert thomas.has_permission(perm, course_id=course.id) == val
            if val:
                a.ensure_permission(perm, course_id=course.id)
            else:
                with pytest.raises(APIException) as err:
                    a.ensure_permission(perm, course_id=course.id)
                assert err.value.api_code == APICodes.INCORRECT_PERMISSION
    for course, val in zip([bs_course, pse_course, aco_course], vals):
        with pytest.raises(APIException) as err:
            a.ensure_permission(perm, course_id=course.id)
        assert err.value.api_code == APICodes.NOT_LOGGED_IN


@pytest.mark.parametrize('perm', ['wow_nope'])
def test_non_existing_permission(thomas, bs_course, perm):
    with pytest.raises(KeyError):
        thomas.has_permission(perm)
    with pytest.raises(KeyError):
        thomas.has_permission(perm, course_id=bs_course.id)


@pytest.mark.parametrize('perm', ['wow_nope', 'add_own_work', 'edit_name'])
def test_non_existing_course(thomas, bs_course, perm):
    assert not thomas.has_permission(perm, course_id=bs_course.id * 10)


@pytest.mark.parametrize('perm,vals', [('edit_name', (True, True, True)), (
    'edit_email', (True, True, False)), ('add_user', (False, True, False))])
def test_role_permissions(thomas, superuser, fixed, perm, vals, login_endpoint,
                          test_client):
    for user, val in zip([thomas, superuser, fixed], vals):
        with test_client:
            login_endpoint(user.id)
            if val:
                a.ensure_permission(perm, course_id=None)
            else:
                with pytest.raises(APIException) as err:
                    a.ensure_permission(perm, course_id=None)
                assert err.value.api_code == APICodes.INCORRECT_PERMISSION
    with pytest.raises(APIException) as err:
        a.ensure_permission(perm)
    assert err.value.api_code == APICodes.NOT_LOGGED_IN


def test_all_permissions(thomas, bs_course, pse_course, aco_course):
    all_perms = {
        'edit_name': True,
        'edit_email': True,
        'add_user': False,
    }
    assert all_perms == thomas.get_all_permissions()
    bs_perms = {
        'add_own_work': False,
        'add_others_work': True,
        'remove_course': False,
    }
    aco_perms = {
        'add_own_work': False,
        'add_others_work': False,
        'remove_course': False,
    }
    pse_perms = {
        'add_own_work': True,
        'add_others_work': False,
        'remove_course': False,
    }
    assert bs_perms == thomas.get_all_permissions(bs_course.id)
    assert pse_perms == thomas.get_all_permissions(pse_course.id)
    assert aco_perms == thomas.get_all_permissions(aco_course.id)


def test_all_permissions(thomas, bs_course, pse_course, aco_course, superuser,
                         fixed, login_endpoint, test_client):
    for user in [thomas, superuser, fixed]:
        with test_client:
            login_endpoint(user.id)
            for course in [bs_course, pse_course, aco_course, None]:
                query = {} if course is None else {'course_id': course.id}
                rv = test_client.get(
                    '/api/v1/permissions/', query_string=query)
                for perm, val in json.loads(rv.get_data(as_text=True)).items():
                    assert val == user.has_permission(perm, course)
            test_client.post('/api/v1/logout')

    rv = test_client.get('/api/v1/permissions/')
    assert rv.status_code == 401

    with test_client:
        login_endpoint(thomas.id)
        rv = test_client.get(
            '/api/v1/permissions/', query_string={'course_id': 'a'})
        assert rv.status_code == 400

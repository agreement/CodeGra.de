# -*- py-isort-options: '("-sg *"); -*-
import pytest
import os
import sys
import flask_login
import flask

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + '/../')

import psef.models as m
import psef.auth as a
from psef.errors import APIException


@pytest.fixture(scope='module')
def perms(db):
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
        db.session.add(perm)
    db.session.commit()
    yield perms


@pytest.fixture(scope='module')
def student_role(db, perms):
    role = m.Role(name='student', _permissions={perms[1].name: perms[1]})
    db.session.add(role)
    db.session.commit()
    yield role


@pytest.fixture(scope='module')
def fixed_role(db, perms):
    role = m.Role(name='fixed', _permissions={})
    db.session.add(role)
    db.session.commit()
    yield role


@pytest.fixture(scope='module')
def admin_role(db, perms):
    role = m.Role(
        name='admin',
        _permissions={p.name: p
                      for p in perms if not p.default_value})
    db.session.add(role)
    db.session.commit()
    yield role


@pytest.fixture(scope='module')
def pse_course(db):
    pse = m.Course(name='Project Software Engineering')
    db.session.add(pse)
    db.session.commit()
    yield pse


@pytest.fixture(scope='module')
def bs_course(db):
    bs = m.Course(name='Besturingssystemen')
    db.session.add(bs)
    db.session.commit()
    yield bs


@pytest.fixture(scope='module')
def aco_course(db):
    aco = m.Course(name='Architectuur en Computerarchitectuur')
    db.session.add(aco)
    db.session.commit()
    yield aco


@pytest.fixture(scope='module')
def ta_crole(db, bs_course, perms):
    ta = m.CourseRole(
        name='TA',
        course=bs_course,
        _permissions={p.name: p
                      for p in perms[3:5]})
    ta2 = m.CourseRole(name='TA', course=None, _permissions={})
    db.session.add(ta)
    db.session.add(ta2)
    db.session.commit()
    yield ta


@pytest.fixture(scope='module')
def student_crole(db, pse_course):
    student = m.CourseRole(name='student', course=pse_course)
    db.session.add(student)
    db.session.commit()
    yield student


@pytest.fixture(scope='module')
def thomas(db, perms, student_role, bs_course, student_crole, pse_course,
           ta_crole):
    thomas = m.User(
        name='Thomas Schaper',
        password='',
        email='th',
        role=student_role,
        courses={bs_course.id: ta_crole,
                 pse_course.id: student_crole})

    db.session.add(thomas)
    db.session.commit()
    yield m.User.query.filter_by(name='Thomas Schaper').first()


@pytest.fixture(scope='module')
def superuser(db, admin_role):
    suser = m.User(name='Super User', role=admin_role, password='', email='su')
    db.session.add(suser)
    db.session.commit()
    yield m.User.query.filter_by(name='Super User').first()


@pytest.fixture(scope='module')
def fixed(db, fixed_role):
    suser = m.User(name='Fixed', role=fixed_role, password='', email='f')
    db.session.add(suser)
    db.session.commit()
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
                assert err.value.api_code == APIException.INCORRECT_PERMISSION
    for course, val in zip([bs_course, pse_course, aco_course], vals):
        with pytest.raises(APIException) as err:
            a.ensure_permission(perm, course_id=course.id)
        assert err.value.api_code == APIException.NOT_LOGGED_IN


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
                assert err.value.api_code == APIException.INCORRECT_PERMISSION
    with pytest.raises(APIException) as err:
        a.ensure_permission(perm)
    assert err.value.api_code == APIException.NOT_LOGGED_IN

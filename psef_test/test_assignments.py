# -*- py-isort-options: '("-sg *"); -*-
import pytest
import os
import sys
import flask_login
import flask
import json

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + '/../')

import psef.models as m
import psef.views as v


@pytest.fixture(scope='module')
def perms(session):
    perms = []
    perms.append(
        m.Permission(
            name='can_see_assignments',
            default_value=True,
            course_permission=True))
    perms.append(
        m.Permission(
            name='can_see_others_work',
            default_value=False,
            course_permission=True))
    perms.append(
        m.Permission(
            name='can_see_own_work',
            default_value=True,
            course_permission=True))

    for perm in perms:
        session.add(perm)
    session.commit()
    yield perms


@pytest.fixture(scope='module')
def bs_works(session, bs_course, thomas, other):
    works = []
    assig = bs_course[1][0]
    works.append(
        m.Work(
            assignment=assig,
            user=thomas,
            state='initial',
            edit=0,
            grade=10,
            comment='none'))
    works.append(
        m.Work(
            assignment=assig,
            user=other,
            state='done',
            edit=0,
            grade=10,
            comment='none'))
    for perm in works:
        session.add(perm)
    session.commit()
    yield works


@pytest.fixture(scope='module')
def student_crole2(session, pse_course, bs_course):
    student = m.CourseRole(name='student2', course=pse_course[0])
    session.add(student)
    student2 = m.CourseRole(name='student2', course=bs_course[0])
    session.add(student2)
    session.commit()
    yield student2, student


@pytest.fixture(scope='module')
def student_crole(session, pse_course, bs_course, perms):
    student = m.CourseRole(
        name='student',
        course=pse_course[0],
        _permissions={perms[1].name: perms[1]})
    session.add(student)
    student2 = m.CourseRole(
        name='student',
        course=bs_course[0],
        _permissions={perms[1].name: perms[1]})
    session.add(student2)
    session.commit()
    yield student2, student


@pytest.fixture(scope='module')
def student_role(session):
    role = m.Role(name='student', _permissions={})
    session.add(role)
    session.commit()
    yield role


@pytest.fixture(scope='module')
def pse_course(session):
    pse = m.Course(name='Project Software Engineering')
    session.add(pse)
    assignments = []
    assignments.append(
        m.Assignment(name='Final deadline', description='', course=pse))
    for asig in assignments:
        session.add(asig)
    session.commit()
    yield pse, assignments


@pytest.fixture(scope='module')
def bs_course(session):
    bs = m.Course(name='Besturingssystemen')
    session.add(bs)
    assignments = []
    assignments.append(
        m.Assignment(name='Security', description='AA', course=bs))
    assignments.append(m.Assignment(name='Shell', description='BB', course=bs))
    for asig in assignments:
        session.add(asig)
    session.commit()
    yield bs, assignments


@pytest.fixture(scope='module')
def aco_course(session):
    aco = m.Course(name='Architectuur en Computerarchitectuur')
    session.add(aco)
    assignments = []
    assignments.append(
        m.Assignment(name='Doe assembly', description='Wowser', course=aco))
    assignments.append(
        m.Assignment(name='Doe meer assembly', description='aa', course=aco))
    for asig in assignments:
        session.add(asig)
    session.commit()
    yield aco, assignments


@pytest.fixture(scope='module')
def thomas(session, perms, student_role, bs_course, student_crole, pse_course):
    thomas = m.User(
        name='Thomas Schaper',
        password='',
        email='th',
        role=student_role,
        courses={
            bs_course[0].id: student_crole[0],
            pse_course[0].id: student_crole[1]
        })

    session.add(thomas)
    session.commit()
    yield m.User.query.filter_by(name='Thomas Schaper').first()


@pytest.fixture(scope='module')
def other(session, perms, student_role, bs_course, student_crole2, pse_course):
    student_crole = student_crole2
    thomas = m.User(
        name='Other',
        password='',
        email='ths',
        role=student_role,
        courses={
            bs_course[0].id: student_crole[0],
            pse_course[0].id: student_crole[1]
        })

    session.add(thomas)
    session.commit()
    yield m.User.query.filter_by(name='Other').first()


def test_get_student_assignments(thomas, aco_course, bs_course, pse_course,
                                 login_endpoint, test_client):
    with test_client:
        login_endpoint(thomas.id)
        rv = test_client.get('/api/v1/assignments/')
        data = json.loads(rv.get_data(as_text=True))
        for assig in pse_course[1] + bs_course[1]:
            assert {
                "id": assig.id,
                "name": assig.name,
                'course_name': assig.course.name,
                'course_id': assig.course.id
            } in data
        assert len(data) == len(pse_course[1] + bs_course[1])
        test_client.post('/api/v1/logout')

    rv = test_client.get('/api/v1/assignments/')
    assert rv.status_code == 401


def test_get_student_assignment(thomas, bs_course, aco_course, login_endpoint,
                                test_client):
    with test_client:
        login_endpoint(thomas.id)
        for assignment in bs_course[1]:
            rv = test_client.get(
                '/api/v1/assignments/{}'.format(assignment.id))
            data = json.loads(rv.get_data(as_text=True))
            assert data == {
                'name': assignment.name,
                'description': assignment.description,
                'course_name': assignment.course.name,
                'course_id': assignment.course_id,
            }

        for assignment in aco_course[1]:
            rv = test_client.get(
                '/api/v1/assignments/{}'.format(assignment.id))
            assert rv.status_code == 403

        test_client.post('/api/v1/logout')

    for assignment in bs_course[1]:
        rv = test_client.get('/api/v1/assignments/{}'.format(assignment.id))
        assert rv.status_code == 401


def test_get_all_works(thomas, other, bs_course, login_endpoint, test_client,
                       bs_works):
    with test_client:
        login_endpoint(thomas.id)
        assig = bs_course[1][0]
        rv = test_client.get('/api/v1/assignments/{}/works'.format(assig.id))
        data = json.loads(rv.get_data(as_text=True))
        print(data)
        assert data[0]['user_id'] == thomas.id
        assert data[1]['user_id'] == other.id
        assert len(data) == 2

        test_client.post('/api/v1/logout')
        login_endpoint(other.id)
        assig = bs_course[1][0]
        rv = test_client.get('/api/v1/assignments/{}/works'.format(assig.id))
        data = json.loads(rv.get_data(as_text=True))
        print(data)
        assert data[0]['user_id'] == other.id
        assert len(data) == 1

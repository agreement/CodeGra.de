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
def perms(db):
    perms = []
    perms.append(
        m.Permission(
            name='can_see_assignments',
            default_value=True,
            course_permission=True))

    for perm in perms:
        db.session.add(perm)
    db.session.commit()
    yield perms


@pytest.fixture(scope='module')
def student_crole(db, pse_course, bs_course):
    student = m.CourseRole(name='student', course=pse_course[0])
    db.session.add(student)
    student2 = m.CourseRole(name='student', course=bs_course[0])
    db.session.add(student2)
    db.session.commit()
    yield student2, student


@pytest.fixture(scope='module')
def student_role(db):
    role = m.Role(name='student', _permissions={})
    db.session.add(role)
    db.session.commit()
    yield role


@pytest.fixture(scope='module')
def pse_course(db):
    pse = m.Course(name='Project Software Engineering')
    db.session.add(pse)
    assignments = []
    assignments.append(
        m.Assignment(name='Final deadline', description='', course=pse))
    for asig in assignments:
        db.session.add(asig)
    db.session.commit()
    yield pse, assignments


@pytest.fixture(scope='module')
def bs_course(db):
    bs = m.Course(name='Besturingssystemen')
    db.session.add(bs)
    assignments = []
    assignments.append(
        m.Assignment(name='Security', description='', course=bs))
    assignments.append(m.Assignment(name='Shell', description='', course=bs))
    for asig in assignments:
        db.session.add(asig)
    db.session.commit()
    yield bs, assignments


@pytest.fixture(scope='module')
def aco_course(db):
    aco = m.Course(name='Architectuur en Computerarchitectuur')
    db.session.add(aco)
    assignments = []
    assignments.append(
        m.Assignment(name='Doe assembly', description='', course=aco))
    assignments.append(
        m.Assignment(name='Doe meer assembly', description='', course=aco))
    for asig in assignments:
        db.session.add(asig)
    db.session.commit()
    yield aco, assignments


@pytest.fixture(scope='module')
def thomas(db, perms, student_role, bs_course, student_crole, pse_course):
    thomas = m.User(
        name='Thomas Schaper',
        password='',
        email='th',
        role=student_role,
        courses={
            bs_course[0].id: student_crole[0],
            pse_course[0].id: student_crole[1]
        })

    db.session.add(thomas)
    db.session.commit()
    yield m.User.query.filter_by(name='Thomas Schaper').first()


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

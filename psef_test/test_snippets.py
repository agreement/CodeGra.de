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
            name='can_use_snippets',
            default_value=True,
            course_permission=False))

    for perm in perms:
        session.add(perm)
    session.commit()
    yield perms


@pytest.fixture(scope='module')
def student_role(session):
    role = m.Role(name='student', _permissions={})
    session.add(role)
    session.commit()
    yield role


@pytest.fixture(scope='module')
def thomas(session, perms, student_role):
    thomas = m.User(
        name='Thomas Schaper',
        password='',
        email='th',
        role=student_role,
        courses={})

    session.add(thomas)
    session.commit()
    yield m.User.query.filter_by(name='Thomas Schaper').first()


@pytest.fixture(scope='module')
def other(session, perms, student_role):
    thomas = m.User(
        name='Other', password='', email='ths', role=student_role, courses={})

    session.add(thomas)
    session.commit()
    yield m.User.query.filter_by(name='Other').first()


@pytest.fixture(scope='module')
def snippets(session, thomas, other):
    tsnips = []
    osnips = []
    tsnips.append(m.Snippet(key='hello', value='bye', user=thomas))
    tsnips.append(
        m.Snippet(key='malloc', value='don\'t forget malloc', user=thomas))

    osnips.append(m.Snippet(key='asd', value='WWWWWWWWW\nWWWW', user=other))

    for snip in osnips + tsnips:
        session.add(snip)
    session.commit()
    yield tsnips, osnips


def test_get_all_snippets(thomas, other, snippets, login_endpoint,
                          test_client):
    for user, snips in zip([thomas, other], snippets):
        with test_client:
            login_endpoint(user.id)
            rv = test_client.get('/api/v1/snippets/')
            data = json.loads(rv.get_data(as_text=True))
            for snip in snips:
                assert {
                    'key': snip.key,
                    'value': snip.value,
                    'id': snip.id
                } in data
            assert len(snips) == len(data)
            test_client.post('/api/v1/logout')

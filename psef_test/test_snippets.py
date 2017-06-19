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


@pytest.fixture(scope='function')
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

    for snip in osnips + tsnips:
        if m.Snippet.query.get(snip.id):
            session.delete(snip)
    session.commit()


def test_get_all_snippets(thomas, other, snippets, login_endpoint,
                          test_client):
    for user, snips in zip([thomas, other], snippets):
        with test_client:
            login_endpoint(user.id)
            rv = test_client.get('/api/v1/snippets/')
            data = json.loads(rv.get_data(as_text=True))
            for snip in snips:
                assert snip.key in data
                assert data[snip.key] ==  {
                    'value': snip.value,
                    'id': snip.id
                }
            assert len(snips) == len(data)
            test_client.post('/api/v1/logout')
    rv = test_client.get('/api/v1/snippets/')
    assert rv.status_code == 401


def test_delete_snippets(thomas, snippets, login_endpoint, test_client):
    with test_client:
        login_endpoint(thomas.id)

        rv = test_client.delete(
            '/api/v1/snippets/{}'.format(snippets[0][0].id))
        assert rv.status_code == 204

        rv = test_client.get('/api/v1/snippets/')
        data = json.loads(rv.get_data(as_text=True))

        assert snippets[0][0].key not in data
        assert len(data) + 1 == len(snippets[0])

        rv = test_client.delete(
            '/api/v1/snippets/{}'.format(snippets[1][0].id))
        assert rv.status_code == 403

        test_client.post('/api/v1/logout')

    rv = test_client.delete('/api/v1/snippets/{}'.format(snippets[0][1].id))
    assert rv.status_code == 401


def test_add_snippets(thomas, login_endpoint, test_client):
    headers = [('Content-Type', 'application/json')]
    with test_client:
        def put(data):
            return test_client.put('/api/v1/snippet',
                                   data=json.dumps(data),
                                   headers=headers)
        login_endpoint(thomas.id)

        rv = put({'key': 'hello', 'value': 'val'})
        assert rv.status_code == 204

        rv = test_client.get('/api/v1/snippets/')
        data = json.loads(rv.get_data(as_text=True))

        items = len(data)

        for key, perm in data.items():
            if key == 'hello' and perm['value'] == 'val':
                break
        else:
            assert False

        rv = put({'key': 'hello', 'value': 'bye'})
        assert rv.status_code == 204

        rv = test_client.get('/api/v1/snippets/')
        data = json.loads(rv.get_data(as_text=True))

        assert items == len(data)

        for key, perm in data.items():
            if key == 'hello' and perm['value'] == 'bye':
                break
        else:
            assert False

        test_client.post('/api/v1/logout')

        rv = put({'key': 'hello', 'value': 'bye'})
        assert rv.status_code == 401

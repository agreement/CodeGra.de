# -*- py-isort-options: '("-sg *"); -*-
import os
import sys

import flask_login
import pytest

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + '/../')

import psef
from psef import db as _db
import psef.models as m
import psef.auth as a

TESTDB = 'test_project.db'
TESTDB_PATH = "/tmp/psef-{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


@pytest.fixture(scope='session')
def app(request):
    """Session-wide test `Flask` application."""
    settings_override = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URI
    }
    app = psef.create_app(settings_override)

    # Establish an application context before running the tests.
    ctx = app.app_context()
    ctx.push()

    yield app

    ctx.pop()


@pytest.fixture(scope='session')
def test_client(app):
    yield app.test_client()


@pytest.fixture(scope='session')
def login_endpoint(app, test_client):
    @app.route('/auto_login/<int:id>')
    def _login(id):
        user = m.User.query.get(id)
        flask_login.login_user(user, remember=True)
        return "ok"
    yield lambda id: test_client.get('/auto_login/' + str(id),
                                     follow_redirects=True)


@pytest.fixture(scope='module')
def db(app, request):
    """Session-wide test database."""
    if os.path.exists(TESTDB_PATH):
        os.unlink(TESTDB_PATH)
    _db.app = app
    _db.create_all()

    yield _db

    _db.drop_all()
    os.unlink(TESTDB_PATH)


pytest.fixture(scope='module')


def session(db, request):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={})
    session = db.create_scoped_session(options=options)

    db.session = session

    yield session

    transaction.rollback()
    connection.close()
    session.remove()

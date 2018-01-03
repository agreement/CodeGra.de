import os
import sys
import copy
import json
import datetime
import contextlib

import pytest
import flask_migrate
import flask_jwt_extended as flask_jwt
from flask import _app_ctx_stack as ctx_stack
from werkzeug.local import LocalProxy

import psef
import manage
import psef.auth as a
import psef.models as m

TESTDB = 'test_project.db'
TESTDB_PATH = "/tmp/psef/psef-{}".format(TESTDB)
TEST_DATABASE_URI = 'sqlite:///' + TESTDB_PATH


def pytest_addoption(parser):
    parser.addoption(
        "--postgresql",
        action="store",
        default=False,
        help="Run the test using postresql"
    )


@pytest.fixture(scope='session')
def app(request):
    """Session-wide test `Flask` application."""
    settings_override = {
        'TESTING': True,
        'DEBUG': True,
        'UPLOAD_DIR': f'/tmp/psef/uploads',
        'CELERY_CONFIG':
            {
                'BROKER_URL': 'redis:///',
                'BACKEND_URL': 'redis:///'
            },
        'MIRROR_UPLOAD_DIR': f'/tmp/psef/mirror_uploads',
        'MAX_UPLOAD_SIZE': 2 ** 20,  # 1mb
        'LTI_CONSUMER_KEY_SECRETS': {
            'my_lti': '12345678'
        },
    }
    if request.config.getoption('--postgresql'):
        print('Running with postgres!')
        pdb = request.config.getoption('--postgresql')
        settings_override['SQLALCHEMY_DATABASE_URI'] = f'postgresql:///{pdb}'
        settings_override['_USING_SQLITE'] = False
    else:
        settings_override['SQLALCHEMY_DATABASE_URI'] = TEST_DATABASE_URI
        settings_override['_USING_SQLITE'] = True

    settings_override['CELERY_CONFIG'] = {
        'CELERY_TASK_ALWAYS_EAGER': True,
        'CELERY_TASK_EAGER_PROPAGATES': True,
    }
    app = psef.create_app(settings_override, skip_celery=True)

    psef.tasks.celery.conf.update(
        {
            'task_always_eager': False,
            'task_eager_propagates': False,
        }
    )

    # Establish an application context before running the tests.
    with app.app_context():

        class FlaskTestClientProxy(object):
            def __init__(self, app):
                self.app = app

            def __call__(self, environ, start_response):
                if (_TOKENS and
                        _TOKENS[-1] is not None and
                        'HTTP_AUTHORIZATION' not in environ):
                    environ['HTTP_AUTHORIZATION'] = f'Bearer {_TOKENS[-1]}'
                return self.app(environ, start_response)

        app.wsgi_app = FlaskTestClientProxy(app.wsgi_app)

        yield app


@pytest.fixture
def test_client(app):
    client = app.test_client()

    def req(
        method,
        url,
        status_code,
        result=None,
        query=None,
        data=None,
        real_data=None,
        include_response=False,
        **kwargs
    ):
        if real_data is None:
            data = json.dumps(data) if data is not None else None
            kwargs['content_type'] = 'application/json'
        else:
            data = real_data
        rv = getattr(client, method)(
            url,
            query_string=query,
            data=data,
            **kwargs,
        )

        print(rv.get_data(as_text=True))
        assert rv.status_code == status_code

        if status_code == 204:
            assert rv.get_data(as_text=True) == ''
            assert result is None
            res = None
        else:
            val = json.loads(rv.get_data(as_text=True))
            res = copy.deepcopy(val)

        def checker(vals, tree):
            is_list = isinstance(tree, list)
            i = 0
            for k, value in enumerate(tree) if is_list else tree.items():
                i += 1
                assert is_list or k in vals

                if isinstance(value, type):
                    assert isinstance(vals[k], value)
                elif isinstance(value, list) or isinstance(value, dict):
                    checker(vals[k], value)
                else:
                    assert vals[k] == value

            assert len(vals) == i

        if result is not None:
            checker({'top': val}, {'top': result})

        if include_response:
            return res, rv
        return res

    client.req = req
    yield client


@pytest.fixture
def error_template():
    yield {
        'code': str,
        'message': str,
        'description': str,
    }


@pytest.fixture(params=[True, False])
def boolean(request):
    yield request.param


_TOKENS = []


@pytest.fixture(autouse=True)
def logged_in():
    @contextlib.contextmanager
    def _login(user):
        setattr(ctx_stack.top, 'jwt_user', None)
        if isinstance(user, str) and user == 'NOT_LOGGED_IN':
            _TOKENS.append(None)
            res = None
        else:
            _TOKENS.append(
                flask_jwt.create_access_token(identity=user.id, fresh=True)
            )
            res = user

        yield res

        _TOKENS.pop(-1)
        setattr(ctx_stack.top, 'jwt_user', None)

    yield _login
    _TOKENS.clear()

    _TOKENS.clear()


@pytest.fixture
def named_user(session, request):
    if request.param == 'NOT_LOGGED_IN':
        return 'NOT_LOGGED_IN'
    return LocalProxy(session.query(m.User).filter_by(name=request.param).one)


@pytest.fixture
def student_user(session):
    return LocalProxy(session.query(m.User).filter_by(name="Stupid1").one)


@pytest.fixture
def teacher_user(session):
    return LocalProxy(session.query(m.User).filter_by(name="Robin").one)


@pytest.fixture
def ta_user(session):
    return LocalProxy(
        session.query(m.User).filter_by(name="Thomas Schaper").one
    )


@pytest.fixture
def admin_user(session):
    return LocalProxy(session.query(m.User).filter_by(name="admin").one)


@pytest.fixture
def pse_course(session):
    return session.query(m.Course
                         ).filter_by(name="Project Software Engineering").one()


@pytest.fixture
def prog_course(session):
    yield m.Course.query.filter_by(name='Programmeertalen').one()


@pytest.fixture
def inprog_course(session):
    yield m.Course.query.filter_by(name='Inleiding Programmeren').one()


@pytest.fixture
def bs_course(session):
    return session.query(m.Course).filter_by(name="Besturingssystemen").one()


@pytest.fixture
def prolog_course(session):
    return session.query(
        m.Course
    ).filter_by(name="Introductie Logisch programmeren").one()


@pytest.fixture(scope='session', autouse=True)
def db(app, request):
    """Session-wide test database."""
    if os.path.exists(TESTDB_PATH):
        os.unlink(TESTDB_PATH)

    if not request.config.getoption('--postgresql'):
        psef.models.db.create_all()

    manage.app = app
    manage.seed_force(psef.models.db)
    manage.test_data(psef.models.db)

    yield psef.models.db

    if request.config.getoption('--postgresql'):
        psef.models.db.drop_all()
        psef.models.db.create_all()
    else:
        os.unlink(TESTDB_PATH)


@pytest.fixture
def session(app, db):
    """Creates a new database session for a test."""
    connection = db.engine.connect()
    transaction = connection.begin()

    options = dict(bind=connection, binds={}, autoflush=False)
    session = db.create_scoped_session(options=options)

    psef.models.db.session = session

    yield session

    transaction.rollback()

    try:
        session.remove()
        connection.close()
    except:
        pass

    db.session.begin(subtransactions=True)


@pytest.fixture
def monkeypatch_celery(app, monkeypatch):
    psef.tasks.celery.conf.task_always_eager = True
    psef.tasks.celery.conf.task_eager_propagates = True
    yield
    psef.tasks.celery.conf.task_always_eager = False
    psef.tasks.celery.conf.task_eager_propagates = False


@pytest.fixture(params=['Programmeertalen'])
def course_name(request):
    yield request.param


@pytest.fixture(params=[False])
def state_is_hidden(request):
    yield request.param


@pytest.fixture(params=[False])
def with_works(request):
    yield request.param


@pytest.fixture(params=['new'])
def assignment(course_name, state_is_hidden, session, request, with_works):
    course = m.Course.query.filter_by(name=course_name).one()
    state = (
        m._AssignmentStateEnum.hidden
        if state_is_hidden else m._AssignmentStateEnum.open
    )
    assig = m.Assignment(
        name='TEST COURSE',
        state=state,
        course=course,
        deadline=datetime.datetime.utcnow() +
        datetime.timedelta(days=1 if request.param == 'new' else -1)
    )
    session.add(assig)
    session.commit()

    if with_works:
        names = ['Stupid1', 'Stupid2', 'Stupid3', 'Œlµo']
        if with_works != 'single':
            names += names
        for uname in names:
            user = m.User.query.filter_by(name=uname).one()
            work = m.Work(assignment=assig, user=user)
            session.add(work)
        session.commit()

    yield assig


@pytest.fixture
def filename(request):
    yield request.param


@pytest.fixture
def stub_function_class():
    class StubFunction:
        def __init__(self, ret_func=lambda: None):
            self.args = []
            self.kwargs = []
            self.rets = []
            self.ret_func = ret_func

        def __call__(self, *args, **kwargs):
            self.args.append(args)
            self.kwargs.append(kwargs)
            self.rets.append(self.ret_func())
            return self.rets[-1]

        @property
        def called(self):
            return len(self.args) > 0

        def reset(self):
            self.__init__(self.ret_func)

    yield StubFunction


@pytest.fixture
def assignment_real_works(
    filename,
    test_client,
    logged_in,
    assignment,
):
    res = []
    for name in ['Stupid1', 'Stupid2', 'Œlµo']:
        user = m.User.query.filter_by(name=name).one()
        with logged_in(user):
            res.append(
                test_client.req(
                    'post',
                    f'/api/v1/assignments/{assignment.id}/submission',
                    201,
                    real_data={
                        'file':
                            (
                                f'{os.path.dirname(__file__)}/../'
                                f'test_data/test_linter/{filename}',
                                os.path.basename(os.path.realpath(filename))
                            )
                    }
                )
            )

    yield assignment, res[0]

import os
import urllib
import datetime

import jwt
import pytz
import pytest
import dateutil.parser

import psef.lti as lti
import psef.auth as auth
import psef.models as m

perm_error = pytest.mark.perm_error
data_error = pytest.mark.data_error


@pytest.fixture(autouse=True)
def monkeypatch_oauth_check(monkeypatch):
    def valid_oauth(*args, **kwargs):
        return

    monkeypatch.setattr(auth, 'ensure_valid_oauth', valid_oauth)


def test_lti_new_user_new_course(test_client, app, logged_in, ta_user):
    due_at = datetime.datetime.utcnow() + datetime.timedelta(
        days=1, hours=1, minutes=2
    )
    due_at = due_at.replace(second=0, microsecond=0)

    def do_lti_launch(
        name='A the A-er',
        lti_id='USER_ID',
        source_id='',
        published='false',
        username='a-the-a-er',
        due=None
    ):
        with app.app_context():
            due_date = due or due_at.isoformat() + 'Z'
            data = {
                'custom_canvas_course_name': 'NEW_COURSE',
                'custom_canvas_course_id': 'MY_COURSE_ID',
                'custom_canvas_assignment_id': 'MY_ASSIG_ID',
                'custom_canvas_assignment_title': 'MY_ASSIG_TITLE',
                'roles': 'instructor',
                'custom_canvas_user_login_id': username,
                'custom_canvas_course_title': 'Common Lisp',
                'custom_canvas_assignment_due_at': due_date,
                'custom_canvas_assignment_published': published,
                'user_id': lti_id,
                'lis_person_contact_email_primary': 'a@a.nl',
                'lis_person_name_full': name,
                'context_id': 'NO_CONTEXT',
                'context_title': 'WRONG_TITLE',
                'oauth_consumer_key': 'my_lti',
                'lis_outcome_service_url': source_id,
            }
            if source_id:
                data['lis_result_sourcedid'] = source_id
            res = test_client.post('/api/v1/lti/launch/1', data=data)

            url = urllib.parse.urlparse(res.headers['Location'])
            jwt = urllib.parse.parse_qs(url.query)['jwt'][0]
            lti_res = test_client.req(
                'get',
                '/api/v1/lti/launch/2',
                200,
                headers={'Jwt': jwt},
            )
            if published == 'false':
                assert lti_res['assignment']['state'] == 'hidden'
            else:
                assert m.Assignment.query.get(
                    lti_res['assignment']['id']
                ).state == m._AssignmentStateEnum.open
            assert lti_res['assignment']['course']['name'] == 'NEW_COURSE'
            if due is None:
                assert lti_res['assignment']['deadline'] == due_at.isoformat()
            return lti_res['assignment'], lti_res.get('access_token', None)

    def get_user_info(token):
        with app.app_context():
            return test_client.req(
                'get',
                '/api/v1/login',
                200,
                headers={'Authorization': f'Bearer {token}'} if token else {}
            )

    assig, token = do_lti_launch(due='WOW, wrong')
    assert (dateutil.parser.parse(assig['deadline']) - due_at).days == 363
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    assert out['username'] == 'a-the-a-er'
    old_id = out['id']

    _, token = do_lti_launch()
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    assert out['username'] == 'a-the-a-er'
    assert out['id'] == old_id

    user = m.User.query.filter_by(name=out['name']).one()
    assert len(user.courses) == 1
    assert list(user.courses.values())[0].name == 'Teacher'
    with logged_in(user):
        _, token = do_lti_launch()
        assert token is None
        out = get_user_info(False)
        assert out['name'] == 'A the A-er'
        assert out['username'] == 'a-the-a-er'

    with logged_in(ta_user):
        _, token = do_lti_launch()
        out = get_user_info(token)
        assert out['name'] == 'A the A-er'
        assert out['username'] == 'a-the-a-er'

    with logged_in(ta_user):
        assig, token = do_lti_launch(
            lti_id='THOMAS_SCHAPER',
            source_id='WOW',
            username='SOMETHING_ELSE',
            due='WOW_WRONG',
        )
        assert token is None
        out = get_user_info(False)
        assert out['name'] == ta_user.name
        assert out['username'] == ta_user.username
        assert m.User.query.get(ta_user.id).lti_user_id == 'THOMAS_SCHAPER'

        assert assig['id'] in ta_user.assignment_results

        assert dateutil.parser.parse(assig['deadline']) == due_at

        assig, token = do_lti_launch(
            lti_id='THOMAS_SCHAPER',
            source_id='WOW2',
            published='true',
            username='WOW33',
        )
        out = get_user_info(False)
        assert ta_user.assignment_results[assig['id']].sourcedid == 'WOW2'


def test_lti_no_course_roles(
    test_client, app, logged_in, ta_user, monkeypatch
):
    due_at = datetime.datetime.utcnow() + datetime.timedelta(days=1)

    def do_lti_launch(
        username='A the A-er',
        lti_id='USER_ID',
        source_id='',
        published='false',
        parse=True,
        code=200
    ):
        with app.app_context():
            data = {
                'custom_canvas_course_name': 'NEW_COURSE',
                'custom_canvas_course_id': 'MY_COURSE_ID',
                'custom_canvas_assignment_id': 'MY_ASSIG_ID',
                'custom_canvas_assignment_title': 'MY_ASSIG_TITLE',
                'roles': 'administrator,non_existing',
                'custom_canvas_user_login_id': username,
                'custom_canvas_course_title': 'Common Lisp',
                'custom_canvas_due_at': due_at.isoformat(),
                'custom_canvas_assignment_published': published,
                'user_id': lti_id,
                'lis_person_contact_email_primary': 'a@a.nl',
                'lis_person_name_full': username,
                'context_id': 'NO_CONTEXT',
                'context_title': 'WRONG_TITLE',
                'oauth_consumer_key': 'my_lti',
                'lis_outcome_service_url': source_id,
            }
            if source_id:
                data['lis_result_sourcedid'] = source_id
            res = test_client.post('/api/v1/lti/launch/1', data=data)

            url = urllib.parse.urlparse(res.headers['Location'])
            jwt = urllib.parse.parse_qs(url.query)['jwt'][0]
            lti_res = test_client.req(
                'get',
                '/api/v1/lti/launch/2',
                code,
                headers={'Jwt': jwt},
            )
            if not parse:
                return lti_res

            if published == 'false':
                assert lti_res['assignment']['state'] == 'hidden'
            else:
                assert m.Assignment.query.get(
                    lti_res['assignment']['id']
                ).state == m._AssignmentStateEnum.open
            assert lti_res['assignment']['course']['name'] == 'NEW_COURSE'
            return lti_res['assignment'], lti_res.get(
                'access_token', None
            ), lti_res

    def get_user_info(token):
        with app.app_context():
            return test_client.req(
                'get',
                '/api/v1/login',
                200,
                headers={'Authorization': f'Bearer {token}'} if token else {}
            )

    _, token, res = do_lti_launch()
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    assert res['new_role_created']
    old_id = out['id']

    _, token, __ = do_lti_launch()
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    assert out['id'] == old_id

    user = m.User.query.filter_by(name=out['name']).one()
    assert user.role.name == 'Admin'
    assert len(user.courses) == 1
    assert list(user.courses.values())[0].name == 'non_existing'

    monkeypatch.setitem(app.config['FEATURES'], 'AUTOMATIC_LTI_ROLE', False)

    _, __, res = do_lti_launch(username='NEW_USERNAME')
    assert not res['new_role_created']

    res = do_lti_launch(username='NEW_USER', lti_id='5', code=400, parse=False)
    assert res['message'].startswith('The given LTI role was not')


@pytest.mark.parametrize('patch', [True, False])
@pytest.mark.parametrize('filename', [
    ('correct.tar.gz'),
])
def test_lti_grade_passback(
    test_client, app, logged_in, ta_user, filename, monkeypatch, patch,
    monkeypatch_celery
):
    due_at = datetime.datetime.utcnow() + datetime.timedelta(days=1)

    class Patch:
        def __init__(self):
            self.called = False
            self.args = []
            self.kwargs = {}

        def __call__(self, *args, **kwargs):
            self.called = True
            self.args = args
            self.kwargs = kwargs

    patch_delete = Patch()
    patch_replace = Patch()

    if patch:
        monkeypatch.setitem(app.config, '_USING_SQLITE', True)

    monkeypatch.setattr(lti.OutcomeRequest, 'post_delete_result', patch_delete)
    monkeypatch.setattr(
        lti.OutcomeRequest, 'post_replace_result', patch_replace
    )

    def do_lti_launch(
        username='A the A-er',
        lti_id='USER_ID',
        source_id='NON_EXISTING2!',
        published='false'
    ):
        with app.app_context():
            data = {
                'custom_canvas_course_name': 'NEW_COURSE',
                'custom_canvas_course_id': 'MY_COURSE_ID_100',
                'custom_canvas_assignment_id': 'MY_ASSIG_ID_100',
                'custom_canvas_assignment_title': 'MY_ASSIG_TITLE',
                'roles': 'administrator,instructor',
                'custom_canvas_user_login_id': username,
                'custom_canvas_course_title': 'Common Lisp',
                'custom_canvas_due_at': due_at.isoformat(),
                'custom_canvas_assignment_published': published,
                'user_id': lti_id,
                'lis_person_contact_email_primary': 'a@a.nl',
                'lis_person_name_full': username,
                'context_id': 'NO_CONTEXT!!',
                'context_title': 'WRONG_TITLE!!',
                'oauth_consumer_key': 'my_lti',
                'lis_outcome_service_url': source_id,
            }
            if source_id:
                data['lis_result_sourcedid'] = source_id
            res = test_client.post('/api/v1/lti/launch/1', data=data)

            url = urllib.parse.urlparse(res.headers['Location'])
            jwt = urllib.parse.parse_qs(url.query)['jwt'][0]
            lti_res = test_client.req(
                'get',
                '/api/v1/lti/launch/2',
                200,
                headers={'Jwt': jwt},
            )
            if published == 'false':
                assert lti_res['assignment']['state'] == 'hidden'
            else:
                assert m.Assignment.query.get(
                    lti_res['assignment']['id']
                ).state == m._AssignmentStateEnum.open
            assert lti_res['assignment']['course']['name'] == 'NEW_COURSE'
            return lti_res['assignment'], lti_res.get('access_token', None)

    def get_upload_file(token, assig_id):
        full_filename = (
            f'{os.path.dirname(__file__)}/'
            f'../test_data/test_blackboard/{filename}'
        )
        with app.app_context():
            test_client.req(
                'post',
                f'/api/v1/assignments/{assig_id}/submission',
                201,
                real_data={'file': (full_filename, 'bb.tar.gz')},
                headers={'Authorization': f'Bearer {token}'},
            )
            res = test_client.req(
                'get', f'/api/v1/assignments/{assig_id}/submissions/', 200
            )
            assert len(res) == 1
            return res[0]

    def set_grade(token, grade, work_id):
        test_client.req(
            'patch',
            f'/api/v1/submissions/{work_id}',
            200,
            data={'grade': grade,
                  'feedback': 'feedback'},
            headers={'Authorization': f'Bearer {token}'},
        )

    assig, token = do_lti_launch()
    work = get_upload_file(token, assig['id'])

    assert patch_replace.called
    assert not patch_delete.called
    assert patch_replace.args[0] is None
    assert 'url' in patch_replace.kwargs['result_data']
    patch_delete.called = False
    patch_replace.called = False

    set_grade(token, 5.0, work['id'])

    assert not patch_delete.called
    assert not patch_replace.called
    patch_delete.called = False
    patch_replace.called = False

    test_client.req(
        'patch',
        f'/api/v1/assignments/{assig["id"]}',
        204,
        data={
            'state': 'done',
        },
        headers={'Authorization': f'Bearer {token}'},
    )

    assert patch_replace.called
    assert not patch_delete.called
    assert patch_replace.args[0] == '0.5'
    assert patch_replace.kwargs['result_data'] is None
    patch_delete.called = False
    patch_replace.called = False

    if patch:
        test_client.req(
            'get',
            f'/api/v1/submissions/{work["id"]}/grade_history/',
            200,
            result=[
                {
                    'changed_at': str,
                    'is_rubric': False,
                    'grade': float,
                    'passed_back': True,
                    'user': dict,
                }
            ],
            headers={'Authorization': f'Bearer {token}'},
        )

    set_grade(token, 6, work['id'])
    assert patch_replace.called
    assert not patch_delete.called
    assert patch_replace.args[0] == '0.6'
    assert patch_replace.kwargs['result_data'] is None
    patch_delete.called = False
    patch_replace.called = False

    set_grade(token, None, work['id'])

    assert not patch_replace.called
    assert patch_delete.called


def test_lti_assignment_create(
    test_client, app, logged_in, ta_user, error_template
):
    def do_lti_launch(
        username='A the A-er',
        lti_id='USER_ID',
        source_id='NON_EXISTING2!',
        published='false'
    ):
        with app.app_context():
            data = {
                'custom_canvas_course_name': 'NEW_COURSE',
                'custom_canvas_course_id': 'MY_COURSE_ID_100',
                'custom_canvas_assignment_id': 'MY_ASSIG_ID_100',
                'custom_canvas_assignment_title': 'MY_ASSIG_TITLE',
                'roles': 'administrator,instructor',
                'custom_canvas_user_login_id': username,
                'custom_canvas_course_title': 'Common Lisp',
                'custom_canvas_assignment_published': published,
                'user_id': lti_id,
                'lis_person_contact_email_primary': 'a@a.nl',
                'lis_person_name_full': username,
                'context_id': 'NO_CONTEXT!!',
                'context_title': 'WRONG_TITLE!!',
                'oauth_consumer_key': 'my_lti',
                'lis_outcome_service_url': source_id,
            }
            if source_id:
                data['lis_result_sourcedid'] = source_id
            res = test_client.post('/api/v1/lti/launch/1', data=data)

            url = urllib.parse.urlparse(res.headers['Location'])
            jwt = urllib.parse.parse_qs(url.query)['jwt'][0]
            lti_res = test_client.req(
                'get',
                '/api/v1/lti/launch/2',
                200,
                headers={'Jwt': jwt},
            )
            if published == 'false':
                assert lti_res['assignment']['state'] == 'hidden'
            else:
                assert m.Assignment.query.get(
                    lti_res['assignment']['id']
                ).state == m._AssignmentStateEnum.open
            assert lti_res['assignment']['course']['name'] == 'NEW_COURSE'
            return lti_res['assignment'], lti_res.get('access_token', None)

    with app.app_context():
        assig, token = do_lti_launch()
        course = assig['course']
        test_client.req(
            'post',
            f'/api/v1/courses/{course["id"]}/assignments/',
            400,
            data={
                'name': 'wow',
            },
            headers={'Authorization': f'Bearer {token}'},
            result=error_template,
        )


def test_reset_lti_email(test_client, app, logged_in, ta_user, session):
    due_at = datetime.datetime.utcnow() + datetime.timedelta(
        days=1, hours=1, minutes=2
    )
    due_at = due_at.replace(second=0, microsecond=0)

    def do_lti_launch(
        email,
        name='A the A-er',
        lti_id='USER_ID',
        source_id='',
        published='false',
        username='a-the-a-er',
        due=None
    ):
        with app.app_context():
            due_date = due or due_at.isoformat() + 'Z'
            data = {
                'custom_canvas_course_name': 'NEW_COURSE',
                'custom_canvas_course_id': 'MY_COURSE_ID',
                'custom_canvas_assignment_id': 'MY_ASSIG_ID',
                'custom_canvas_assignment_title': 'MY_ASSIG_TITLE',
                'roles': 'instructor',
                'custom_canvas_user_login_id': username,
                'custom_canvas_course_title': 'Common Lisp',
                'custom_canvas_assignment_due_at': due_date,
                'custom_canvas_assignment_published': published,
                'user_id': lti_id,
                'lis_person_contact_email_primary': email,
                'lis_person_name_full': name,
                'context_id': 'NO_CONTEXT',
                'context_title': 'WRONG_TITLE',
                'oauth_consumer_key': 'my_lti',
                'lis_outcome_service_url': source_id,
            }
            if source_id:
                data['lis_result_sourcedid'] = source_id
            res = test_client.post('/api/v1/lti/launch/1', data=data)

            url = urllib.parse.urlparse(res.headers['Location'])
            jwt = urllib.parse.parse_qs(url.query)['jwt'][0]
            lti_res = test_client.req(
                'get',
                '/api/v1/lti/launch/2',
                200,
                headers={'Jwt': jwt},
            )
            if published == 'false':
                assert lti_res['assignment']['state'] == 'hidden'
            else:
                assert m.Assignment.query.get(
                    lti_res['assignment']['id']
                ).state == m._AssignmentStateEnum.open
            assert lti_res['assignment']['course']['name'] == 'NEW_COURSE'
            if due is None:
                assert lti_res['assignment']['deadline'] == due_at.isoformat()
            return lti_res['assignment'], lti_res.get('access_token', None)

    def get_user_info(token):
        with app.app_context():
            return test_client.req(
                'get',
                '/api/v1/login',
                200,
                headers={'Authorization': f'Bearer {token}'} if token else {}
            )

    assig, token = do_lti_launch('orig@example.com')
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    assert out['username'] == 'a-the-a-er'
    old_id = out['id']

    _, token = do_lti_launch('new@example.com')
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    assert out['username'] == 'a-the-a-er'
    assert out['email'] == 'orig@example.com'
    assert out['id'] == old_id

    m.User.query.filter_by(id=out['id']).update({'reset_email_on_lti': True})
    session.commit()
    _, token = do_lti_launch('new@example.com')
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    assert out['username'] == 'a-the-a-er'
    assert out['email'] == 'new@example.com'
    assert out['id'] == old_id

    assert not m.User.query.get(out['id']).reset_email_on_lti, """
    This field should be reset
    """


def test_invalid_jwt(
    test_client, app, logged_in, ta_user, session, error_template
):
    due_at = datetime.datetime.utcnow() + datetime.timedelta(
        days=1, hours=1, minutes=2
    )
    due_at = due_at.replace(second=0, microsecond=0)

    email = 'thomas@example.com'
    name = 'A the A-er'
    lti_id = 'USER_ID'
    source_id = ''
    published = 'false'
    username = 'a-the-a-er'
    due = None
    with app.app_context():
        due_date = due or due_at.isoformat() + 'Z'
        data = {
            'custom_canvas_course_name': 'NEW_COURSE',
            'custom_canvas_course_id': 'MY_COURSE_ID',
            'custom_canvas_assignment_id': 'MY_ASSIG_ID',
            'custom_canvas_assignment_title': 'MY_ASSIG_TITLE',
            'roles': 'instructor',
            'custom_canvas_user_login_id': username,
            'custom_canvas_course_title': 'Common Lisp',
            'custom_canvas_assignment_due_at': due_date,
            'custom_canvas_assignment_published': published,
            'user_id': lti_id,
            'lis_person_contact_email_primary': email,
            'lis_person_name_full': name,
            'context_id': 'NO_CONTEXT',
            'context_title': 'WRONG_TITLE',
            'oauth_consumer_key': 'my_lti',
            'lis_outcome_service_url': source_id,
        }
        if source_id:
            data['lis_result_sourcedid'] = source_id
        res = test_client.post('/api/v1/lti/launch/1', data=data)

        url = urllib.parse.urlparse(res.headers['Location'])
        jwt = urllib.parse.parse_qs(url.query)['jwt'][0]
        lti_res = test_client.req(
            'get',
            '/api/v1/lti/launch/2',
            400,
            headers={'Jwt': 'INVALID_JWT'},
            result=error_template
        )

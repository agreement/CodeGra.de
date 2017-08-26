import urllib
import datetime

import pytz
import pytest
import dateutil.parser

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
                'lis_person_sourcedid': username,
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


def test_lti_no_course_roles(test_client, app, logged_in, ta_user):
    due_at = datetime.datetime.utcnow() + datetime.timedelta(days=1)

    def do_lti_launch(
        username='A the A-er',
        lti_id='USER_ID',
        source_id='',
        published='false'
    ):
        with app.app_context():
            data = {
                'custom_canvas_course_name': 'NEW_COURSE',
                'custom_canvas_course_id': 'MY_COURSE_ID',
                'custom_canvas_assignment_id': 'MY_ASSIG_ID',
                'custom_canvas_assignment_title': 'MY_ASSIG_TITLE',
                'roles': 'administrator,non_existing',
                'lis_person_sourcedid': username,
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

    def get_user_info(token):
        with app.app_context():
            return test_client.req(
                'get',
                '/api/v1/login',
                200,
                headers={'Authorization': f'Bearer {token}'} if token else {}
            )

    _, token = do_lti_launch()
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    old_id = out['id']

    _, token = do_lti_launch()
    out = get_user_info(token)
    assert out['name'] == 'A the A-er'
    assert out['id'] == old_id

    user = m.User.query.filter_by(name=out['name']).one()
    assert user.role.name == 'Admin'
    assert len(user.courses) == 1
    assert list(user.courses.values())[0].name == 'non_existing'

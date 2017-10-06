import os
import sys
import json

import pytest

import psef.auth as a
import psef.models as m
from psef.errors import APICodes, APIException

should_raise = pytest.mark.should_raise


@pytest.mark.parametrize(
    'perm,vals',
    [
        # name, (bs_course (is ta), pse_course (is student), prolog (nothing))
        ('can_submit_own_work', (False, True, False)),
        ('can_see_others_work', (True, False, False)),
        ('can_see_assignments', (True, True, False)),
        should_raise(('add_user', (False, False, False)),
                     )  # This is not a real permission
    ]
)
def test_course_permissions(
    ta_user, bs_course, pse_course, prolog_course, perm, vals, logged_in,
    test_client, request, error_template
):
    should_r = request.node.get_marker('should_raise')
    if should_r:
        error = 404
    else:
        error = False

    with logged_in(ta_user):
        for course, val in zip([bs_course, pse_course, prolog_course], vals):
            if should_r:
                with pytest.raises(KeyError):
                    res = ta_user.has_permission(perm, course_id=course.id)
                    print('er', res)
            else:
                assert ta_user.has_permission(perm, course_id=course.id) == val
            test_client.req(
                'get',
                '/api/v1/permissions/',
                error or 200,
                query={'course_id': course.id,
                       'permission': perm},
                result=error_template if error else val,
            )

            if not error:
                if val:
                    a.ensure_permission(perm, course_id=course.id)
                else:
                    with pytest.raises(APIException) as err:
                        a.ensure_permission(perm, course_id=course.id)
                    assert err.value.api_code == APICodes.INCORRECT_PERMISSION

    if not error:
        for course, val in zip([bs_course, pse_course, prolog_course], vals):
            with pytest.raises(APIException) as err:
                a.ensure_permission(perm, course_id=course.id)
            assert err.value.api_code == APICodes.NOT_LOGGED_IN


@pytest.mark.parametrize('perm', ['wow_nope'])
def test_non_existing_permission(
    ta_user, bs_course, perm, logged_in, test_client
):
    with pytest.raises(KeyError):
        ta_user.has_permission(perm)
    with pytest.raises(KeyError):
        ta_user.has_permission(perm, course_id=bs_course.id)

    with logged_in(ta_user):
        test_client.req(
            'get',
            '/api/v1/permissions/',
            404,
            query={'course_id': bs_course.id,
                   'permission': perm}
        )
        test_client.req(
            'get', f'/api/v1/permissions/', 404, query={'permission': perm}
        )


@pytest.mark.parametrize('perm', ['can_grade_work', 'can_submit_own_work'])
def test_non_existing_course(ta_user, bs_course, perm):
    assert not ta_user.has_permission(perm, course_id=bs_course.id * 10)


@pytest.mark.parametrize(
    'perm,vals',
    [('can_edit_own_info', (True, True)), ('can_add_users', (False, True))],
)
def test_role_permissions(
    ta_user, admin_user, perm, vals, logged_in, test_client
):
    for user, val in zip([ta_user, admin_user], vals):
        print(user.has_permission(perm))
        with logged_in(user):
            query = {'permission': perm}
            test_client.req(
                'get', '/api/v1/permissions/', 200, query=query, result=val
            )
            if val:
                a.ensure_permission(perm, course_id=None)
            else:
                with pytest.raises(APIException) as err:
                    a.ensure_permission(perm, course_id=None)
                assert err.value.api_code == APICodes.INCORRECT_PERMISSION

    with pytest.raises(APIException) as err:
        a.ensure_permission(perm)
    assert err.value.api_code == APICodes.NOT_LOGGED_IN


def test_all_permissions(
    ta_user, bs_course, pse_course, prolog_course, admin_user, student_user,
    logged_in, test_client
):
    for user in [ta_user, admin_user, student_user]:
        with logged_in(user):
            for course in [bs_course, pse_course, prolog_course, None]:
                query = {} if course is None else {'course_id': course.id}
                res = test_client.req(
                    'get', '/api/v1/permissions/', 200, query=query
                )
                for perm, val in res.items():
                    assert val == user.has_permission(perm, course)

    rv = test_client.get('/api/v1/permissions/')
    assert rv.status_code == 401

    with logged_in(ta_user):
        test_client.req(
            'get',
            '/api/v1/permissions/',
            400,
            query={'course_id': 'a'},
        )


@pytest.mark.parametrize(
    'permission',
    ['can_manage_course', 'can_see_assignments', 'can_grade_work']
)
@pytest.mark.parametrize(
    'named_user', ['Thomas Schaper', 'Stupid1', 'admin'],
    indirect=['named_user']
)
def test_get_all_permissions(
    named_user, logged_in, test_client, permission, error_template
):
    with logged_in(named_user):
        course_perms = test_client.req(
            'get',
            f'/api/v1/permissions/',
            200,
            query={'course_id': 'all',
                   'permission': permission}
        )
        assert len(course_perms) == len(named_user.courses)
        print([(c, cr.name, cr.id) for c, cr in named_user.courses.items()])
        for course_id, has in course_perms.items():
            assert has == named_user.has_permission(permission, int(course_id))

        course_perms = test_client.req(
            'get',
            f'/api/v1/permissions/',
            400,
            query={'course_id': 'all'},
            result=error_template
        )

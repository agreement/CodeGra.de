import json

import pytest

import psef
import psef.models as m
from psef.errors import APICodes

perm_error = pytest.mark.perm_error


@pytest.mark.parametrize(
    'named_user', [
        ('Thomas Schaper'),
        ('Stupid1'),
        ('admin'),
        perm_error(error=403)('nobody'),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=True
)
def test_simple_add_delete(
    named_user, logged_in, test_client, request, error_template
):
    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        snips = []
        for i in range(2):
            snip = {
                'value': f'My snippet value{i}',
                'key': f'My snippet key{i}',
            }
            snips.append(snip)
            test_client.req(
                'put',
                '/api/v1/snippet',
                error or 201,
                data=snip,
                result=error_template if error else {
                    'id': int,
                    **snip,
                }
            )
        res = test_client.req('get', '/api/v1/snippets/', error or 200,
                              result=error_template if error else [
                                  {'id': int, **snip} for snip in snips
                              ],)
        if not error:
            for snip in res:
                test_client.req(
                    'delete', f'/api/v1/snippets/{snip["id"]}', 204
                )
            res = test_client.req('get', '/api/v1/snippets/', 200, result=[])


@pytest.mark.parametrize(
    'named_user', [
        ('Thomas Schaper'),
        ('Stupid1'),
        ('admin'),
        perm_error(error=403)('nobody'),
        perm_error(error=401)('NOT_LOGGED_IN'),
    ],
    indirect=True
)
def test_simple_update(
    named_user, logged_in, test_client, error_template, request
):
    perm_err = request.node.get_marker('perm_error')
    if perm_err:
        error = perm_err.kwargs['error']
    else:
        error = False

    with logged_in(named_user):
        snips = []
        for i in range(2):
            snip = {
                'value': f'My snippet value{i}',
                'key': f'My snippet key{i}',
            }
            snips.append(snip)
            test_client.req(
                'put',
                '/api/v1/snippet',
                error or 201,
                data=snip,
                result=error_template if error else {
                    'id': int,
                    **snip,
                }
            )
        snips = test_client.req(
            'get',
            '/api/v1/snippets/',
            error or 200,
            result=error_template if error else [
                {'id': int, **snip} for snip in snips
            ],
        )
        if not error:
            snips[0]['value'] = 'dag dag'
            test_client.req(
                'put',
                '/api/v1/snippet',
                201,
                data={
                    'value': snips[0]['value'],
                    'key': snips[0]['key'],
                },
                result=snips[0],
            )
        # Make sure the id has not changed.
        test_client.req(
            'get',
            '/api/v1/snippets/',
            error or 200,
            result=error_template if error else snips
        )


@pytest.mark.parametrize(
    'named_user', [
        ('Thomas Schaper'),
        ('Stupid1'),
        ('admin'),
    ],
    indirect=True
)
def test_full_update(named_user, logged_in, test_client):
    with logged_in(named_user):
        snips = []
        for i in range(2):
            snip = {
                'value': f'My snippet value{i}',
                'key': f'My snippet key{i}',
            }
            snips.append(snip)
            test_client.req(
                'put',
                '/api/v1/snippet',
                201,
                data=snip,
                result={
                    'id': int,
                    **snip,
                }
            )
        snips = test_client.req('get', '/api/v1/snippets/', 200, result=[
            {'id': int, **snip} for snip in snips
        ])
        snips[0]['value'] = 'dag dag'
        snips[0]['key'] = 'hello hello'
        test_client.req(
            'patch',
            f'/api/v1/snippets/{snips[0]["id"]}',
            status_code=204,
            data={
                'value': snips[0]['value'],
                'key': snips[0]['key'],
            },
        )
        test_client.req('get', '/api/v1/snippets/', 200, result=[
            {'id': int, **snip} for snip in snips
        ])


@pytest.mark.parametrize(
    'named_user', [
        ('Devin Hillenius'),
        ('Stupid1'),
        ('admin'),
    ],
    indirect=True
)
def test_modify_others_snippet(named_user, ta_user, test_client, logged_in):
    with logged_in(named_user):
        snip = {'key': 'k', 'value': 'v'}
        snip = test_client.req(
            'put',
            '/api/v1/snippet',
            201,
            data=snip,
            result={
                'id': int,
                **snip,
            },
        )

    with logged_in(ta_user):
        test_client.req(
            'delete',
            f'/api/v1/snippets/{snip["id"]}',
            403,
            result={
                'message': str,
                'description': str,
                'code': APICodes.INCORRECT_PERMISSION.name,
            }
        )
        test_client.req(
            'patch',
            f'/api/v1/snippets/{snip["id"]}',
            403,
            data=snip,
            result={
                'message': str,
                'description': str,
                'code': APICodes.INCORRECT_PERMISSION.name,
            }
        )

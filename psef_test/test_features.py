import pytest

import psef.models as m


@pytest.mark.parametrize(
    'features', [{
        'BLACKBOARD': 5,
        'WOWSERS!': True,
        'OFF': False,
    }, None]
)
def test_about_features(test_client, app, features, monkeypatch):
    if features is not None:
        monkeypatch.setitem(app.config, 'FEATURES', features)
    test_client.req(
        'get',
        '/api/v1/about',
        200,
        result={
            'version': app.config['_VERSION'],
            'features': {
                k: bool(v)
                for k, v in app.config['FEATURES'].items()
            }
        }
    )


def test_disable_features(
    test_client, logged_in, ta_user, monkeypatch, app, error_template
):
    monkeypatch.setitem(app.config['FEATURES'], 'BLACKBOARD_ZIP_UPLOAD', False)
    with logged_in(ta_user):
        res = test_client.req(
            'post',
            '/api/v1/assignments/5/submissions/',
            400,
            result=error_template
        )
        assert 'feature is not enabled' in res['message']

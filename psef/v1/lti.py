import typing as t
import urllib
import datetime
import traceback

import jwt
import flask

import psef.errors as errors
import psef.models as models
import psef.helpers as helpers
from psef import app
from psef.lti import CanvasLTI
from psef.models import db

from . import api


@api.route('/lti/launch/1', methods=['POST'])
@helpers.feature_required('LTI')
def launch_lti() -> t.Any:
    """Do a LTI launch.

    .. :quickref: LTI; Do a LTI Launch.
    """
    lti = {
        'params': CanvasLTI.create_from_request(flask.request).launch_params,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
    }
    return flask.redirect(
        '{}/lti_launch/?inLTI=true&jwt={}'.format(
            app.config['EXTERNAL_URL'],
            urllib.parse.quote(
                jwt.encode(
                    lti,
                    app.config['LTI_SECRET_KEY'],
                    algorithm='HS512',
                ).decode('utf8')
            )
        )
    )


@api.route('/lti/launch/2', methods=['GET'])
@helpers.feature_required('LTI')
def second_phase_lti_launch(
) -> helpers.JSONResponse[t.Mapping[str, t.Union[str, models.Assignment, bool]]
                          ]:
    try:
        launch_params = jwt.decode(
            flask.request.headers.get('Jwt', None),
            app.config['LTI_SECRET_KEY'],
            algorithm='HS512'
        )['params']
    except jwt.DecodeError:
        traceback.print_exc()
        raise errors.APIException(
            (
                'Decoding given JWT token failed, LTI is probably '
                'not configured right. Please contact your site admin.'
            ),
            f'The decoding of "{flask.request.headers.get("Jwt")}" failed.',
            errors.APICodes.INVALID_PARAM,
            400,
        )
    lti = CanvasLTI(launch_params)

    user, new_token, updated_email = lti.ensure_lti_user()
    course = lti.get_course()
    assig = lti.get_assignment(user)
    lti.set_user_role(user)
    new_role_created = lti.set_user_course_role(user, course)
    db.session.commit()

    result: t.Mapping[str, t.Union[str, models.Assignment, bool]]
    result = {
        'assignment': assig,
        'new_role_created': new_role_created,
    }
    if new_token is not None:
        result['access_token'] = new_token
    if updated_email:
        result['updated_email'] = updated_email

    return helpers.jsonify(result)

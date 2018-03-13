"""
This module defines all API routes with the main directory "about". Thus
the APIs in this module are mostly used get information about the instance
running psef.

:license: AGPLv3, see LICENSE for details.
"""
import typing as t

import psef
from psef.helpers import JSONResponse, jsonify

from . import api


@api.route('/about', methods=['GET'])
def about(
) -> JSONResponse[t.Mapping[str, t.Union[str, t.Mapping[str, bool]]]]:
    """Get the version and features of the currently running instance.

    .. :quickref: About; Get the version and features.

    :>json string version: The version of the running instance.
    :>json object features: A mapping from string to a boolean for every
        feature indicating if the current instance has it enabled.

    :returns: The mapping as described above.
    """
    features = {
        key: bool(value)
        for key, value in psef.app.config['FEATURES'].items()
    }
    return jsonify(
        {
            'version': psef.app.config['_VERSION'],
            'features': features,
        },
    )

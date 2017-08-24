"""
This module defines all API routes with the main directory "about". Thus
the APIs in this module are mostly used get information about the instance
running psef.

:license: AGPLv3, see LICENSE for details.
"""
import typing as t

from flask import request

import psef
from psef.helpers import (
    JSONType, JSONResponse, EmptyResponse, jsonify, ensure_json_dict,
    ensure_keys_in_dict, make_empty_response
)

from . import api


@api.route('/about', methods=['GET'])
def about(
) -> JSONResponse[t.Mapping[str, t.Union[str, t.Mapping[str, bool]]]]:
    features = {
        key: bool(value)
        for key, value in psef.app.config['FEATURES'].items()
    }
    return jsonify(
        {
            'version': psef.app.config['VERSION'],
            'features': features,
        },
    )

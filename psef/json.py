#!/usr/bin/env python3

import json

from psef import app


class _CustomJSONEncoder(json.JSONEncoder):
    """This JSON encoder is used to enable the JSON serialization of custom
    classes.

    Classes can define their serialization by implementing a __to_json__
    method.
    """
    def default(self, obj):
        try:
            return obj.__to_json__()
        except AttributeError:
            return super().default(obj)


app.json_encoder = _CustomJSONEncoder

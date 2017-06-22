#!/usr/bin/env python3

import json

from psef import app


class _CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return obj.__to_json__()
        except AttributeError:
            return super().default(obj)


app.json_encoder = _CustomJSONEncoder

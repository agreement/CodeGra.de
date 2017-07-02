#!/usr/bin/env python3

import json

from psef import app


class CustomJSONEncoder(json.JSONEncoder):
    """This JSON encoder is used to enable the JSON serialization of custom
    classes.

    Classes can define their serialization by implementing a `__to_json__`
    method.
    """
    def default(self, obj):
        """A way to serialize arbitrary methods to JSON.

        Classes can use this method by implementing a `__to_json__` method that
        should return a JSON serializable object.

        :param object obj: The object that should be converted to JSON.
        """
        try:
            return obj.__to_json__()
        except AttributeError:
            return super().default(obj)


app.json_encoder = CustomJSONEncoder

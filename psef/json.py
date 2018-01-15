#!/usr/bin/env python3

import typing as t
from json import JSONEncoder


class CustomJSONEncoder(JSONEncoder):
    """This JSON encoder is used to enable the JSON serialization of custom
    classes.

    Classes can define their serialization by implementing a `__to_json__`
    method.
    """

    def default(self, obj: t.Any) -> t.Any:
        """A way to serialize arbitrary methods to JSON.

        Classes can use this method by implementing a `__to_json__` method that
        should return a JSON serializable object.

        :param object obj: The object that should be converted to JSON.
        """
        try:
            return obj.__to_json__()
        except AttributeError:  # pragma: no cover
            return super().default(obj)


def get_extended_encoder_class(
    use_extended: t.Callable[[object], bool],
) -> t.Type:
    """Get a json encoder class.

    :param use_extended: The returned class only uses the
        ``__extended_to_json__`` method if this callback returns something that
        is equal to ``True``. This method is called with a single argument that
        is the object that is currently encoded.
    :returns: A class (not a instance!) that can be used as ``JSONEncoder``
        class.
    """

    class CustomExtendedJSONEncoder(JSONEncoder):
        """This JSON encoder is used to enable the JSON serialization of custom
        classes.

        Classes can define their serialization by implementing a
        `__extended_to_json__` or a `__to_json__` method. This class first
        tries the extended method and if it does not exist it tries to normal
        one.
        """

        def default(self, obj: t.Any) -> t.Any:
            """A way to serialize arbitrary methods to JSON.

            Classes can use this method by implementing a `__to_json__` method
            that should return a JSON serializable object.

            :param object obj: The object that should be converted to JSON.
            """
            if hasattr(obj, '__extended_to_json__') and use_extended(obj):
                try:
                    return obj.__extended_to_json__()
                except AttributeError:  # pragma: no cover
                    pass

            try:
                return obj.__to_json__()
            except AttributeError:  # pragma: no cover
                return super().default(obj)

    return CustomExtendedJSONEncoder


def init_app(app: t.Any) -> None:
    app.json_encoder = CustomJSONEncoder

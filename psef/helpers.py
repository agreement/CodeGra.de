"""
This module implements generic helpers and convenience functions.

:license: AGPLv3, see LICENSE for details.
"""
import abc
import enum
import typing as t
import datetime
import operator
from functools import wraps, reduce

import flask  # type: ignore
import werkzeug

import psef
import psef.json as json
import psef.errors
import psef.models
from typing_extensions import NoReturn, Protocol

#: Type vars
T = t.TypeVar('T')
Z = t.TypeVar('Z', bound='Comparable')
Y = t.TypeVar('Y', bound='psef.models.Base')
InstanceType = t.Union[t.Type, t.Tuple[t.Type, ...]]


class Comparable(Protocol):  # pragma: no cover
    """A protocol that for comparable variables.

    To satisfy this protocol a object should implement the ``__eq__``,
    ``__lt__``, ``__gt__``, ``__le__`` and``__ge__`` magic functions.
    """

    @abc.abstractmethod
    def __eq__(self, other: t.Any) -> bool:
        ...

    @abc.abstractmethod
    def __lt__(self: Z, other: Z) -> bool:
        ...

    def __gt__(self: Z, other: Z) -> bool:
        return (not self < other) and self != other

    def __le__(self: Z, other: Z) -> bool:
        return self < other or self == other

    def __ge__(self: Z, other: Z) -> bool:
        return (not self < other)


def get_all_subclasses(cls: t.Type[T]) -> t.Iterable[t.Type['T']]:
    """Returns all subclasses of the given class.

    Stolen from:
    https://stackoverflow.com/questions/3862310/how-can-i-find-all-subclasses-of-a-class-given-its-name

    :param cls: The parent class
    :returns: A list of all subclasses
    """
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def between(min_bound: Z, item: Z, max_bound: Z) -> Z:
    """Make sure ``item`` is between two bounds.

    >>> between(0, 5, 10)
    5
    >>> between(0, -1, 10)
    0
    >>> between(0, 11, 10)
    10
    >>> between(10, 5, 0)
    Traceback (most recent call last):
    ...
    ValueError: `min_bound` cannot be higher than `max_bound`

    .. note::

        ``min_bound`` cannot be larger than ``max_bound``. They can be equal.

    :param min_bound: The minimum this function should return
    :param max_bound: The maximum this function should return
    :param item: The item to check
    :returns: ``item`` if it is between ``min_bound`` and ``max_bound``,
        otherwise the bound is returned that is closest to the item.
    """
    if min_bound > max_bound:
        raise ValueError('`min_bound` cannot be higher than `max_bound`')

    if item <= min_bound:
        return min_bound
    elif item >= max_bound:
        return max_bound

    return item


def get_request_start_time() -> datetime.datetime:
    """Return the start time of the current request.

    :returns: The time as returned by the python time module.
    :rtype: float
    """
    return flask.g.request_start_time


_JSONValue = t.Union[str, int, float, bool, None, t.Dict[str, t.Any],
                     t.List[t.Any]]
JSONType = t.Union[t.Dict[str, _JSONValue], t.List[_JSONValue], _JSONValue]


class ExtendedJSONResponse(t.Generic[T]):
    """A datatype for a JSON response created by using the
    ``__extended_to_json__`` if available.

    This is a subtype of :py:class:`werkzeug.wrappers.Response` where the body
    is a valid JSON object and ``content-type`` is ``application/json``.

    .. warning::

        This class is only used for type hinting and is never actually used! It
        does not contain any valid data!
    """

    def __init__(self) -> None:  # pragma: no cover
        raise NotImplementedError("Do not use this class as actual data")


class JSONResponse(t.Generic[T]):
    """A datatype for a JSON response.

    This is a subtype of :py:class:`werkzeug.wrappers.Response` where the body
    is a valid JSON object and ``content-type`` is ``application/json``.

    .. warning::

        This class is only used for type hinting and is never actually used! It
        does not contain any valid data!
    """

    def __init__(self) -> None:  # pragma: no cover
        raise NotImplementedError("Do not use this class as actual data")


class EmptyResponse:
    """An empty response.

    This is a subtype of :py:class:`werkzeug.wrappers.Response` where the body
    is empty and the status code is always 204.

    .. warning::

        This class is only used for type hinting and is never actually used! It
        does not contain any valid data!
    """

    def __init__(self) -> None:  # pragma: no cover
        raise NotImplementedError("Do not use this class as actual data")


def _filter_or_404(model: t.Type[Y], get_all: bool,
                   criteria: t.Tuple) -> t.Union[Y, t.Sequence[Y]]:
    """Get the specified object by filtering or raise an exception.

    :param get_all: Get all objects if ``True`` else get a single one.
    :param model: The object to get.
    :param criteria: The criteria to filter with.
    :returns: The requested object.

    :raises APIException: If no object with the given id could be found.
        (OBJECT_ID_NOT_FOUND)
    """
    crit_str = ' AND '.join(str(crit) for crit in criteria)
    query = model.query.filter(*criteria)  # type: ignore
    obj = query.all() if get_all else query.one_or_none()
    if not obj:
        raise psef.errors.APIException(
            f'The requested {model.__name__.lower()} was not found',
            f'There is no "{model.__name__}" when filtering with {crit_str}',
            psef.errors.APICodes.OBJECT_ID_NOT_FOUND, 404
        )
    return obj


def filter_all_or_404(model: t.Type[Y], *criteria: t.Any) -> t.Sequence[Y]:
    """Get all objects of the specified model filtered by the specified
    criteria.

    .. note::
        ``Y`` is bound to :py:class:`psef.models.Base`, so it should be a
        SQLAlchemy model.

    :param model: The object to get.
    :param criteria: The criteria to filter with.
    :returns: The requested objects.

    :raises APIException: If no object with the given id could be found.
        (OBJECT_ID_NOT_FOUND)
    """
    return t.cast(t.Sequence[Y], _filter_or_404(model, True, criteria))


def filter_single_or_404(model: t.Type[Y], *criteria: t.Any) -> Y:
    """Get a single object of the specified model by filtering or raise an
    exception.

    .. note::
        ``Y`` is bound to :py:class:`psef.models.Base`, so it should be a
        SQLAlchemy model.

    :param model: The object to get.
    :param criteria: The criteria to filter with.
    :returns: The requested object.

    :raises APIException: If no object with the given id could be found.
        (OBJECT_ID_NOT_FOUND)
    """
    return t.cast(Y, _filter_or_404(model, False, criteria))


def get_or_404(model: t.Type[Y], object_id: t.Any) -> Y:
    """Get the specified object by primary key or raise an exception.

    .. note::
        ``Y`` is bound to :py:class:`psef.models.Base`, so it should be a
        SQLAlchemy model.

    :param model: The object to get.
    :param object_id: The primary key identifier for the given object.
    :returns: The requested object.

    :raises APIException: If no object with the given id could be found.
        (OBJECT_ID_NOT_FOUND)
    """
    obj: t.Optional[Y] = model.query.get(object_id)
    if obj is None:
        raise psef.errors.APIException(
            f'The requested "{model.__name__}" was not found',
            f'There is no "{model.__name__}" with primary key {object_id}',
            psef.errors.APICodes.OBJECT_ID_NOT_FOUND, 404
        )
    return obj


def ensure_keys_in_dict(
    mapping: t.Mapping[T, t.Any], keys: t.Sequence[t.Tuple[T, InstanceType]]
) -> None:
    """Ensure that the given keys are in the given mapping.

    :param mapping: The mapping to check.
    :param keys: The keys that should be in the mapping. If key is a tuple it
        is of the form (key, type) where ``mappping[key]`` has to be of type
        ``type``.
    :return: Nothing.

    :raises psef.errors.APIException: If a key from ``keys`` is missing in
        ``mapping`` (MISSING_REQUIRED_PARAM)
    """

    def _get_type_name(t: t.Union[t.Type, t.Tuple[t.Type, ...]]) -> str:
        if isinstance(t, tuple):
            return ', '.join(ty.__name__ for ty in t)
        else:
            return t.__name__

    missing: t.List[t.Union[T, str]] = []
    type_wrong = False
    for key, check_type in keys:
        if key not in mapping:
            missing.append(key)
        elif (not isinstance(mapping[key], check_type)
              ) or (check_type == int and isinstance(mapping[key], bool)):
            missing.append(
                f'{str(key)} was of wrong type'
                f' (should be a "{_get_type_name(check_type)}"'
                f', was a "{type(mapping[key]).__name__}")'
            )
            type_wrong = True
    if missing:
        msg = 'The given object does not contain all required keys'
        key_type = ', '.join(
            f"\'{k[0]}\': {_get_type_name(k[1])}" for k in keys
        )
        raise psef.errors.APIException(
            msg + (' or the type was wrong' if type_wrong else ''),
            '"{}" is missing required keys "{}" of all required keys "{}{}{}"'.
            format(
                mapping, ', '.join(str(m) for m in missing), '{', key_type, '}'
            ), psef.errors.APICodes.MISSING_REQUIRED_PARAM, 400
        )


def ensure_json_dict(json: JSONType) -> t.Dict[str, JSONType]:
    """Make sure that the given json is a JSON dictionary

    :param json: The input json that should be checked.
    :returns: Exactly the same JSON if it is in fact a dictionary.

    :raises psef.errors.APIException: If the given JSON is not a dictionary.
        (INVALID_PARAM)
    """
    if isinstance(json, t.Dict):
        return json
    raise psef.errors.APIException(
        'The given JSON is not a object as is required',
        f'"{json}" is not a object', psef.errors.APICodes.INVALID_PARAM, 400
    )


def _maybe_add_warning(
    response: flask.Response,
    warning: t.Optional[psef.errors.HttpWarning],
) -> None:
    if warning is not None:
        response.headers['Warning'] = warning


def extended_jsonify(
    obj: T,
    status_code: int = 200,
    warning: t.Optional[psef.errors.HttpWarning] = None,
) -> ExtendedJSONResponse[T]:
    """Create a response with the given object ``obj`` as json payload.

    This function differs from :py:func:`jsonify` by that it used the
    ``__extended_to_json__`` magic function if it is available.

    :param obj: The object that will be jsonified using
        :py:class:`~.psef.json.CustomExtendedJSONEncoder`
    :param statuscode: The status code of the response
    :param warning: The warning that should be added to the response
    :returns: The response with the jsonified object as payload
    """
    try:
        psef.app.json_encoder = json.CustomExtendedJSONEncoder
        response = flask.make_response(flask.jsonify(obj))
    finally:
        psef.app.json_encoder = json.CustomJSONEncoder
    response.status_code = status_code

    _maybe_add_warning(response, warning)

    return response


def jsonify(
    obj: T,
    status_code: int = 200,
    warning: t.Optional[psef.errors.HttpWarning] = None,
) -> JSONResponse[T]:
    """Create a response with the given object ``obj`` as json payload.

    :param obj: The object that will be jsonified using
        :py:class:`~.psef.json.CustomJSONEncoder`
    :param statuscode: The status code of the response
    :param warning: The warning that should be added to the response
    :returns: The response with the jsonified object as payload
    """
    response = flask.make_response(flask.jsonify(obj))
    response.status_code = status_code

    _maybe_add_warning(response, warning)

    return response


def make_empty_response(
    warning: t.Optional[psef.errors.HttpWarning] = None,
) -> EmptyResponse:
    """Create an empty response.

    :param warning: The warning that should be added to the response
    :returns: A empty response with status code 204
    """
    response = flask.make_response('')
    response.status_code = 204

    _maybe_add_warning(response, warning)

    return response


def feature_required(feature_name: str) -> t.Callable:
    """ A decorator used to make sure the function decorated is only called
    with a certain feature enabled.

    :param feature_name: The name of the feature to check for.

    :returns: The value of the decorated function if the given feature is
        enabled.

    :raises APIException: If the feature is not enabled. (DISABLED_FEATURE)
    """

    def decorator(f: t.Callable) -> t.Callable:
        @wraps(f)
        def decorated_function(*args: t.Any, **kwargs: t.Any) -> t.Any:
            enabled = psef.app.config['FEATURES'][feature_name]
            if enabled:
                return f(*args, **kwargs)
            else:
                raise psef.errors.APIException(
                    'This feature is not enabled for this instance.',
                    f'The feature "{feature_name}" is not enabled.',
                    psef.errors.APICodes.DISABLED_FEATURE, 400
                )

        return decorated_function

    return decorator


class NotGiven(enum.Enum):
    _token: int = 0


_empty = NotGiven._token

_DictItem = t.Tuple[t.Union[str, t.Tuple[str, str]], InstanceType]


def with_items_in_request(
    required: t.Sequence[_DictItem],
    optional_pairs: t.Sequence[t.Sequence[_DictItem]] = None,
    get_source: t.Optional[t.Callable[[], t.Dict[str, JSONType]]] = None,
) -> t.Callable[[T], T]:
    def get_source_name(orig: t.Union[str, t.Tuple[str, str]]) -> str:
        if isinstance(orig, tuple):
            return orig[0]
        else:
            return orig

    def get_function_name(orig: t.Union[str, t.Tuple[str, str]]) -> str:
        if isinstance(orig, tuple):
            return orig[1]
        else:
            return orig

    if optional_pairs is None:
        optional_pairs = []

    required_set = set(get_source_name(name) for name, _ in required)
    for optional in optional_pairs:
        for name, _ in optional:
            if get_source_name(name) in required_set:
                raise ValueError(
                    f'The param "{name}" cannot be optional and required'
                )

    def raise_mypy_err(check_type: InstanceType, annot_t: t.Any) -> NoReturn:
        raise ValueError(
            f'The types to check on ("{check_type}") is not the '
            f'is not the same as the annotations ("{annot_t}")'
        )

    def check_items(
        annots: t.Dict[str, t.Any],
        items: t.Iterable[_DictItem],
    ) -> None:
        for _n, check_type in items:
            name = get_function_name(_n)

            if name not in annots:
                raise ValueError(
                    f'The required option "{name}" is not a '
                    'param to the given function.'
                )

            annot_t = annots[name]

            if isinstance(check_type, tuple):
                if not isinstance(annot_t, type(t.Union)):
                    raise ValueError(
                        f'The argument "{name}" is checked for multiple types '
                        'but can be a single type according to annotations'
                    )

                if t.Union[(check_type)] != annot_t:
                    raise_mypy_err(check_type, annot_t)
            elif annot_t != check_type:
                raise_mypy_err(check_type, annot_t)

    def ensure_and_copy(
        res: t.Dict[str, t.Any],
        vals: t.Dict[str, t.Any],
        required: t.Sequence[_DictItem],
    ) -> None:
        ensure_keys_in_dict(
            vals,
            [(get_source_name(k), v) for k, v in required]
        )
        for k, _ in required:
            res[get_function_name(k)] = vals[get_source_name(k)]

    def decorator(f: T) -> T:
        check_items(f.__annotations__, required)
        for optional in optional_pairs:
            opts = (
                (
                    name,
                    (NotGiven, ) + types
                    if isinstance(types, tuple) else tuple(
                        (NotGiven, types),
                    ),
                ) for name, types in optional
            )
            check_items(
                f.__annotations__,
                opts,
            )

        @wraps(t.cast(t.Any, f))
        def decorated_function(*args: t.Any, **kwargs: t.Any) -> T:
            if get_source is None:
                source = ensure_json_dict(flask.request.get_json())
            else:
                source = get_source()

            ensure_and_copy(kwargs, source, required)

            for optional in optional_pairs:
                if any(name in source for name, _ in optional):
                    ensure_and_copy(kwargs, source, optional)
                else:
                    updated = {
                        get_function_name(name): _empty
                        for name, _ in optional
                    }
                    kwargs.update(updated)

            return t.cast(t.Callable, f)(*args, **kwargs)

        return t.cast(T, decorated_function)

    return decorator

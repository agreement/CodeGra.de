"""
This module implements parsers that raise a `APIException` when they fail.

:license: AGPLv3, see LICENSE for details.
"""
import enum
import typing as t
import datetime

import dateutil

from psef.errors import APICodes, APIException

T = t.TypeVar('T', bound=enum.Enum)


def parse_datetime(to_parse: str) -> datetime.datetime:
    """Parse a datetime string using dateutil.

    :param to_parse: The string to parse.
    :returns: The parsed datetime object.
    :raises APIException: If the parsing fails for whatever reason.
    """
    try:
        return dateutil.parser.parse(to_parse)
    except (ValueError, OverflowError):
        raise APIException(
            'The given date is not valid!',
            '{} cannot be parsed by dateutil.'.format(to_parse),
            APICodes.INVALID_PARAM, 400
        )


def parse_enum(to_parse: str, enum: t.Type[T]) -> T:
    """Parse the given string to the given enum.

    :param to_parse: The string to parse.
    :param enum: The enum to parse to.
    :returns: A instance of the given enum.
    :raises APIException: If the parsing fails in some way.
    """
    try:
        return enum[to_parse]
    except KeyError:
        raise APIException(
            f'The given value is not a valid item in {enum.__name__}.',
            f'{to_parse} is not a member from {enum.__name__}.',
            APICodes.INVALID_PARAM, 400
        )

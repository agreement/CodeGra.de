"""
This module implements parsers that raise a `APIException` when they fail.

:license: AGPLv3, see LICENSE for details.
"""
import enum
import typing as t
import datetime
import email.utils

import dateutil
from validate_email import validate_email

from psef.errors import APICodes, APIException

T = t.TypeVar('T', bound=enum.Enum)


def init_app(_: t.Any) -> None:
    pass


def parse_datetime(
    to_parse: object,
    allow_none: bool = False,
) -> t.Optional[datetime.datetime]:
    """Parse a datetime string using dateutil.

    :param to_parse: The object to parse, if this is not a string the parsing
        will always fail.
    :param allow_none: Allow ``None`` to be passed without raising a
        exception. if ``to_parse`` is ``None`` and this option is ``True`` the
        result will be ``None``.
    :returns: The parsed datetime object.
    :raises APIException: If the parsing fails for whatever reason.
    """
    if to_parse is None and allow_none:
        return None

    if isinstance(to_parse, str):
        try:
            return dateutil.parser.parse(to_parse)
        except (ValueError, OverflowError):
            pass

    raise APIException(
        'The given date is not valid!',
        '{} cannot be parsed by dateutil.'.format(to_parse),
        APICodes.INVALID_PARAM, 400
    )


def parse_enum(
    to_parse: object,
    parse_into_enum: t.Type[T],
    allow_none: bool = False,
    option_name: t.Optional[str] = None,
) -> T:
    """Parse the given string to the given parse_into_enum.

    :param to_parse: The object to parse. If this value is not a string or
        ``None`` the function will always return a type error.
    :param parse_into_enum: The enum to parse to.
    :param allow_none: Allow ``None`` to be passed and return ``None`` if this
        is the case. If this value is ``False`` and ``None`` is passed the
        function will raise a :class:`.APIException`.
    :param option_name: The name of the option, only used in error display.
    :returns: A instance of the given enum.
    :raises APIException: If the parsing fails in some way.
    """
    if allow_none and to_parse is None:
        return None

    if isinstance(to_parse, str):
        try:
            return parse_into_enum[to_parse]
        except KeyError:
            pass

    raise APIException(
        f'The given {option_name or "option"} is not a valid option',
        f'{to_parse} is not a member from {parse_into_enum.__name__}.',
        APICodes.INVALID_PARAM, 400
    )


def parse_email_list(
    to_parse: object,
    allow_none: bool = False,
) -> t.Optional[t.List[t.Tuple[str, str]]]:
    """Parse email list into a list of emails.

    This list should be in the form of a ``address-list`` as specified in
    RFC2822.

    :param to_parse: The object to parse, it should be a :class:`str` if you
        want it to succeed.
    :param allow_none: If ``True`` we will not error if ``to_parse`` is
        ``None``.
    :returns: A list of addresses or ``None`` if ``to_parse`` is ``None`` and
        ``allow_none`` is ``True``.
    :raises APIException: If the parsing fails in some way.
    """
    if allow_none and to_parse is None:
        return None

    if isinstance(to_parse, str):
        addresses = email.utils.getaddresses([to_parse.strip()])
        if all(validate_email(email) for _, email in addresses):
            return addresses

    raise APIException(
        f'The given string of emails contains invalid items',
        f'The string "{to_parse}" contains invalid items.',
        APICodes.INVALID_PARAM, 400
    )


def try_parse_email_list(
    to_parse: object,
    allow_none: bool = False,
) -> t.Optional[str]:
    """Try parsing an email list.

    This function is basically the same as :func:`.parse_email_list` but
    this function returns ``to_parse`` stripped of unnecessary whitespaces if
    the parsing succeeded.

    :param to_parse: See :func:`.parse_email_list` for what it does.
    :param allow_none: See :func:`.parse_email_list` for what it does.
    :returns: Its input stripped of spaces if parsing succeeded.
    """
    # parse_email will always throw when to_parse is not `(type(None), str)`
    if parse_email_list(to_parse, allow_none) is None:
        return None
    else:
        return t.cast(str, to_parse).strip()

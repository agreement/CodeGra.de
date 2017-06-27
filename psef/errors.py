from enum import IntEnum, unique

from flask import jsonify

from psef import app


@unique
class APICodes(IntEnum):
    INCORRECT_PERMISSION = 0
    NOT_LOGGED_IN = 1
    OBJECT_ID_NOT_FOUND = 2
    OBJECT_WRONG_TYPE = 3
    MISSING_REQUIRED_PARAM = 4
    INVALID_PARAM = 5
    REQUEST_TOO_LARGE = 6
    LOGIN_FAILURE = 7
    INACTIVE_USER = 8
    INVALID_URL = 9
    OBJECT_NOT_FOUND = 10
    BLOCKED_ASSIGNMENT = 11
    INVALID_CREDENTIALS = 12
    INVALID_STATE = 13
    INVALID_OAUTH_REQUEST = 14


class APIException(Exception):
    """The exception to use if an API call failed.
    """

    def __init__(self, message, description, api_code, status_code, **rest):
        """
        :param str message: The user friendly message to display.
        :param str description: The description used for debugging.
        :param int api_code: The error code in the API, should be a constant
                             from this class.
        :param int status_code: The Http status code to use, should not be 2xx.
        :param rest: All the other fields to return in the JSON object.
        """
        super(APIException, self).__init__()
        self.status_code = status_code
        self.api_code = api_code
        self.description = description
        self.message = message
        self.rest = rest

    def __to_json__(self):
        "Convert this APIException instance to a dictionary."
        ret = self.rest
        ret['message'] = self.message
        ret['description'] = self.description
        ret['code'] = self.api_code
        return ret


@app.errorhandler(APIException)
def handle_api_error(error):
    """Handle the an API exception by converting the error to a JSON object.
    """
    response = jsonify(error)
    response.status_code = error.status_code
    return response

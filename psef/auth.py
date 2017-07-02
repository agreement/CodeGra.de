from functools import wraps

import flask
import oauth2
from flask_login import current_user

from psef import login_manager
from psef.errors import APICodes, APIException


class PermissionException(APIException):
    """The exception used when a permission check fails.
    """
    def __init__(self, *args, **kwargs):
        super(PermissionException, self).__init__(*args, **kwargs)


@login_manager.unauthorized_handler
def _raise_login_exception(desc='No user was logged in.'):
    raise PermissionException('You need to be logged in to do this.', desc,
                              APICodes.NOT_LOGGED_IN, 401)


def _user_active():
    """Check if there is a current user who is authenticated and active.

    :returns: True if there is an active logged in user
    :rtype: bool
    """
    return (current_user and current_user.is_authenticated and
            current_user.is_active)


def ensure_can_see_grade(work):
    """Ensure the current user can see the grade of the given work.

    :param models.Work work: The work

    :returns: Nothing
    :rtype: None

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user can not see the grade.
                                 (INCORRECT_PERMISSION)
    """
    if _user_active():
        if work.user.id != current_user.id:
            ensure_permission('can_see_others_work', work.assignment.course.id)

        if not work.assignment.is_done:
            ensure_permission('can_see_grade_before_open',
                              work.assignment.course.id)
        return
    _raise_login_exception()


def ensure_enrolled(course_id):
    """Ensure the current user is enrolled in the given course.

    :param course_id: The course id of the course.
    :type course_id: int

    :returns: Nothing
    :rtype: None

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the user is not enrolled in the given
                                 course. (INCORRECT_PERMISSION)
    """
    if _user_active():
        if course_id not in current_user.courses:
            raise PermissionException(
                'You are not enrolled in this course',
                'The user "{}" is not enrolled in course "{}"'.format(
                    current_user.id,
                    course_id), APICodes.INCORRECT_PERMISSION, 403)
        return
    _raise_login_exception()


def ensure_permission(permission_name, course_id=None):
    """Ensure that the current user is logged and has the given permission.

    :param str permission_name: The name of the permission to check for.
    :param course_id: The course id of the course that should be used for the
                      course permission, if it is None a role permission is
                      implied. If a course_id is supplied but the given
                      permission is not a course permission (but a role
                      permission) this function will **NEVER** grant the
                      permission.
    :type course_id: None or int

    :returns: Nothing
    :rtype: None

    :raises PermissionException: If there is no logged in user. (NOT_LOGGED_IN)
    :raises PermissionException: If the permission is not enabled for the
                                 current user. (INCORRECT_PERMISSION)
    """
    if _user_active():
        if current_user.has_permission(permission_name, course_id=course_id):
            return
        else:
            raise PermissionException(
                'You do not have permission to do this.',
                'The permission "{}" is not enabled for user "{}"'.format(
                    permission_name,
                    current_user.id), APICodes.INCORRECT_PERMISSION, 403)
    else:
        _raise_login_exception(
            ('The user was not logged in, ' +
             'so it did not have the permission "{}"').format(permission_name))


def permission_required(permission_name, course_id=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ensure_permission(permission_name, course_id=course_id)
            return f(*args, **kwargs)

        return decorated_function

    return decorator


permission_required.__doc__ = ensure_permission.__doc__

# The code below is copied for a large part from here:
# https://github.com/tophatmonocle/ims_lti_py


class RequestValidatorMixin(object):
    '''
    A 'mixin' for OAuth request validation.
    '''

    def __init__(self):
        super(_RequestValidatorMixin, self).__init__()

        self.oauth_server = oauth2.Server()
        signature_method = oauth2.SignatureMethod_HMAC_SHA1()
        self.oauth_server.add_signature_method(signature_method)
        self.oauth_consumer = oauth2.Consumer(self.consumer_key,
                                              self.consumer_secret)

    def is_valid_request(self,
                         request,
                         parameters={},
                         fake_method=None,
                         handle_error=True):
        '''
        Validates an OAuth request using the python-oauth2 library:
            https://github.com/simplegeo/python-oauth2
        '''

        def handle(e):
            if handle_error:
                return False
            else:
                raise e

        try:
            # Set the parameters to be what we were passed earlier
            # if we didn't get any passed to us now
            if not parameters and hasattr(self, 'params'):
                parameters = self.params

            method, url, headers, parameters = self.parse_request(
                request, parameters, fake_method)

            oauth_request = oauth2.Request.from_request(
                method, url, headers=headers, parameters=parameters)

            oauth2.Token
            self.oauth_server.verify_request(oauth_request,
                                             self.oauth_consumer, {})

        except oauth2.Error as e:
            return handle(e)
        except ValueError as e:
            return handle(e)
        # Signature was valid
        return True

    def parse_request(self, request, parameters, fake_method):
        '''
        This must be implemented for the framework you're using
        Returns a tuple: (method, url, headers, parameters)
        method is the HTTP method: (GET, POST)
        url is the full absolute URL of the request
        headers is a dictionary of any headers sent in the request
        parameters are the parameters sent from the LMS

        :param object request: The request to be parsed.
        :param dict parameters: Extra parameters for the given request.
        :param object fake_method: The fake method to be used.
        :rtype: tuple[str, str, dict[str, str], dict[str, str]]
        :returns: A tuple of, respectively, the requets method, url, headers
            and form, where the last two are a key value mapping.
        '''
        raise NotImplementedError()

    def valid_request(self, request):
        '''
        Check whether the OAuth-signed request is valid and throw error if not.
        '''
        self.is_valid_request(request, parameters={}, handle_error=False)


class _FlaskOAuthValidator(RequestValidatorMixin):
    def __init__(self, key, secret):
        self.consumer_key = key
        self.consumer_secret = secret
        super(_FlaskOAuthValidator, self).__init__()

    def parse_request(self, req, parameters=None, fake_method=None):
        '''
        Parse Flask request
        '''
        return (req.method, req.url, dict(req.headers), req.form.copy())


def ensure_valid_oauth(key,
                       secret,
                       request,
                       parser_cls=_FlaskOAuthValidator):
    """Make sure the given oauth key and secret is valid for the given request.

    :param str key: The oauth key to be used for validating.
    :param str secret: The oauth secret to be used for validating.
    :param object request: The request that should be validated.
    :param RequestValidatorMixin parser_cls: The class used to parse the given
        ``request`` it should subclass :py:class:`RequestValidatorMixin` and
        should at least override the
        :func:`RequestValidatorMixin.parse_request` method.
    """
    validator = parser_cls(key, secret)
    if not validator.is_valid_request(request):
        raise PermissionException(
            'No valid oauth request could be found.',
            'The given request is not a valid oauth request.',
            APICodes.INVALID_OAUTH_REQUEST, 400)

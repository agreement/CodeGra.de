from functools import wraps

from flask_login import current_user

from psef import login_manager
from psef.errors import APIException


def _raise_login_exception(desc='No user was logged in.'):
    raise APIException('You need to be logged in to do this.', desc,
                       APIException.NOT_LOGGED_IN, 401)


def ensure_permission(permission_name, course_id=None):
    """Ensure that the current user is logged and has the given permission.

    :param str permission_name: The name of the permission to check for.
    :param course_id: The course id of the course that should be used for the
                      course permission, if it is None a role permission is
                      implied. If a course_id is supplied but the given
                      permission is not a course permission (but a role
                      permission) this function will NEVER grant the
                      permission.
    :vartype course_id: None or int
    :rtype: None
    :raises APIException: If the permission is not enabled for the current
                          user.
    """
    if (current_user and current_user.is_authenticated and
            current_user.is_active):
        if current_user.has_permission(permission_name, course_id=course_id):
            return
        else:
            raise APIException(
                'You do not have permission to do this.',
                'The permission "{}" is not enabled for user "{}"'.format(
                    permission_name,
                    current_user.id), APIException.INCORRECT_PERMISSION, 403)
    else:
        _raise_login_exception(
            ('The user was not logged in, ' +
             'so it did not have the permission "{}"').format(permission_name))


def permission_required(permission_name, course_id=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            ensure_permission(permission_name, course_id=course_id)
            f(*args, **kwargs)

        return decorated_function

    return decorator


permission_required.__doc__ = ensure_permission.__doc__

login_manager.unauthorized_handler(_raise_login_exception)

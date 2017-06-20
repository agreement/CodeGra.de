from functools import wraps

from flask_login import current_user

import psef.models as models
from psef import login_manager
from psef.errors import APICodes, APIException


class PermissionException(APIException):
    def __init__(self, *args, **kwargs):
        super(PermissionException, self).__init__(*args, **kwargs)


@login_manager.unauthorized_handler
def _raise_login_exception(desc='No user was logged in.'):
    raise PermissionException('You need to be logged in to do this.', desc,
                              APICodes.NOT_LOGGED_IN, 401)


def _user_active():
    return (current_user and current_user.is_authenticated and
            current_user.is_active)


def ensure_can_see_grade(work):
    if _user_active():
        if work.user.id != current_user.id:
            ensure_permission('can_see_others_work', work.assignment.course.id)
        if work.assignment.state != models.AssignmentStateEnum.done:
            ensure_permission('can_see_grade_before_open',
                              work.assignment.course.id)
        return
    _raise_login_exception()


def ensure_enrolled(course_id):
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
                      permission) this function will NEVER grant the
                      permission.
    :vartype course_id: None or int
    :rtype: None
    :raises PermissionException: If the permission is not enabled for the
                                 current
                          user.
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

"""
This module defines all celery tasks. It is very important that you DO NOT
change the way parameters are used or the parameters provided in existing tasks
as there may tasks left in the old queue. Instead create a new task and change
the mapping of the variables at the bottom of this file.

:license: AGPLv3, see LICENSE for details.
"""
import typing as t
from operator import itemgetter

from celery import Celery as _Celery
from celery.utils.log import get_task_logger

import psef as p

logger = get_task_logger(__name__)  # pylint: disable=invalid-name

# pylint: disable=missing-docstring,no-self-use,pointless-statement
if t.TYPE_CHECKING:  # pragma: no cover

    class CeleryTask:
        def delay(self, *_args: t.Any, **_kwargs: t.Any) -> t.Any:
            ...

        def apply_async(self, *_args: t.Any, **_kwargs: t.Any) -> t.Any:
            ...

    class Celery:
        def __init__(self, _name: str) -> None:
            self.conf: t.MutableMapping[t.Any, t.Any] = {}
            self.control: t.Any

        def init_app(self, _app: t.Any) -> None:
            ...

        def task(self, _callback: t.Any) -> CeleryTask:
            # `CeleryTask()` is returned here as this code is also executed
            # when generating the documentation.
            return CeleryTask()
else:
    Celery = _Celery
# pylint: enable=missing-docstring,no-self-use,pointless-statement


class MyCelery(Celery):
    """A subclass of celery that makes sure tasks are always called with a
    flask app context
    """

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self._flask_app: t.Any = None
        super(MyCelery, self).__init__(*args, **kwargs)

        if t.TYPE_CHECKING:  # pragma: no cover

            class TaskBase:
                pass
        else:
            # self.Task is available in the `Celery` object.
            TaskBase = self.Task  # pylint: disable=access-member-before-definition,invalid-name

        outer_self = self

        class _ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
                # This is not written by us but taken from here:
                # https://web.archive.org/web/20150617151604/http://slides.skien.cc/flask-hacks-and-best-practices/#15

                # pylint: disable=protected-access

                if outer_self._flask_app is None:  # pragma: no cover
                    raise ValueError('You forgot the initialize celery!')

                if outer_self._flask_app.config['TESTING']:
                    return TaskBase.__call__(self, *args, **kwargs)

                with outer_self._flask_app.app_context():  # pragma: no cover
                    return TaskBase.__call__(self, *args, **kwargs)

        self.Task = _ContextTask  # pylint: disable=invalid-name

    def init_app(self, app: t.Any) -> None:
        self._flask_app = app


celery = MyCelery('psef')  # pylint: disable=invalid-name


def init_app(app: t.Any) -> None:
    """Initialize tasks for the given flask app.

    :param: The flask app to initialize for.
    :returns: Nothing
    """
    celery.conf.update(app.config['CELERY_CONFIG'])
    # This is a weird class that is like a dict but not really.
    celery.conf.update({'task_ignore_result': True})
    celery.init_app(app)


@celery.task
def _lint_instances_1(
    linter_name: str,
    cfg: str,
    linter_instance_ids: t.Sequence[int],
) -> None:
    p.linters.LinterRunner(
        p.linters.get_linter_by_name(linter_name),
        cfg,
    ).run(linter_instance_ids)


@celery.task
def _passback_grades_1(submission_ids: t.Sequence[int]) -> None:
    if not submission_ids:  # pragma: no cover
        return

    for sub in p.models.Work.query.filter(p.models.Work.id.in_(  # type: ignore
        submission_ids,
    )):
        sub.passback_grade()


@celery.task
def _send_reminder_mails_1(assignment_id: int) -> None:
    assig = p.models.Assignment.query.get(assignment_id)
    finished = set(g.user_id for g in assig.finished_graders)

    if assig is None or None in {assig.done_type, assig.reminder_email_time}:
        return

    to_mail: t.Iterable[int]

    if assig.done_type == p.models.AssignmentDoneType.assigned_only:
        to_mail = assig.get_assigned_grader_ids()
    elif assig.done_type == p.models.AssignmentDoneType.all_graders:
        to_mail = map(itemgetter(1), assig.get_all_graders(sort=False))

    with p.mail.mail.connect() as conn:
        for user_id in to_mail:
            if user_id in finished:
                continue

            try:
                p.mail.send_grade_reminder_email(
                    assig,
                    p.models.User.query.get(user_id),
                    conn,
                )
            # pylint: disable=broad-except
            except Exception:  # pragma: no cover
                # This happens if mail sending fails or if the user has no
                # e-mail address.
                # TODO: add some sort of logging system.
                # TODO: make this exception more specific
                pass


@celery.task
def _send_done_mail_1(assignment_id: int) -> None:
    assig = p.models.Assignment.query.get(assignment_id)

    if assig is not None and assig.done_email is not None:
        p.mail.send_whopie_done_email(assig)


@celery.task
def _send_grader_status_mail_1(
    assignment_id: int,
    user_id: int,
) -> None:
    assig = p.models.Assignment.query.get(assignment_id)
    user = p.models.User.query.get(user_id)

    if assig and user:
        p.mail.send_grader_status_changed_mail(assig, user)


@celery.task
def _add_1(first: int, second: int) -> int:  # pragma: no cover
    """This function is used for testing if celery works. What it actually does
    is completely irrelevant.
    """
    return first + second


passback_grades = _passback_grades_1.delay  # pylint: disable=invalid-name
lint_instances = _lint_instances_1.delay  # pylint: disable=invalid-name
add = _add_1.delay  # pylint: disable=invalid-name
send_reminder_mails = _send_reminder_mails_1.apply_async  # pylint: disable=invalid-name
send_done_mail = _send_done_mail_1.delay  # pylint: disable=invalid-name
send_grader_status_mail = _send_grader_status_mail_1.delay  # pylint: disable=invalid-name

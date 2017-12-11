"""
This module defines all celery tasks. It is very important that you DO NOT
change the way parameters are used or the parameters provided in existing tasks
as there may tasks left in the old queue. Instead create a new task and change
the mapping of the variables at the bottom of this file.

:license: AGPLv3, see LICENSE for details.
"""
import typing as t

from celery import Celery as _Celery

import psef as p

if t.TYPE_CHECKING:  # pragma: no cover

    class CeleryTask:
        def delay(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
            ...

        def apply_async(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
            ...

    class Celery:
        def __init__(self, name: str) -> None:
            self.conf: t.MutableMapping[t.Any, t.Any] = {}

        def init_app(self, app: t.Any) -> None:
            ...

        def task(self, callback: t.Any) -> CeleryTask:
            return CeleryTask()
else:
    Celery = _Celery


class MyCelery(Celery):
    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        self._flask_app: t.Any = None
        super(MyCelery, self).__init__(*args, **kwargs)

        if t.TYPE_CHECKING:  # pragma: no cover

            class TaskBase:
                pass
        else:
            TaskBase = self.Task

        outer_self = self

        class ContextTask(TaskBase):
            abstract = True

            def __call__(self, *args: t.Any, **kwargs: t.Any) -> t.Any:
                # This is not written by us but taken from here:
                # https://web.archive.org/web/20150617151604/http://slides.skien.cc/flask-hacks-and-best-practices/#15

                if outer_self._flask_app is None:  # pragma: no cover
                    raise ValueError('You forgot the initialize celery!')

                if outer_self._flask_app.config['TESTING']:
                    return TaskBase.__call__(self, *args, **kwargs)

                with outer_self._flask_app.app_context():  # pragma: no cover
                    return TaskBase.__call__(self, *args, **kwargs)

        self.Task = ContextTask

    def init_app(self, app: t.Any) -> None:
        self._flask_app = app


celery = MyCelery('psef')


def init_app(app: t.Any) -> None:
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
    p.linters.LinterRunner(p.linters.get_linter_by_name(linter_name),
                           cfg).run(linter_instance_ids)


@celery.task
def _passback_grades_1(submission_ids: t.Sequence[int]) -> None:
    if not submission_ids:  # pragma: no cover
        return

    for sub in p.models.Work.query.filter(p.models.Work.id.in_(  # type: ignore
        submission_ids,
    )):
        sub.passback_grade()


@celery.task
def _add_1(a: int, b: int) -> int:  # pragma: no cover
    """This function is used for testing if celery works. What it actually does
    is completely irrelevant.
    """
    return a + b


passback_grades = _passback_grades_1.delay
lint_instances = _lint_instances_1.delay
add = _add_1.delay

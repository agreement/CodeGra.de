#!/usr/bin/env python3
"""
This module contains all the linters that are integrated in the service.

Integrated linters are ran by the :class:`LinterRunner` and thus implement run
method.
"""

import os
import uuid
import typing as t
import tempfile
import traceback
import subprocess

import sqlalchemy
from sqlalchemy.orm import sessionmaker

import psef
import psef.files
import psef.models as models
from psef.models import db
from psef.helpers import get_all_subclasses


class Linter:
    """The base class for a linter.

    Every linter should inherit from this class as they are discovered by
    reflecting on subclasses from this class. They should override the ``run``
    method, and they may override the ``DEFAULT_OPTIONS`` variable. If
    ``RUN_LINTER`` is set to ``False`` we never actually run the linter, but
    only create a :py:class:`.models.AssignmentLinter` for this assignment and
    a :py:class:`.models.LinterInstance` for each submission.

    .. note::

        If a linter doesn't override ``DEFAULT_OPTIONS`` the user will not have
        the ability to define a custom configuration for the linter in the
        frontend.
    """
    DEFAULT_OPTIONS: t.ClassVar[t.Mapping[str, str]] = {}
    RUN_LINTER: t.ClassVar[bool] = True

    def __init__(self, cfg: str) -> None:
        self.config = cfg

    def run(self, tempdir: str, emit: t.Callable[[str, int, str, str], None]
            ) -> None:  # pragma: no cover
        """Run the linter on the code in `tempdir`.

        :param tempdir: The temp directory that should contain the code to
                            run the linter on.
        :param emit: A callback to emit a line of feedback, where the first
                     argument is the filename, the second is the line number,
                     the third is the code of the linter error, and the fourth
                     and last is the message of the linter.
        """
        raise NotImplementedError('A subclass should implement this function!')


class Pylint(Linter):
    """The pylint checker.

    This checks python modules for many common errors. It only works on proper
    modules and will display an error on the first line of every file if the
    given code was not a proper module.
    """
    DEFAULT_OPTIONS: t.ClassVar[t.Mapping[str, str]] = {
        'Empty config file': ''
    }

    def run(self, tempdir: str,
            emit: t.Callable[[str, int, str, str], None]) -> None:
        """Run the pylinter.

        Arguments are the same as for :py:meth:`Linter.run`.
        """
        cfg = os.path.join(tempdir, '.__config__')
        with open(cfg, 'w') as config_file:
            config_file.write(self.config)
        sep = uuid.uuid4()
        fmt = '{1}{0}{2}{0}{3}{0}{4}'.format(
            sep, '{path}', '{line}', '{msg_id}', '{msg}'
        )

        out = subprocess.run(
            [
                'pylint', '--rcfile={}'.format(cfg), '--msg-template', fmt,
                tempdir
            ],
            stdout=subprocess.PIPE
        )
        res = out.stdout.decode('utf8')
        if out.returncode == 32:
            raise ValueError(res)
        if out.returncode == 1:
            for dir_name, _, files in os.walk(tempdir):
                for test_file in files:
                    if test_file.endswith('.py'):
                        emit(
                            os.path.join(dir_name, test_file), 1, 'ERR',
                            'No init file was found, pylint did not run!'
                        )
            return
        for line in res.split('\n'):
            args = line.split(str(sep))
            try:
                emit(args[0], int(args[1]), *args[2:])
            except (IndexError, ValueError):
                pass


class Flake8(Linter):
    """Run the Flake8 linter.

    This linter checks for errors in python code and checks the pep8 python
    coding standard. All "noqa"s are disabled when running.
    """
    DEFAULT_OPTIONS: t.ClassVar[t.Mapping[str, str]] = {
        'Empty config file': ''
    }

    def run(self, tempdir: str,
            emit: t.Callable[[str, int, str, str], None]) -> None:
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        # This is not guessable
        sep = uuid.uuid4()
        fmt = '%(path)s{0}%(row)d{0}%(code)s{0}%(text)s'.format(sep)
        out = subprocess.run(
            [
                'flake8', '--disable-noqa', '--config={}'.format(cfg),
                '--format', fmt, tempdir, '--exit-zero'
            ],
            stdout=subprocess.PIPE
        )
        res = out.stdout.decode('utf8')

        if out.returncode != 0:
            raise ValueError(res)

        for line in res.split('\n'):
            args = line.split(str(sep))
            try:
                emit(args[0], int(args[1]), *args[2:])
            except (IndexError, ValueError):
                pass


class MixedWhitespace(Linter):
    """Run the MixedWhitespace linter.

    This linter checks if a file contains mixed indentation on the same line.
    It doesn't catch different types of indentation being used in a file but on
    different lines. Instead of adding a comment in the sidebar, the mixed
    whitespace will be highlighted in the code.
    """
    RUN_LINTER: t.ClassVar[bool] = False


class LinterRunner():
    """This class is used to run a :class:`Linter` with a specific config on
    sets of :class:`models.Work`.

    .. py:attribute:: linter
        The attached :class:`Linter` that will be ran by this class.
    """

    def __init__(self, cls: t.Type[Linter], cfg: str) -> None:
        """Create a new instance of :class:`LinterRunner`

        :param Linter cls: The linter to run.
        :param str cfg: The config as as `str` to pass to the linter.
        """
        self.linter = cls(cfg)  # type: Linter

    def run(self, linter_instance_ids: t.Sequence[int]) -> None:
        """Run this linter runner on the given works.

        .. note:: This method takes a long time to execute, please run it in a
                  thread.

        :param linter_instance_ids: A sequence of all the ids of the linter
            instances which should be run. If this linter instance has already
            run once its old comments will be removed.

        :returns: Nothing
        """
        for linter_instance_id in linter_instance_ids:
            linter_instance = db.session.query(models.LinterInstance
                                               ).get(linter_instance_id)

            # This should never happen however it is better to check here.
            if linter_instance is None:  # pragma: no cover
                continue

            try:
                self.test(linter_instance)
            except Exception as e:
                traceback.print_exc()
                linter_instance.state = models.LinterState.crashed
                db.session.commit()

    def test(self, linter_instance: models.LinterInstance) -> None:
        """Test the given code (:class:`models.Work`) and add generated
        comments.

        :param linter_instance: The linter instance that will be run. This
            linter instance is linked to a work from which all files will be
            restored and the linter will be run on those files.
        :returns: Nothing
        """
        temp_res: t.Dict[str, t.Dict[int, t.List[t.Tuple[str, str]]]]
        temp_res = {}
        res: t.Dict[int, t.Mapping[int, t.Sequence[t.Tuple[str, str]]]]
        res = {}

        code = db.session.query(models.File).filter_by(
            work_id=linter_instance.work_id,
            parent=None,
        ).one()

        with tempfile.TemporaryDirectory() as tmpdir:

            def emit(f: str, line: int, code: str, msg: str) -> None:
                if f.startswith(tmpdir):
                    f = f[len(tmpdir) + 1:]
                if f not in temp_res:
                    temp_res[f] = {}
                line = line - 1
                if line not in temp_res[f]:
                    temp_res[f][line] = []
                temp_res[f][line].append((code, msg))

            files = psef.files.restore_directory_structure(
                code,
                tmpdir,
            )

            self.linter.run(os.path.join(tmpdir, code.name), emit)

        tmpdir = None

        def do(tree: psef.files.FileTree, parent: str) -> None:
            parent = os.path.join(parent, tree['name'])
            if 'entries' in tree:  # this is dir:
                for entry in tree['entries']:
                    do(entry, parent)
            elif parent in temp_res:
                res[tree['id']] = temp_res[parent]
                del temp_res[parent]

        do(files, '')

        models.LinterComment.query.filter_by(linter_id=linter_instance.id
                                             ).delete()

        for comment in linter_instance.add_comments(res):
            db.session.add(comment)

        linter_instance.state = models.LinterState.done

        db.session.commit()


def get_all_linters(
) -> t.Dict[str, t.Dict[str, t.Union[str, t.Mapping[str, str]]]]:
    """Get an overview of all linters.

    The returned linters are all the subclasses of :class:`Linter`.

    :returns: A mapping of the name of the linter to a dictionary containing
        the description and the default options of the linter with that name

    .. testsetup::

        from psef.linters import get_all_linters, Linter

    .. doctest::

        >>> class MyLinter(Linter): pass
        >>> MyLinter.__doc__ = "Description"
        >>> MyLinter.DEFAULT_OPTIONS = {'wow': 'sers'}
        >>> all_linters = get_all_linters()
        >>> sorted(all_linters.keys())
        ['Flake8', 'MixedWhitespace', 'MyLinter', 'Pylint']
        >>> linter = all_linters['MyLinter']
        >>> linter == {'desc': 'Description', 'opts': {'wow': 'sers'} }
        True
    """
    res = {}
    for cls in get_all_subclasses(Linter):
        item: t.Dict[str, t.Union[str, t.Mapping[str, str]]]
        item = {
            'desc': cls.__doc__,
            'opts': cls.DEFAULT_OPTIONS,
        }
        res[cls.__name__] = item
    return res


def get_linter_by_name(name: str) -> t.Type[Linter]:
    """Get the linter class associated with the given name.

    :param str name: The name of the linter wanted.
    :returns: The linter with the attribute `__name__` equal to `name`. If
        there are multiple linters with the name `name` the result can be any
        one of these linters.
    :raises ValueError: If the linter with the specified name is not found.
    """
    for linter in get_all_subclasses(Linter):
        if linter.__name__ == name:
            return linter
    raise ValueError('No linter with name {} found.'.format(name))

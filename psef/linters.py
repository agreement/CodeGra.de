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

import requests
import sqlalchemy
from sqlalchemy.orm import sessionmaker

import psef.files
import psef.models as models
from psef import app
from psef.helpers import get_all_subclasses

ENGINE = sqlalchemy.create_engine(
    app.config['SQLALCHEMY_DATABASE_URI'],
    **app.config['DATABASE_CONNECT_OPTIONS']
)


class Linter:
    """The base class for a linter.

    Every linter should inherit from this class as they are discovered by
    reflecting on subclasses from this class. They should also override all
    methods and variables from this class.
    """
    DEFAULT_OPTIONS = {}  # type: t.MutableMapping[str, str]

    def __init__(self, cfg: str) -> None:
        self.config = cfg

    def run(self, tempdir: str,
            emit: t.Callable[[str, int, str, str], None]) -> None:
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
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def run(self, tempdir: str,
            emit: t.Callable[[str, int, str, str], None]) -> None:
        """Run the pylinter.

        Arguments are the same as for :py:meth:`Linter.run`.
        """
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as config_file:
            config_file.write(self.config)
        sep = uuid.uuid4()
        fmt = '{1}{0}{2}{0}{3}{4}{0}{5}'.format(
            sep, '{path}', '{line}', '{C}', '{msg_id}', '{msg}'
        )

        out = subprocess.run(
            [
                'pylint', '--rcfile={}'.format(cfg), '--msg-template', fmt,
                tempdir
            ],
            stdout=subprocess.PIPE
        )
        if out.returncode == 1:
            for dir_name, _, files in os.walk(tempdir):
                for test_file in files:
                    if test_file.endswith('.py'):
                        emit(
                            os.path.join(dir_name, test_file), 1, 'ERR',
                            'No init file was found, pylint did not run!'
                        )
            return
        for line in out.stdout.decode('utf8').split('\n'):
            args = line.split(str(sep))
            if len(args) == 4:
                try:
                    emit(args[0], int(args[1]), *args[2:])
                except ValueError:
                    pass


class Flake8(Linter):
    """Run the Flake8 linter.

    This linter checks for errors in python code and checks the pep8 python
    coding standard. All "noqa"s are disabled when running.
    """
    DEFAULT_OPTIONS = {'Empty config file': ''}

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
                '--format', fmt, tempdir
            ],
            stdout=subprocess.PIPE
        ).stdout.decode('utf8')
        for line in out.split('\n'):
            args = line.split(str(sep))
            if len(args) == 4:
                try:
                    emit(args[0], int(args[1]), *args[2:])
                except ValueError:
                    pass


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

    def run(
        self, works: t.Iterable[int], tokens: t.Iterable[str], urlpath: str
    ) -> None:
        """Run this linter runner on the given works.

        .. note:: This method takes a long time to execute, please run it in a
                  thread.

        .. note:: The `tokens` and `works` should match item for item. So
                  `token[i]` should be valid only for `work[i]`.

        The results will be send to the given URL with are PUT request and are
        identifiable by the token which will be formatted into the URL.

        :param works: A list of ids of :class:`psef.models.Work` items that
                      will be fetched and where the linters will run on.
        :param tokens: A list of tokens that are the ids of
                       :class:`psef.models.LinterInstance` that will be used
                       when posting back to the given callback url.
        :param urlpath: The url that should be used to postback the result
                            of the linters, it should be possible to do
                            `urlpath.format(token)` which should result in a
                            valid url for posting back the result.
        :returns: Nothing
        """
        session = sessionmaker(bind=ENGINE, autoflush=False)()
        for work, token in zip(works, tokens):
            code = session.query(models.File).filter_by(
                parent=None, work_id=work
            ).first()
            try:
                self.test(code, urlpath.format(token))
            except Exception as e:
                traceback.print_exc()
                requests.put(urlpath.format(token), json={'crashed': True})

    def test(self, code: models.File, callback_url: str) -> None:
        """Test the given code (:class:`models.Work`) and send the results to the
        given URL.

        :param code: The file that the linter should be run on, this file and
                     all its children will be restored to a directory and the
                     linter will run on them.
        :param callback_url: The url that should be used to give back the
                     result of the linter.
        :returns: Nothing
        """
        temp_res: t.MutableMapping[str, t.MutableSequence[t.Tuple[int, str, str
                                                                  ]]] = {}
        res: t.MutableMapping[str, t.MutableSequence[t.Tuple[int, str, str]]
                              ] = {}

        def emit(f: str, line: int, code: str, msg: str):
            if f.startswith(tmpdir):
                f = f[len(tmpdir) + 1:]
            elif f[0] == '/':
                f = f[1:]
            if f not in temp_res:
                temp_res[f] = []
            temp_res[f].append((line - 1, code, msg))

        with tempfile.TemporaryDirectory() as tmpdir:
            files = psef.files.restore_directory_structure(code, tmpdir)

            self.linter.run(tmpdir, emit)

        def do(tree: t.MutableMapping[str, t.Any], parent: str) -> None:
            parent = os.path.join(parent, tree['name'])
            if 'entries' in tree:  # this is dir:
                for entry in tree['entries']:
                    do(entry, parent)
            elif parent in temp_res:
                res[tree['id']] = temp_res[parent]
                del temp_res[parent]

        do(files, '')
        requests.put(
            callback_url,
            json={'files': res,
                  'name': self.linter.__class__.__name__}
        )


def get_all_linters(
) -> t.Dict[str, t.Dict[str, t.Union[str, t.MutableMapping[str, str]]]]:
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
        ['Flake8', 'MyLinter', 'Pylint']
        >>> linter = all_linters['MyLinter']
        >>> linter == {'desc': 'Description', 'opts': {'wow': 'sers'} }
        True
    """
    res = {}
    for cls in get_all_subclasses(Linter):
        item: t.Dict[str, t.Union[str, t.MutableMapping[str, str]]]
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

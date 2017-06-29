#!/usr/bin/env python3

import os
import uuid
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

ENGINE = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'],
                                  **app.config['DATABASE_CONNECT_OPTIONS'])


class Linter:
    """The base class for a linter.

    Every linter should inherit from this class as they are discovered by
    reflecting on subclasses from this class. They should also override all
    methods and variables from this class.
    """
    NAME = None
    DEFAULT_OPTIONS = {}

    def run(self, tempdir, emit):
        """Run the bear linter on the code in `tempdir`.

        :param str tempdir: The temp directory that should contain the code to
                            run the linter on.
        :param emit: A callback to emit a line of feedback, where the first
                     argument is the filename, the second is the line number,
                     the third is the code of the linter error, and the fourth
                     and last is the message of the linter.
        :type emit: Callable[str, str, str, str]
        :rtype: None
        """
        raise NotImplementedError('A subclass should implement this function!')


class BearLinter(Linter):
    """Implements a generic coala linter.

    This class itself is not a functional linter yet, you need to at least
    define/override `NAME`, `DEFAULT_OPTIONS`, `FILTER_STR`, `EXTENSION` and `BEAR_NAME`.
    The first two are defined in :class:`Linter`, the third is the string
    passed to `coala` as files argument, the fourth is the extension that
    should be put after the `LINTER_STR`, and the last is the name of the bear
    that should be given to the `coala` program.
    """
    NAME = '__ignore__'
    FILTER_STR = '/**/*.'
    BEAR_NAME = None
    EXTENSION = '*'

    def __init__(self, config):
        """Create a new :class:`BearLinter`.

        :param str config: The config for the bearlinter as a string.
        """
        self.config = config

    def run(self, tempdir, emit):
        """Run the bear linter.

        The arguments are the same as for the base :py:meth:`Linter.emit`
        function.
        """
        cfg = os.path.join(tempdir, '.coafile')
        with open(cfg, 'w') as config_file:
            config_file.write(self.config)

        sep = str(uuid.uuid4())

        sourcedir = tempdir + self.FILTER_STR + self.EXTENSION
        out = subprocess.run(
            [
                'coala', '--format', '{1}{0}{2}{0}{3}{0}{4}'.format(
                    sep, '{file}', '{line}', '{severity_str}', '{message}'),
                '--config', os.path.join(tempdir, '.coafile'),
                '--files', sourcedir, '--bears', self.BEAR_NAME,
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')

        for line in out.split('\n'):
            if line:
                line2 = line.split(sep, 3)
                try:
                    emit(line2[0], int(line2[1]), line2[2], line2[3])
                except ValueError:
                    pass


class Pylint(Linter):
    """The pylint checker.

    This checks python modules for many common errors. It only works on proper
    modules and will display an error on the first line of every file if the
    given code was not a proper module.
    """
    NAME = 'Pylint'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        """Create a new :class:`Pylint` instance.

        :param str config: The config for pylint as a string.
        """
        self.config = config

    def run(self, tempdir, emit):
        """Run the pylinter.

        Arguments are the same as for :py:meth:`Linter.run`.
        """
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as config_file:
            config_file.write(self.config)
        sep = uuid.uuid4()
        fmt = '{1}{0}{2}{0}{3}{4}{0}{5}'.format(sep, '{path}', '{line}', '{C}',
                                                '{msg_id}', '{msg}')

        out = subprocess.run(
            [
                'pylint', '--rcfile={}'.format(cfg), '--msg-template', fmt,
                tempdir
            ],
            stdout=subprocess.PIPE)
        if out.returncode == 1:
            for dir_name, _, files in os.walk(tempdir):
                for test_file in files:
                    if test_file.endswith('.py'):
                        emit(
                            os.path.join(dir_name, test_file), 1, 'ERR',
                            'No init file was found, pylint did not run!')
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
    NAME = 'Flake8'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
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
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            args = line.split(str(sep))
            if len(args) == 4:
                try:
                    emit(args[0], int(args[1]), *args[2:])
                except ValueError:
                    pass


class PyFlakes(BearLinter):
    """Run the pyflake checker.

    This linter checks python code for style error, but not for formatting.
    """
    NAME = 'PyFlakes'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'PyFlakesBear'
    EXTENSION = 'py'


class Pycodestyle(BearLinter):
    """Run the Pycodestyle checker.

    This linter checks python code for pep8 compliance.
    """
    NAME = 'Pycodestyle'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'PycodestyleBear'
    EXTENSION = 'py'


class HtmlLintBear(BearLinter):
    """Run the HTMLLint linter.
    """
    NAME = 'HTML Linter'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'HTMLLintBear'
    EXTENSION = '(html|htm)'


class ShellCheckBear(BearLinter):
    """Run the shellcheck linter.

    This linter checks shell, bash and languages like them for common errors.
    """
    NAME = 'Shell Linter'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'ShellCheckBear'


class HaskellCheckBear(BearLinter):
    """Run the GHCmod package.

    This linter checks Haskell code for style errors.
    """
    NAME = 'GhcMod'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'GhcModBear'


class JavaCheckBear(BearLinter):
    """Run the java Checkstyle linter.
    """
    NAME = 'Checkstyle'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'CheckstyleBear'
    EXTENSION = 'java'


class ClangCheckBear(BearLinter):
    """Run the Clang compiler as linter.

    This linter check C and C++ code for syntax errors and semantical problems.
    """
    NAME = 'Clang'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'ClangBear'


class GoLintCheckBear(BearLinter):
    """Run the GoLint checer.

    This checker checks for common errors in Go code.
    """
    NAME = 'Golint'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'GoLintBear'


class GoFmtCheckBear(BearLinter):
    """Run gofmt as a linter.

    This checker checks for deviations from the formatting as indicated by the
    `gofmt` program.
    """
    NAME = 'Gofmt'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'GofmtBear'


class PHPCodeCheckBear(BearLinter):
    """Run the PHP CodeSniffer linter.

    This linter checks PHP code for syntax en formatting errors.
    """
    NAME = 'PHP Codesniffer'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'PHPCodeSnifferBear'


class ESLintCheckBear(BearLinter):
    """Run the ESLint linter.

    This linter checks JavaScript for style issues and semantic errors.
    """
    NAME = 'Eslint'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'ESLintCheckBear'


class SCSSCheckBear(BearLinter):
    """Run the SCSSLint linter.

    This linter checks CSS for formatting and syntax errors.
    """
    NAME = 'SCSSLint'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'SCSSLintBear'


class LatexCheckBear(BearLinter):
    """Run the chktex linter.

    This linter checks Latex for formatting and syntax errors
    """
    NAME = 'Chktex'
    DEFAULT_OPTIONS = {'Empty config file': ''}
    BEAR_NAME = 'LatexLintBear'


class LinterRunner():
    """The class that controls running a subclass of :class:`Linter`
    """

    def __init__(self, cls, cfg):
        """Create a new instance of :class:`LinterRunner`

        :param Linter cls: The linter to run.
        :param str cfg: The config as as `str` to pass to the linter.
        """
        self.linter = cls(cfg)

    def run(self, works, tokens, urlpath):
        """Run this linter runner on the given works.

        .. note:: This method takes a long time to execute, please run it in a
                  thread.

        .. note:: The `tokens` and `works` should match item for item. So
                  `token[i]` should be valid only for `work[i]`.

        :param works: A list of ids of :class:`psef.models.Work` items that
                      will be fetched and where the linters will run on.
        :type works: list[int]
        :param tokens: A list of tokens that are the ids of
                       :class:`psef.models.LinterInstance` that will be used
                       when posting back to the given callback url.
        :type tokens: list[str]
        :param str urlpath: The url that should be used to postback the result
                            of the linters, it should be possible to do
                            `urlpath.format(token)` which should result in a
                            valid url for posting back the result.
        :rtype: None
        """
        session = sessionmaker(bind=ENGINE, autoflush=False)()
        for work, token in zip(works, tokens):
            code = session.query(models.File).filter_by(
                parent=None, work_id=work).first()
            try:
                self.test(code, urlpath.format(token))
            except Exception as e:
                traceback.print_exc()
                requests.put(urlpath.format(token), json={'crashed': True})

    def test(self, code, callback_url):
        """Actually run the linter for the given code object.

        :param code: The file that the linter should be run on, this file and
                     all its children will be restored to a directory and the
                     linter will run on them.
        :type code: psef.models.File
        :param str callback_url: The url that should be used to give back the
                     result of the linter.
        :rtype: None
        """
        temp_res = {}
        res = {}

        def emit(f, line, code, msg):
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

        def do(tree, parent):
            parent = os.path.join(parent, tree['name'])
            if 'entries' in tree:  # this is dir:
                for entry in tree['entries']:
                    do(entry, parent)
            elif parent in temp_res:
                res[tree['id']] = temp_res[parent]
                del temp_res[parent]

        do(files, '')
        requests.put(
            callback_url, json={'files': res,
                                'name': self.linter.NAME})


def get_all_linters():
    """Get all classes that are linters.

    :rtype: dict[str, dict[str, *]]
    :returns: A dictionary that that maps the name of the linter to a
              dictionary with two keys, `desc` and `opts`, that respectively
              are the documentation for the linter and possible default
              options, which is a dictionary mapping a descriptive name of the
              default option to the config string.
    """
    res = {}
    for cls in get_all_subclasses(Linter):
        if cls.NAME == '__ignore__':
            continue
        res[cls.NAME] = {
            'desc': cls.__doc__,
            'opts': cls.DEFAULT_OPTIONS,
        }
    return res


def get_linter_by_name(name):
    """Get the linter class associated with the given name.

    :param str name: The name of the linter wanted.
    :rtype: Linter
    :returns: The linter with the attribute `NAME` equal to `name`. If there
              are multiple linters with the name `name` the result can be any
              one of these linters.
    """
    for linter in get_all_subclasses(Linter):
        if linter.NAME == name:
            return linter

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

engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'],
                                  **app.config['DATABASE_CONNECT_OPTIONS'])


class Linter:
    NAME = None
    DESCRIPTION = None
    DEFAULT_OPTIONS = {}


class Pylint(Linter):
    NAME = 'Pylint'
    DESCRIPTION = 'The pylint checker, this checker only works on modules!'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        # This is not guessable
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
                for f in files:
                    if f.endswith('.py'):
                        emit(
                            os.path.join(dir_name, f), 1, 'ERR',
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
    NAME = 'Flake8'
    DESCRIPTION = 'The flake8 linter with all "noqa"s disabled.'
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


# BERENLINTERS

# pylint
class PyLintBear(Linter):
    NAME = 'PyLint'
    DESCRIPTION = 'The pylint checker'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'PyLintBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        helpme(out)


def helpme(out):
    for line in out.split('\n'):
        if len(line) > 0:
            line2 = line.split(None, 3)
            try:
                Linter.emit(line2[0], int(line2[1]), line2[2], line2[3])
            except ValueError:
                pass    
# html lint
class HtmlLintBear(Linter):
    NAME = 'HTML Linter'
    DESCRIPTION = 'The HTML lint checker'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'HTMLLintBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass


class ShellCheckBear(Linter):
    NAME = 'Shell Linter'
    DESCRIPTION = 'The Shell cheker'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'ShellCheckBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass

class HaskellCheckBear(Linter):
    NAME = 'Haskell Linter'
    DESCRIPTION = 'Haskell ghc mod package'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'GhcModBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass

class JavaCheckBear(Linter):
    NAME = 'Java Linter'
    DESCRIPTION = 'Java Checkstyle'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'CheckstyleBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass


class ClangCheckBear(Linter):
    NAME = 'Clang'
    DESCRIPTION = 'syntax and semantical problems'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'ClangBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass


class GoLintCheckBear(Linter):
    NAME = 'golint'
    DESCRIPTION = 'Suggest better formatting options in Go code.'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'GoLintBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass


class GoFmtCheckBear(Linter):
    NAME = 'gofmt'
    DESCRIPTION = 'Suggest better formatting options in Go code.'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'GofmtBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass


class PHPCodeCheckBear(Linter):
    NAME = 'PHP Codesniffer'
    DESCRIPTION = 'PHP syntax en formatting'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'PHPCodeSnifferBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass


class ESLintCheckBear(Linter):
    NAME = 'Eslint'
    DESCRIPTION = 'Check JavaScript for style issues and semantic errors.'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'ESLintBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass


class SCSSCheckBear(Linter):
    NAME = 'SCSSLint'
    DESCRIPTION = 'Check CSS for formatting and syntax errors'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'SCSSLintBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass


class LatexCheckBear(Linter):
    NAME = 'chktex'
    DESCRIPTION = 'Check Latex for formatting and syntax errors'
    DEFAULT_OPTIONS = {'Empty config file': ''}

    def __init__(self, config):
        self.config = config

    def run(self, tempdir, emit):
        cfg = os.path.join(tempdir, '.flake8')
        with open(cfg, 'w') as f:
            f.write(self.config)

        sourcedir = tempdir + "/**/*.*"
        out = subprocess.run(
            [
                'coala', '--format', '{file} {line} {severity_str} {message}',
                '--files', sourcedir, '--bears', 'LatexLintBear', '-I'
            ],
            stdout=subprocess.PIPE).stdout.decode('utf8')
        for line in out.split('\n'):
            if len(line) > 0:
                args = line.split(None, 3)
                try:
                    emit(args[0], int(args[1]), args[2], args[3])
                except ValueError:
                    pass

class LinterRunner():
    def __init__(self, cls, cfg):
        self.linter = cls(cfg)

    def run(self, works, tokens, urlpath):
        session = sessionmaker(bind=engine, autoflush=False)()
        for work, token in zip(works, tokens):
            code = session.query(models.File).filter_by(
                parent=None, work_id=work).first()
            try:
                self.test(code, urlpath.format(token))
            except Exception as e:
                traceback.print_exc()
                requests.put(urlpath.format(token), json={'crashed': True})

    def test(self, code, callback_url):
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
    res = {}
    for cls in get_all_subclasses(Linter):
        res[cls.NAME] = {
            'desc': cls.DESCRIPTION,
            'opts': cls.DEFAULT_OPTIONS,
        }
    return res


def get_linter_by_name(name):
    for linter in get_all_subclasses(Linter):
        if linter.NAME == name:
            return linter

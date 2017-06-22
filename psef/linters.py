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

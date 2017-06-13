# -*- py-isort-options: '("-sg *"); -*-
import os
import sys
import tempfile
import shutil
import subprocess

import pytest

from werkzeug.datastructures import FileStorage

from pathlib import Path

my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, my_path + '/../')

import psef.auth as a
import psef.models as m
from psef.errors import APIException
import psef.files


def ensure_list(item):
    if isinstance(item, list):
        return item
    return [item]


@pytest.fixture(scope='module')
def pse_course(session):
    pse = m.Course(name='Project Software Engineering')
    session.add(pse)
    session.commit()
    yield pse


@pytest.fixture(scope='module')
def bs_course(session):
    bs = m.Course(name='Besturingssystemen')
    session.add(bs)
    session.commit()
    yield bs


@pytest.fixture(scope='module')
def seq_assignment(session, bs_course):
    sec = m.Assignment(name='Security assignment', course=bs_course)
    session.add(sec)
    session.commit()
    yield sec


@pytest.fixture(scope='module')
def thomas(session, bs_course):
    thomas = m.User(
        name='Thomas Schaper',
        role=None,
        courses={},
        password='',
        email='thas')

    session.add(thomas)
    session.commit()
    yield m.User.query.filter_by(name='Thomas Schaper').first()


@pytest.fixture(scope='module')
def seq_work(session, seq_assignment, thomas):
    work = m.Work(
        assignment=seq_assignment,
        user=thomas,
        edit=0,
        state=m.WorkStateEnum.initial)
    session.add(work)
    session.commit()
    yield work


@pytest.mark.parametrize('files', [{
    '.': [('file.c', 'FILES!!')]
}, {
    'dir1': [('file_1.c', 'om'), ('file_2.py', '23'), {
        'dir2': [('file4', 'as'), ('file5.a/c.b', 'muchnice'), {
            'dir4': []
        }]
    }]
}])
def test_file_tree(db, session, seq_work, files):
    def tree_to_dict(tree):
        if tree.is_directory:
            assert not tree.extension
            return {
                tree.name: [tree_to_dict(child) for child in tree.children]
            }
        else:
            if tree.extension:
                assert tree.extension.find('.') == -1
                return (tree.name + '.' + tree.extension, tree.filename)
            else:
                assert tree.name.find('.') == -1
                return (tree.name, tree.filename)

    seq_work.add_file_tree(db, files)
    session.commit()
    db.session.commit()
    tree = m.File.query.filter(m.File.work == seq_work and
                               m.File.parent is None).first()
    assert (tree_to_dict(tree) == files)
    m.File.query.filter_by(work_id=seq_work.id).delete()
    session.commit()


@pytest.mark.parametrize('files', [{
    '.': ['file.c']
}, {
    '.': ['file.c', 'file2.c']
}, {
    'dir1': [
        'file_1.c', 'file_2.py', {
            'dir2': [
                'file4', 'file5.a_c.b', {
                    'dir4': [{
                        'dir5': ['a.c']
                    }, {
                        'dir6': []
                    }]
                }
            ]
        }
    ]
}])
def test_extract(session, seq_work, files):
    def create_tree(tree, parent):
        for item in ensure_list(tree):
            if isinstance(item, dict):
                for key, f in item.items():
                    Path(os.path.join(parent, key)).mkdir()
                    create_tree(f, os.path.join(parent, key))
            else:
                Path(os.path.join(parent, item)).touch()

    def same_tree(a, b):
        b = ensure_list(b)
        for item in ensure_list(a):
            if isinstance(item, dict):
                for bitem in b:
                    if isinstance(bitem, dict):
                        print(bitem.keys(), item.keys())
                        if set(bitem.keys()) == set(item.keys()):
                            for key, val in item.items():
                                if not same_tree(val, bitem[key]):
                                    return False
                            break
                else:
                    return False
            else:
                assert isinstance(item[1], str)
                if item[0] not in b:
                    return False
        return True

    tmpdir = tempfile.mkdtemp()
    _, tmparchive = tempfile.mkstemp()
    os.remove(tmparchive)
    tmparchive += '.tar.gz'
    try:
        if len(files.keys()) == 1 and list(files.keys())[0] == '.':
            create_tree(list(files.values())[0], tmpdir)
        else:
            create_tree(files, tmpdir)
        subprocess.call(['tar', '-cvzf', tmparchive, '-C', tmpdir, '.'])
        with open(tmparchive, 'rb') as arch:
            res = psef.files.extract(FileStorage(arch, filename=tmparchive))
            print(res, files)
            if len(files.keys()) == 1 and list(files.keys())[0] == '.':
                assert len(res) == 1
                assert set(list(files.values())[0]) == set(
                    n[0] for n in list(res.values())[0])
            else:
                assert same_tree(res, files)
    finally:
        shutil.rmtree(tmpdir)
        os.remove(tmparchive)


@pytest.mark.parametrize('tree,correct', [({
    1: [1, 2]
}, {
    1: [1, 2]
}), ({
    1: {
        2: {
            3: {
                4: [1]
            }
        }
    }
}, {
    1: [1]
}), ({
    1: {
        2: {
            3: {
                4: [1, {
                    5: 6
                }, 2]
            }
        }
    }
}, {
    1: [1, {
        5: 6
    }, 2]
})])
def test_dehead(tree, correct):
    assert correct == psef.files.dehead_filetree(tree)

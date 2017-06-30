"""
This module is used for file IO and handling and provides functions for
extracting and abstracting the structures of directories and archives.
"""

import os
import re
import csv
import uuid
import shutil
import tempfile
from functools import reduce

import archive
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from psef import app, blackboard
from psef.errors import APICodes, APIException

_known_archive_extensions = tuple(archive.extension_map.keys())

# Gestolen van Erik Kooistra
_bb_txt_format = re.compile(
    r"(?P<assignment_name>.+)_(?P<student_id>\d+)_attempt_"
    r"(?P<datetime>\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}).txt")


def get_binary_contents(file):
    """Get the binary contents of a given :class:`models.File`.

    :param models.File file: The file object to read.
    :returns: The contents of the file
    :rtype: bytes
    """

    filename = os.path.join(app.config['UPLOAD_DIR'], file.filename)
    with open(filename, 'rb') as codefile:
        return codefile.read()


def get_file_contents(code):
    """Get the contents of the given :class:`models.File`.

    :param models.File code: The file object to read.
    :returns: The contents of the file with newlines.
    :rtype: str
    """
    filename = os.path.join(app.config['UPLOAD_DIR'], code.filename)
    try:
        if os.path.islink(filename):
            raise APIException('This file is a symlink to `{}`.'.format(
                (os.readlink(filename))),
                               'The file {} is a symlink'.format(code.id),
                               APICodes.INVALID_STATE, 410)
        with open(filename, 'r', encoding='utf-8') as codefile:
            return codefile.read()
    except UnicodeDecodeError:
        raise APIException(
            'Cannot display this file!',
            'The selected file with id {} was not UTF-8'.format(code.id),
            APICodes.OBJECT_WRONG_TYPE, 400)


def restore_directory_structure(code, parent):
    """Restores the directory structure recursively for a code submission
    (:class:`models.Work`).

    The directory structure is returned like this:
    ```
    {
        "id": 1,
        "name": "rootdir"
        "entries": [
            {
                "id": 2,
                "name": "file1.txt"
            },
            {
                "id": 3,
                "name": "subdir"
                "entries": [
                    {
                        "id": 4,
                        "name": "file2.txt."
                    },
                    {
                        "id": 5,
                        "name": "file3.txt"
                    }
                ],
            },
        ],
    }
    ```

    :param models.File code: A file
    :param str parent: Path to parent directory
    :returns: A tree as described
    :rtype: dict
    """
    out = os.path.join(parent, code.get_filename())
    if code.is_directory:
        os.mkdir(out)
        return {
            "name": code.get_filename(),
            "id": code.id,
            "entries": [
                restore_directory_structure(child, out)
                for child in code.children
            ]
        }
    else:  # this is a file
        filename = os.path.join(app.config['UPLOAD_DIR'], code.filename)
        shutil.copyfile(filename, out, follow_symlinks=False)
        return {"name": code.get_filename(), "id": code.id}


def rename_directory_structure(rootdir):
    """Creates a nested dictionary that represents the folder structure of
    rootdir.

    A tree like:
    + dir1
      + dir 2
        - file 1
        - file 2
      - file 3
    will be moved to files given by :py:func:`random_file_path` and the object
    returned will represent the file structure, which will be something like
    this:
    ```
    {
        'dir1': {
            [
                'dir 2':{
                    [
                        ('file 1', 'new_name'),
                        ('file 2', 'new_name')
                    ]
                },
                ('file 3', 'new_name')
            ]
        }
    }
    ```

    :param str rootdir: The root directory to rename, files will not be removed
    :returns: The tree as described above
    :rtype: dict
    """
    dir = {}
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)
        parent = reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir

    def convert_to_lists(name, dirs):
        res = []
        for key, value in dirs.items():
            if value is None:
                new_name, filename = random_file_path()
                shutil.move(os.path.join(name, key), new_name)
                res.append((key, filename))
            else:
                res.append({
                    key: convert_to_lists(os.path.join(name, key), value)
                })
        return res

    return convert_to_lists(rootdir[:start], dir)[0]


def is_archive(file):
    """Checks whether the file ends with a known archive file extension.

    File extensions are known if they are recognized by the archive module.

    :param FileStorage file: Some file
    :returns: True if the file has a known extension
    :rtype: bool
    """
    return file.filename.endswith(_known_archive_extensions)


def extract_to_temp(file):
    """Extracts the contents of file into a temporary directory.

    :param FileStorage file: An archive
    :returns: The path to the temporary directory
    :rtype: str
    """
    tmpmode, tmparchive = tempfile.mkstemp()
    os.remove(tmparchive)
    tmparchive += os.path.basename(secure_filename('archive_' + file.filename))
    tmpdir = tempfile.mkdtemp()
    try:
        file.save(tmparchive)
        archive.extract(tmparchive, to_path=tmpdir, method='safe')
    finally:
        os.remove(tmparchive)
    return tmpdir


def extract(file):
    """Extracts all files in archive with random name to uploads folder.

    :param FileStorage file: The file to extract
    :returns: A file tree as generated by :py:func:`rename_directory_structure`
    :rtype: dict
    """
    tmpdir = extract_to_temp(file)
    rootdir = tmpdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    res = rename_directory_structure(tmpdir)[tmpdir[start:]]
    if len(res) > 1:
        return {'archive': res if isinstance(res, list) else [res]}
    elif not isinstance(res[0], dict):
        return {'archive': res}
    else:
        return res[0]
    shutil.rmtree(tmpdir)


def random_file_path():
    """Generates a new random file path in the upload directory.

    :returns: The name of the new file and a path to that file
    :rtype: (str, str)
    """
    while True:
        name = str(uuid.uuid4())
        candidate = os.path.join(app.config['UPLOAD_DIR'], name)
        if os.path.exists(candidate):
            continue
        else:
            break
    return candidate, name


def dehead_filetree(tree):
    """Remove the head of the given filetree while preserving the old head
    name.

    So a tree {1: 2: 3: 4: [f1, f2]} will be converted to {1: [f1, f2]}

    :param dict tree: The file tree as generated by :py:func:`extract`
    :returns: The tree deheaded
    :rtype: dict
    """
    assert len(tree) == 1
    head_node = list(tree.keys())[0]
    while len(tree[head_node]) == 1:
        if isinstance(tree[head_node], list):
            tree[head_node] = tree[head_node][0]
        elif isinstance(tree[head_node], dict):
            tree[head_node] = tree[head_node][list(tree[head_node].keys())[0]]
        else:
            break
        if not (isinstance(tree[head_node], list) or
                isinstance(tree[head_node], dict)):
            tree[head_node] = [tree[head_node]]
            break
    return tree


def process_files(files):
    """Process the given files by extracting, moving and saving their tree
    structure.

    :param files: The files to move and extract
    :rtype: list of FileStorage
    :returns: The tree of the files as is described by
              :py:func:`rename_directory_structure`
    :rtype: dict
    """
    if len(files) > 1 or not is_archive(files[0]):
        res = []
        for file in files:
            if is_archive(file):
                res.append(extract(file))
            else:
                new_file_name, filename = random_file_path()
                res.append((file.filename, filename))
                file.save(new_file_name)
        res = {'top': res}
    else:
        res = extract(files[0])

    return dehead_filetree(res)


def process_blackboard_zip(file):
    """Process the given :py:module:`blackboard` zip file by extracting, moving and saving
    the tree structure of each submission.

    :param FileStorage file: The blackboard gradebook to import
    :returns: List of tuples (BBInfo, tree)
    :rtype: list
    """
    tmpdir = extract_to_temp(file)
    info_files = filter(None,
                        [_bb_txt_format.match(f) for f in os.listdir(tmpdir)])
    submissions = []
    for info_file in info_files:
        files = []
        info = blackboard.parse_info_file(
            os.path.join(tmpdir, info_file.string))
        for file in info.files:
            files.append(
                FileStorage(
                    stream=open(
                        os.path.join(tmpdir, file.name), mode='rb'),
                    filename=file.original_name))
        tree = process_files(files)
        map(lambda f: f.close(), files)
        submissions.append((info, tree))
    shutil.rmtree(tmpdir)
    return submissions


def rgetattr(obj, attr):
    """Recursive implementation of getattr

    :param object obj: Some object
    :param str attr: A string identifying some (nested) attribute
    :returns: The requested attribute
    """
    return reduce(getattr, [obj] + attr.split('.'))


def create_csv(objects, attributes, headers=None):
    """Create a csv file from the given objects and attributes.

    :param objects: The objects that will be listed
    :type objects: list of object
    :param attributes: The attributes of each object that will be listed
    :type attributes: list of str
    :param headers: Column headers that will be the first row in the csv file
    :type headers: list of str
    :returns: The path to the csv file
    :rtype: str
    """
    if headers is None:
        headers = attributes

    return create_csv_from_rows([headers] + [[
        str(rgetattr(obj, attr)) for attr in attributes
    ] for obj in objects])


def create_csv_from_rows(rows):
    """Create a csv file from the given rows.

    Rows should be a nested list or other similar iterable like this:
    [[header_1, header_2], [row_1a, row_1b], [row_2a, row_2b]]

    :param rows: The rows that will be used to populate the csv
    :type rows: list of str
    :returns: The path to the csv file
    :rtpe: str
    """
    mode, csv_file = tempfile.mkstemp()
    with open(csv_file, 'w') as csv_output:
        csv_writer = csv.writer(csv_output)
        csv_writer.writerows(rows)
    return csv_file


def remove_tree(tree):
    """Removes all files in the tree.

    This removes all files in a tree as described by
    :py:func`rename_directory_structure`

    :param dict tree: Tree of files
    :returns: Nothing
    :rtype None:
    """
    if isinstance(tree, dict):
        for key in tree.keys():
            remove_tree(tree[key])
    elif isinstance(tree, list):
        for item in tree:
            remove_tree(item)
    else:
        os.remove(os.path.join(app.config['UPLOAD_DIR'], tree[1]))

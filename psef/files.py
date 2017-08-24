"""
This module is used for file IO and handling and provides functions for
extracting and abstracting the structures of directories and archives.
"""

import os
import re
import csv
import uuid
import shutil
import typing as t
import tempfile
from functools import reduce

import archive
from werkzeug.utils import secure_filename
from mypy_extensions import NoReturn
from werkzeug.datastructures import FileStorage

import psef.models as models
import psef.helpers as helpers
from psef import app, blackboard
from psef.errors import APICodes, APIException

_known_archive_extensions = tuple(archive.extension_map.keys())

# Gestolen van Erik Kooistra
_bb_txt_format = re.compile(
    r"(?P<assignment_name>.+)_(?P<student_id>\d+)_attempt_"
    r"(?P<datetime>\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}).txt"
)

FileTree = t.MutableMapping[str, t.Union[int, str, t.MutableSequence[t.Any]]]

# PEP 484 does not support recursive types (because why design a new type
# system that has remotely advanced features, see Go why you should never do
# such a thing) we can't actually define a tree in types, however with enough
# nesting we should come close enough (tm).
if t.TYPE_CHECKING and not hasattr(t, 'SPHINX'):  # pragma: no cover
    _ExtractFileTreeValue0 = t.MutableSequence[
        t.Union[t.Tuple[str, str], t.MutableMapping[str, t.Any]]
    ]
    _ExtractFileTreeValue1 = t.MutableSequence[t.Union[
        t.Tuple[str, str], t.MutableMapping[str, _ExtractFileTreeValue0]
    ]]
    _ExtractFileTreeValue2 = t.MutableSequence[t.Union[
        t.Tuple[str, str], t.MutableMapping[str, _ExtractFileTreeValue1]
    ]]
    _ExtractFileTreeValueN = t.MutableSequence[t.Union[
        t.Tuple[str, str], t.MutableMapping[str, _ExtractFileTreeValue2]
    ]]
    ExtractFileTreeValue = t.MutableSequence[t.Union[
        t.Tuple[str, str], t.MutableMapping[str, _ExtractFileTreeValueN]
    ]]
else:
    ExtractFileTreeValue = t.MutableSequence[
        t.Union[t.Tuple[str, str], t.MutableMapping[str, t.Any]]
    ]
ExtractFileTree = t.MutableMapping[str, ExtractFileTreeValue]


def get_stat_information(file: models.File) -> t.Mapping[str, t.Any]:
    """Get stat information for a given :class:`.models.File`

    The resulting object will look like this:

    .. code:: python

        {
            'is_directory': bool, # Is the given file a directory
            'modification_date':  int, # When was the file last modified, as
                                       # unix timestamp in utc time.
            'size': int, # The size on disk of the file or 0 if the file is a
                         # directory.
            'id': int, # The id of the given file.
        }

    :param file: The file to get the stat information for.
    :returns: The information as described above.
    """
    mod_date = file.modification_date
    filename = file.get_diskname() if file.is_directory else ''
    size = os.stat(filename).st_size if file.is_directory else 0

    return {
        'is_directory': file.is_directory,
        'modification_date': round(mod_date.timestamp()),
        'size': size,
        'id': file.id,
    }


def get_binary_contents(file: models.File) -> bytes:
    """Get the binary contents of a given :class:`.models.File`.

    :param file: The file object to read.
    :returns: The contents of the file
    """

    filename = file.get_diskname()
    with open(filename, 'rb') as codefile:
        return codefile.read()


def get_file_contents(code: models.File) -> str:
    """Get the contents of the given :class:`.models.File`.

    :param code: The file object to read.
    :returns: The contents of the file with newlines.
    """

    def _raise_err(msg: str='') -> NoReturn:
        raise APIException(
            f'Cannot display this file{msg}!',
            'The selected file with id {} was not UTF-8'.format(code.id),
            APICodes.OBJECT_WRONG_TYPE, 400
        )

    try:
        if code.is_directory:
            _raise_err(' as it is a directory')
        filename = code.get_diskname()
        if os.path.islink(filename):
            raise APIException(
                f'This file is a symlink to `{os.readlink(filename)}`.',
                'The file {} is a symlink'.format(code.id),
                APICodes.INVALID_STATE, 410
            )
        with open(filename, 'r', encoding='utf-8') as codefile:
            return codefile.read()
    except UnicodeDecodeError:
        _raise_err()


def restore_directory_structure(
    code: models.File,
    parent: str,
    exclude: models.FileOwner=models.FileOwner.teacher
) -> FileTree:
    """Restores the directory structure recursively for a code submission (a
    :class:`.models.Work`).

    The directory structure is returned like this:

    .. code:: python

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

    :param code: A file
    :param parent: Path to parent directory
    :param exclude: The file owner to exclude.
    :returns: A tree as described
    """
    out = os.path.join(parent, code.get_filename())
    if code.is_directory:
        os.mkdir(out)
        children = code.children.filter(models.File.fileowner != exclude).all()
        children = [
            restore_directory_structure(child, out, exclude)
            for child in children
        ]
        return {
            "name": code.get_filename(),
            "id": code.id,
            "entries": children,
        }
    else:  # this is a file
        shutil.copyfile(code.get_diskname(), out, follow_symlinks=False)
        return {"name": code.get_filename(), "id": code.id}


def rename_directory_structure(rootdir: str) -> ExtractFileTree:
    """Creates a nested dictionary that represents the folder structure of
    rootdir.

    A tree like:

    - dir1
        - dir 2
            - file 1
            - file 2
        - file 3

    will be moved to files given by :py:func:`random_file_path` and the object
    returned will represent the file structure, which will be something like
    this:

    .. code:: python

      {
          'dir1': {
              [
                  'dir 2':{
                      [
                          ('file 1', 'new_name'),
                          ('file 2', 'new_name2')
                      ]
                  },
                  ('file 3', 'new_name3')
              ]
          }
      }

    :param str rootdir: The root directory to rename, files will not be removed
    :returns: The tree as described above
    :rtype: dict[str, dict[str, list[dict or tuple[str, str,]]]]
    """
    dir = {}  # type: t.MutableMapping[str, t.Any]
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    for path, dirs, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)

        # `reduce` returns a reference within `dir` so `dir` will change on the
        # next two lines.
        parent = reduce(dict.get, folders[:-1], dir)
        parent[folders[-1]] = subdir

    def convert_to_lists(name: str,
                         dirs: t.Mapping[str, t.Any]) -> t.Sequence[t.Any]:
        res = [
        ]  # type: t.List[t.Union[t.Tuple[str, str], t.Mapping[str, t.Any]]]
        for key, value in dirs.items():
            if value is None:
                new_name, filename = random_file_path()
                # type filename: str
                shutil.move(os.path.join(name, key), new_name)
                res.append((key, filename))
            else:
                res.append(
                    {
                        key: convert_to_lists(os.path.join(name, key), value)
                    }
                )
        return res

    result_lists = convert_to_lists(rootdir[:start], dir)
    assert len(result_lists) == 1
    return result_lists[0]


def is_archive(file: FileStorage) -> bool:
    """Checks whether the file ends with a known archive file extension.

    File extensions are known if they are recognized by the archive module.

    :param file: Some file
    :returns: True if the file has a known extension
    """
    return file.filename.endswith(_known_archive_extensions)


def extract_to_temp(file: FileStorage) -> str:
    """Extracts the contents of file into a temporary directory.

    :param file: The archive to extract.
    :returns: The pathname of the new temporary directory.
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


def extract(file: FileStorage) -> ExtractFileTree:
    """Extracts all files in archive with random name to uploads folder.

    :param werkzeug.datastructures.FileStorage file: The file to extract.
    :returns: A file tree as generated by
              :py:func:`rename_directory_structure`.
    :rtype: dict
    """
    tmpdir = extract_to_temp(file)
    rootdir = tmpdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    try:
        res = rename_directory_structure(tmpdir)[tmpdir[start:]]
        filename: str = file.filename.split('.')[0]
        if len(res) > 1:
            return {filename: res if isinstance(res, list) else [res]}
        elif not isinstance(res[0], t.MutableMapping):
            return {filename: res}
        else:
            return res[0]
    finally:
        shutil.rmtree(tmpdir)


def random_file_path(config_key: str='UPLOAD_DIR') -> t.Tuple[str, str]:
    """Generates a new random file path in the upload directory.

    :param config_key: The key to use to find the basedir of the random file
        path from the ``app.config`` store.
    :returns: The name of the new file and a path to that file
    """
    while True:
        name = str(uuid.uuid4())
        candidate = os.path.join(app.config[config_key], name)
        if os.path.exists(candidate):  # pragma: no cover
            continue
        else:
            break
    return candidate, name


def dehead_filetree(tree: ExtractFileTree) -> ExtractFileTree:
    """Remove the head of the given filetree while preserving the old head
    name.

    So a tree ``{1: [2: [3: [4: [f1, f2]]]}`` will be converted to
    ``{1: [f1, f2]}``.

    :param dict tree: The file tree as generated by :py:func:`extract`.
    :returns: The same tree but deheaded as described.
    :rtype: dict
    """
    assert len(tree) == 1
    head_node = list(tree.keys())[0]
    head = tree[head_node]

    while (
        isinstance(head, t.MutableSequence) and len(head) == 1 and
        isinstance(head[0], t.MutableMapping) and len(head[0]) == 1
    ):
        head = list(head[0].values())[0]

    tree[head_node] = head

    return tree


def process_files(files: t.MutableSequence[FileStorage]) -> ExtractFileTree:
    """Process the given files by extracting, moving and saving their tree
    structure.

    :param files: The files to move and extract
    :rtype: list of FileStorage
    :returns: The tree of the files as is described by
              :py:func:`rename_directory_structure`
    :rtype: dict
    """
    tree = {}  # type: ExtractFileTree
    if len(files) > 1 or not is_archive(files[0]):
        res = []  # type: t.List[t.Union[ExtractFileTree, t.Tuple[str, str]]]
        for file in files:
            if is_archive(file):
                res.append(extract(file))
            else:
                new_file_name, filename = random_file_path()
                res.append((file.filename, filename))
                file.save(new_file_name)
        tree = {'top': res}
    else:
        tree = extract(files[0])

    return dehead_filetree(tree)


def process_blackboard_zip(
    blackboard_zip: FileStorage
) -> t.MutableSequence[t.Tuple[blackboard.SubmissionInfo, ExtractFileTree]]:
    """Process the given :py:mod:`.blackboard` zip file.

    This is done by extracting, moving and saving the tree structure of each
    submission.

    :param file: The blackboard gradebook to import
    :returns: List of tuples (BBInfo, tree)
    """
    tmpdir = extract_to_temp(blackboard_zip)
    try:
        info_files = filter(
            None, (_bb_txt_format.match(f) for f in os.listdir(tmpdir))
        )
        submissions = []
        for info_file in info_files:
            files = []
            info = blackboard.parse_info_file(
                os.path.join(tmpdir, info_file.string)
            )
            for blackboard_file in info.files:
                files.append(
                    FileStorage(
                        stream=open(
                            os.path.join(tmpdir, blackboard_file.name),
                            mode='rb'
                        ),
                        filename=blackboard_file.original_name
                    )
                )
            tree = process_files(files)
            map(lambda f: f.close(), files)
            submissions.append((info, tree))
        if not submissions:
            raise ValueError
    finally:
        shutil.rmtree(tmpdir)
    return submissions

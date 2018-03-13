"""
This module is used for file IO and handling and provides functions for
extracting and abstracting the structures of directories and archives.

:license: AGPLv3, see LICENSE for details.
"""

import io
import os
import re
import enum
import uuid
import shutil
import typing as t
import tempfile
from functools import reduce

import archive
import mypy_extensions
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

import psef.models as models
from psef import app, blackboard
from psef.errors import APICodes, APIException
from psef.ignore import IgnoreFilterManager

_KNOWN_ARCHIVE_EXTENSIONS = tuple(archive.extension_map.keys())

# Gestolen van Erik Kooistra
_BB_TXT_FORMAT = re.compile(
    r"(?P<assignment_name>.+)_(?P<student_id>.+?)_attempt_"
    r"(?P<datetime>\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}).txt"
)
FileTreeBase = mypy_extensions.TypedDict(  # pylint: disable=invalid-name
    'FileTreeBase',
    {
        'name': str,
        'id': int,
    }
)


def init_app(_: t.Any) -> None:
    pass


# This is valid, see https://github.com/PyCQA/pylint/issues/1927
class FileTree(  # pylint: disable=inherit-non-class,missing-docstring
    FileTreeBase,
    total=False,
):
    entries: t.MutableSequence[t.Any]


# PEP 484 does not support recursive types (because why design a new type
# system that has remotely advanced features, see Go why you should never do
# such a thing) we can't actually define a tree in types, however with enough
# nesting we should come close enough (tm).
if t.TYPE_CHECKING and not hasattr(t, 'SPHINX'):  # pragma: no cover
    # pylint: disable=invalid-name
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
    ExtractFileTreeValue = t.MutableSequence[  # pylint: disable=invalid-name
        t.Union[t.Tuple[str, str], t.MutableMapping[str, t.Any]]
    ]
ExtractFileTree = t.MutableMapping[str, ExtractFileTreeValue]  # pylint: disable=invalid-name


class IgnoredFilesException(APIException):
    """The exception used when a permission check fails.
    """

    def __init__(
        self,
        invalid_files: t.List[t.Tuple[str, str]],
    ) -> None:
        self.invalid_files = invalid_files
        super(IgnoredFilesException, self).__init__(
            message='The archive contains message that are ignored',
            description='Some messages in the archive matched the ignore file',
            api_code=APICodes.INVALID_FILE_IN_ARCHIVE,
            status_code=400,
            invalid_files=invalid_files
        )


@enum.unique
class IgnoreHandling(enum.IntEnum):
    """Describes what to do with ignored files..

    :param keep: Nothing should be done with ignored files, simply keep them.
    :param delete: Ignored files should be deleted from the resulting
        directory.
    :param error: An exception should be raised when ignored files are found in
        the given archive.
    """

    keep: int = 1
    delete: int = 2
    error: int = 3


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
    filename = None if file.is_directory else file.get_diskname()
    size = 0 if file.is_directory else os.stat(filename).st_size

    return {
        'is_directory': file.is_directory,
        'modification_date': round(mod_date.timestamp()),
        'size': size,
        'id': file.id,
    }


def get_file_contents(code: models.File) -> bytes:
    """Get the contents of the given :class:`.models.File`.

    :param code: The file object to read.
    :returns: The contents of the file with newlines.
    """
    if code.is_directory:
        raise APIException(
            'Cannot display this file as it is a directory.',
            f'The selected file with id {code.id} is a directory.',
            APICodes.OBJECT_WRONG_TYPE, 400
        )

    filename = code.get_diskname()
    if os.path.islink(filename):
        raise APIException(
            f'This file is a symlink to `{os.readlink(filename)}`.',
            'The file {} is a symlink'.format(code.id), APICodes.INVALID_STATE,
            410
        )
    with open(filename, 'rb') as codefile:
        return codefile.read()


def restore_directory_structure(
    code: models.File,
    parent: str,
    exclude: models.FileOwner = models.FileOwner.teacher
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
    out = os.path.join(parent, code.name)
    if code.is_directory:
        os.mkdir(out)
        children = code.children.filter(models.File.fileowner != exclude).all()
        subtree: t.List[FileTree] = [
            restore_directory_structure(child, out, exclude)
            for child in children
        ]
        return {
            "name": code.name,
            "id": code.id,
            "entries": subtree,
        }
    else:  # this is a file
        shutil.copyfile(code.get_diskname(), out, follow_symlinks=False)
        return {"name": code.name, "id": code.id}


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
    directory = {}  # type: t.MutableMapping[str, t.Any]
    rootdir = rootdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    for path, _, files in os.walk(rootdir):
        folders = path[start:].split(os.sep)
        subdir = dict.fromkeys(files)

        # `reduce` returns a reference within `directory` so `directory` will
        # change on the next two lines.
        parent = reduce(dict.get, folders[:-1], directory)
        parent[folders[-1]] = subdir

    def __to_lists(name: str,
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
                        key: __to_lists(os.path.join(name, key), value),
                    }
                )
        return res

    result_lists = __to_lists(rootdir[:start], directory)
    assert len(result_lists) == 1
    return result_lists[0]


def is_archive(file: FileStorage) -> bool:
    """Checks whether the file ends with a known archive file extension.

    File extensions are known if they are recognized by the archive module.

    :param file: Some file
    :returns: True if the file has a known extension
    """
    return file.filename.endswith(_KNOWN_ARCHIVE_EXTENSIONS)


def extract_to_temp(
    file: FileStorage,
    ignore_filter: IgnoreFilterManager,
    handle_ignore: IgnoreHandling = IgnoreHandling.keep
) -> str:
    """Extracts the contents of file into a temporary directory.

    :param file: The archive to extract.
    :param ignore_filter: The files and directories that should be ignored.
    :param handle_ignore: Determines how ignored files should be handled.
    :returns: The pathname of the new temporary directory.
    """
    tmpfd, tmparchive = tempfile.mkstemp()

    try:
        os.remove(tmparchive)
        tmparchive += os.path.basename(
            secure_filename('archive_' + file.filename)
        )
        tmpdir = tempfile.mkdtemp()
        file.save(tmparchive)

        if handle_ignore == IgnoreHandling.error:
            arch = archive.Archive(tmparchive)
            wrong_files = ignore_filter.get_ignored_files_in_archive(arch)
            if wrong_files:
                raise IgnoredFilesException(invalid_files=wrong_files)
            arch.extract(to_path=tmpdir, method='safe')
        else:
            archive.extract(tmparchive, to_path=tmpdir, method='safe')
            if handle_ignore == IgnoreHandling.delete:
                ignore_filter.delete_from_dir(tmpdir)
    finally:
        os.close(tmpfd)
        os.remove(tmparchive)

    return tmpdir


def extract(
    file: FileStorage,
    ignore_filter: IgnoreFilterManager = None,
    handle_ignore: IgnoreHandling = IgnoreHandling.keep
) -> t.Optional[ExtractFileTree]:
    """Extracts all files in archive with random name to uploads folder.

    :param werkzeug.datastructures.FileStorage file: The file to extract.
    :param ignore_filter: What files should be ignored in the given archive.
        This can only be None when ``handle_ignore`` is
        ``IgnoreHandling.keep``.
    :param handle_ignore: How should ignored file be handled.
    :returns: A file tree as generated by
        :py:func:`rename_directory_structure`.
    """
    if handle_ignore == IgnoreHandling.keep and ignore_filter is None:
        ignore_filter = IgnoreFilterManager([])
    elif ignore_filter is None:  # pragma: no cover
        raise ValueError

    tmpdir = extract_to_temp(
        file,
        ignore_filter,
        handle_ignore,
    )
    rootdir = tmpdir.rstrip(os.sep)
    start = rootdir.rfind(os.sep) + 1
    try:
        res = rename_directory_structure(tmpdir)[tmpdir[start:]]
        filename: str = file.filename.split('.')[0]
        if not res:
            return None
        elif len(res) > 1:
            return {filename: res if isinstance(res, list) else [res]}
        elif not isinstance(res[0], t.MutableMapping):
            return {filename: res}
        else:
            return res[0]
    finally:
        shutil.rmtree(tmpdir)


def random_file_path(config_key: str = 'UPLOAD_DIR') -> t.Tuple[str, str]:
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


def process_files(
    files: t.MutableSequence[FileStorage],
    force_txt: bool = False,
    ignore_filter: IgnoreFilterManager = None,
    handle_ignore: IgnoreHandling = IgnoreHandling.keep,
) -> ExtractFileTree:
    """Process the given files by extracting, moving and saving their tree
    structure.

    :param files: The files to move and extract
    :param force_txt: Do not extract archive and force all files to be
        considered to be plain text.
    :param ignore_filter: The files and directories that should be ignored.
    :param handle_ignore: Determines how ignored files should be handled.
    :returns: The tree of the files as is described by
              :py:func:`rename_directory_structure`
    """

    def consider_archive(f: FileStorage) -> bool:
        return not force_txt and is_archive(f)

    def raise_error() -> None:
        raise APIException(
            "All files are ignored by a rule in the assignment's ignore file",
            'No files were in the given archive after filtering.',
            APICodes.NO_FILES_SUBMITTED,
            400,
        )

    tree = {}  # type: ExtractFileTree
    if len(files) > 1 or not consider_archive(files[0]):
        res = []  # type: t.List[t.Union[ExtractFileTree, t.Tuple[str, str]]]
        for file in files:
            if consider_archive(file):
                new = extract(file, ignore_filter, handle_ignore)
                if new:
                    res.append(new)
            else:
                if handle_ignore != IgnoreHandling.keep:
                    is_ignored, line = ignore_filter.is_ignored(file.name)

                    if not is_ignored:
                        pass
                    elif handle_ignore == IgnoreHandling.delete:
                        continue
                    elif handle_ignore == IgnoreHandling.error:
                        raise IgnoredFilesException(
                            invalid_files=[(file.filename, line)]
                        )

                new_file_name, filename = random_file_path()
                res.append((file.filename, filename))
                file.save(new_file_name)
        if not res:
            raise_error()
        tree = {'top': res}
    else:
        tree = extract(files[0], ignore_filter, handle_ignore)
        if not tree:
            raise_error()

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

    def __get_files(info: blackboard.SubmissionInfo) -> t.List[FileStorage]:
        files = []
        for blackboard_file in info.files:
            if isinstance(blackboard_file, blackboard.FileInfo):
                name = blackboard_file.original_name
                stream = open(
                    os.path.join(tmpdir, blackboard_file.name), mode='rb'
                )
            else:
                name = blackboard_file[0]
                stream = io.BytesIO(blackboard_file[1])

            if name == '__WARNING__':
                name = '__WARNING__ (User)'

            files.append(FileStorage(stream=stream, filename=name))
        return files

    tmpdir = extract_to_temp(
        blackboard_zip,
        IgnoreFilterManager([]),
        IgnoreHandling.keep,
    )
    try:
        info_files = filter(
            None, (_BB_TXT_FORMAT.match(f) for f in os.listdir(tmpdir))
        )
        submissions = []
        for info_file in info_files:
            info = blackboard.parse_info_file(
                os.path.join(tmpdir, info_file.string)
            )

            try:
                tree = process_files(__get_files(info))
            # TODO: We catch all exceptions, this should probably be narrowed
            # down, however finding all exception types is difficult.
            except Exception:  # pylint: disable=broad-except
                files = __get_files(info)
                files.append(
                    FileStorage(
                        stream=io.BytesIO(
                            b'Some files could not be extracted!',
                        ),
                        filename='__WARNING__'
                    )
                )
                tree = process_files(files, force_txt=True)

            submissions.append((info, tree))
        if not submissions:
            raise ValueError
    finally:
        shutil.rmtree(tmpdir)
    return submissions


def split_path(path: str) -> t.Tuple[t.Sequence[str], bool]:
    """Split a path into an array of parts of a path.

    This functions splits a forward slash separated path into an sequence of
    the directories of this path. If the given path ends with a '/' it returns
    that the given path ends with an directory, otherwise the last part is a
    file, this information is returned as the last part of the returned tuple.

    The given path may contain multiple consecutive forward slashes, these are
    interpreted as a single slash. A leading forward slash is also optional.

    :param path: The forward slash separated path to split.
    :returns: A tuple where the first item is the splitted path and the second
        item is a boolean indicating if the last item of the given path was a
        directory.
    """
    is_dir = path[-1] == '/'

    patharr = [item for item in path.split('/') if item]

    return patharr, is_dir

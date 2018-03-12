"""gitignore files.

For details for the matching rules, see https://git-scm.com/docs/gitignore.

This code is almost copied verbatim from dulwich.

:license: AGPLv3, see LICENSE for details.
"""

import re
import sys
import shutil
import typing as t
import os.path
import tarfile

import archive


def _translate_segment(segment: str) -> str:
    """Translate the given gitignore segment to regex segment.

    :param segment: The segment to translate.
    :returns: A valid regex string.
    """
    if segment == "*":
        return '[^/]+'

    res = []
    i, n = 0, len(segment)
    while i < n:
        c = segment[i:i + 1]
        i = i + 1
        if c == '*':
            res.append('[^/]*')
        elif c == '?':
            res.append('.')
        elif c == '[':
            j = i
            if j < n and segment[j:j + 1] == '!':
                j = j + 1
            if j < n and segment[j:j + 1] == ']':
                j = j + 1
            while j < n and segment[j:j + 1] != ']':
                j = j + 1
            if j >= n:
                res.append('\\[')
            else:
                stuff = segment[i:j].replace('\\', '\\\\')
                i = j + 1
                if stuff.startswith('!'):
                    stuff = '^' + stuff[1:]
                res.append('[' + stuff + ']')
        else:
            res.append(re.escape(c))

    return ''.join(res)


def translate(pat: str) -> str:
    """Translate a shell PATTERN to a regular expression.

    There is no way to quote meta-characters.

    Originally copied from fnmatch in Python 2.7, but modified for Dulwich
    to cope with features in Git ignore patterns.
    """

    res = '(?ms)'

    if '/' not in pat[:-1]:
        # If there's no slash, this is a filename-based match
        res += '(.*/)?'

    if pat.startswith('**/'):
        # Leading **/
        pat = pat[2:]
        res += '(.*/)?'

    if pat.startswith('/'):
        pat = pat[1:]

    for i, segment in enumerate(pat.split('/')):
        if segment == '**':
            res += '(/.*)?'
        else:
            res += (
                (re.escape('/')
                 if i > 0 else '') + _translate_segment(segment)
            )

    if not pat.endswith('/'):
        res += '/?'

    return res + '\Z'


def read_ignore_patterns(f: t.Iterable[str]) -> t.Iterable[t.Tuple[str, str]]:
    """Read a git ignore file.

    :param f: Iterable to read from
    :return: List of patterns
    """

    for line in f:
        line = line.rstrip('\r\n')
        original_line = line

        # Ignore blank lines, they're used for readability.
        if not line:
            continue

        if line.startswith('#'):
            # Comment
            continue

        # Trailing spaces are ignored unless they are quoted with a backslash.
        while line.endswith(' ') and not line.endswith('\\ '):
            line = line[:-1]
        line = line.replace('\\ ', ' ')

        yield line, original_line


class Pattern:
    """A single ignore pattern."""

    def __init__(self, pattern: str, orig_line: str) -> None:
        self.pattern = pattern
        self.original_line = orig_line
        if pattern[0:1] == '!':
            self.is_exclude = False
            pattern = pattern[1:]
        else:
            if pattern[0:1] == '\\':
                pattern = pattern[1:]
            self.is_exclude = True
        flags = 0
        self._re = re.compile(translate(pattern), flags)

    def match(self, path: str) -> bool:
        """Try to match a path against this ignore pattern.

        :param path: Path to match (relative to ignore location)
        :return: boolean
        """
        return bool(self._re.match(path))


class IgnoreFilter:
    def __init__(self, patterns: t.Iterable[str]) -> None:
        self._patterns: t.List[Pattern] = []
        for pattern, orig_line in read_ignore_patterns(patterns):
            self.append_pattern(pattern, orig_line)

    def append_pattern(self, pattern: str, orig_line: str) -> None:
        """Add a pattern to the set."""
        self._patterns.append(Pattern(pattern, orig_line))

    def find_matching(self, path: str) -> t.Iterable[Pattern]:
        """Yield all matching patterns for path.

        :param path: Path to match
        :return: Iterator over  iterators
        """
        for pattern in self._patterns:
            if pattern.match(path):
                yield pattern


class IgnoreFilterManager:
    """Ignore file manager."""

    def __init__(
        self,
        global_filters: t.Sequence[str],
    ) -> None:
        self._filter = IgnoreFilter(global_filters)

    def find_matching(self, path: str) -> t.Iterable[Pattern]:
        """Find matching patterns for path.
        Stops after the first ignore file with matches.
        :param path: Path to check
        :return: Iterator over Pattern instances
        """
        if os.path.isabs(path):  # pragma: no cover
            raise ValueError('%s is an absolute path' % path)

        parts = path.split('/')

        for i in range(len(parts) + 1):
            relpath = '/'.join(parts[:i])

            if i < len(parts):
                # Paths leading up to the final part are all directories,
                # so need a trailing slash.
                relpath += '/'
            matches = list(self._filter.find_matching(relpath))
            if matches:
                return iter(matches)
        return iter([])

    def is_ignored(self,
                   path: str) -> t.Tuple[t.Optional[bool], t.Optional[str]]:
        """Check whether a path is explicitly included or excluded in ignores.
        :param path: Path to check
        :return: None if the file is not mentioned, True if it is included,
            False if it is explicitly excluded.
        """
        matches = list(self.find_matching(path))
        if matches:
            return matches[-1].is_exclude, matches[-1].original_line

        return None, None

    def delete_from_dir(self, top: str) -> None:
        """Delete all files from the given archive.

        .. warning:: This mutates the given directory.

        :param top: The top directory of the archive to traverse and delete
            files from.
        :returns: Nothing.
        """
        for root, dirs, files in os.walk(top):
            new_root = root[len(top) + 1:]

            for sub_dir in dirs:
                sub_dir = os.path.join(new_root, sub_dir)
                if sub_dir and self.is_ignored(sub_dir + '/')[0]:
                    to_remove = os.path.join(top, sub_dir)
                    assert to_remove.startswith(top)
                    shutil.rmtree(to_remove)

            for sub_file in files:
                sub_file = os.path.join(new_root, sub_file)
                if sub_file and self.is_ignored(sub_file)[0]:
                    to_remove = os.path.join(top, sub_file)
                    assert to_remove.startswith(top)
                    os.unlink(to_remove)

    def get_ignored_files_in_archive(
        self,
        arch_wrapper: archive.Archive,
    ) -> t.List[t.Tuple[str, str]]:
        """Get all ignored files in the given archive.

        :param arch: The archive to check for ignored files.
        :returns: All files that should be ignored.
        """
        arch = arch_wrapper._archive

        def get_names() -> t.Iterable[str]:
            if isinstance(arch, archive.TarArchive):
                info: tarfile.TarInfo
                for info in arch._archive.getmembers():
                    if info.isdir():
                        yield info.name + '/'
                    else:
                        yield info.name
            elif isinstance(arch, archive.ZipArchive):
                seen_dirs = set()
                for f in arch.filenames():
                    first = True
                    while f and f not in seen_dirs:
                        f, tail = os.path.split(f)
                        p = (f + '/' if f else '') + tail
                        # We add p without trailing slash as this is easier to
                        # search for
                        seen_dirs.add(p)
                        if not first:
                            p += '/'
                        yield p

                        first = False
            else:  # pragma: no cover
                # This else is not possible as our archive package only
                # supports tar.gz and zip files. However it doesn't hurt to
                # have it here.
                yield from arch.filenames()

        wrong_files = []
        for name in get_names():
            is_ignored, line = self.is_ignored(name)
            if is_ignored:
                wrong_files.append((name, line))
        return wrong_files

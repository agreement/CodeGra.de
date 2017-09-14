#!/usr/bin/env python3
"""
This module implements the parsing of blackboard gradebook info files.

:license: AGPLv3, see LICENSE for details.
"""
import re
import mmap
import typing as t
import datetime

from dateutil import parser as dateparser

_txt_fmt = re.compile(
    r"Name: (?P<name>.+) \((?P<id>[0-9]+)\)\n"
    r"Assignment: (?P<assignment>.+)\n"
    r"Date Submitted: (?P<datetime>.+)\n"
    r"Current Grade: *(?P<grade>([0-9.]*|[^\n]*))\n\n"
    r"Submission Field:\n(?P<text>(.*\n)+)\n"
    r"Comments:\n(?P<comment>(.*\n)+)\n"
    r"Files:\n"
    r"(?P<files>(.+\n.+\n)+)\n?".encode('utf-8')
)

_txt_files_fmt = re.compile(
    r"\tOriginal filename: (.+)\n"
    r"\tFilename: (.+)\n"
)


class FileInfo(
    t.NamedTuple('FileInfo', [
        ('original_name', str),
        ('name', str),
    ])
):
    """A NamedTuple holding information about a specific file.

    :param original_name: The name provided by the user.
    :param name: The name as stored in the blackboard gradebook.
    """


class SubmissionInfo(
    t.NamedTuple(
        'SubmissionInfo', [
            ('student_name', str),
            ('student_id', str),
            ('assignment_name', str),
            ('created_at', datetime.datetime),
            ('grade', t.Optional[float]),
            ('text', str),
            ('comment', str),
            ('files', t.MutableSequence[FileInfo]),
        ]
    )
):
    """A NamedTuple holding information about a submission from a blackboard
    zip.

    :param student_name: The name of the student.
    :param student_id: The id of the student in the system of the university.
    :param assignment_name: Name of the assignment.
    :param created_at: The datetime when the submission was made.
    :param grade: The current grade of the submission.
    :param text: The html text submission of the student.
    :param comment: Comment included by student.
    :param files: The files submitted by the user.
    """


def parse_info_file(file: str) -> SubmissionInfo:
    """Parses a blackboard gradebook .txt file.

    :param file: Path to the file
    :returns: The parsed information
    :rtype: SubmissionInfo
    """
    # _txt_fmt is a object gotten from `re.compile`
    with open(file, 'r+') as f:
        with mmap.mmap(f.fileno(), 0) as data:
            # casting here is wrong, however see
            # https://github.com/python/typeshed/issues/1467
            match = _txt_fmt.match(t.cast(bytes, data))

            try:
                grade = float(match.group('grade'))
            except ValueError:
                grade = None

            info = SubmissionInfo(
                student_name=match.group('name').decode('utf-8'),
                student_id=match.group('id').decode('utf-8'),
                assignment_name=match.group('assignment').decode('utf-8'),
                created_at=dateparser.parse(
                    match.group('datetime').decode('utf-8')
                    .replace(" o'clock", "")
                ),
                grade=grade,
                text=match.group('text').decode('utf-8').rstrip(),
                comment=match.group('comment').decode('utf-8').rstrip(),
                files=[
                    FileInfo(org, cur)
                    for org, cur in _txt_files_fmt.
                    findall(match.group('files').decode('utf-8'))
                ]
            )
            return info

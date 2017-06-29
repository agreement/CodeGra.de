#!/usr/bin/env python3
"""
This module implements the parsing of blackboard gradebook info files.
"""
import re
import mmap
from collections import namedtuple

from dateutil import parser as dateparser

_txt_fmt = re.compile(r"Name: (?P<name>.+) \((?P<id>[0-9]+)\)\n"
                      r"Assignment: (?P<assignment>.+)\n"
                      r"Date Submitted: (?P<datetime>.+)\n"
                      r"Current Grade: (?P<grade>[0-9.]*)\n\n"
                      r"Submission Field:\n(?P<text>(.*\n)+)\n"
                      r"Comments:\n(?P<comment>(.*\n)+)\n"
                      r"Files:\n"
                      r"(?P<files>(.+\n.+\n)+)\n".encode('utf-8'))

_txt_files_fmt = re.compile(r"\tOriginal filename: (.+)\n"
                            r"\tFilename: (.+)\n")

Info = namedtuple('SubmissionInfo', [
    'student_name', 'student_id', 'assignment_name', 'created_at', 'grade',
    'text', 'comment', 'files'
])
"""A namedtuple holding information about a specific file

.. py:attribute:: student_name
    The name of the student

.. py:attribute:: student_id
    The id of the student in the system of the university

.. py:attribute:: assignment_name
    Name of the assignment

.. py:attribute:: created_at
    The datetime when the submission was made

.. py:attribute:: grade
    The current grade of the submission

.. py:attribute:: text
    The html text submission of the student

.. py:attribute:: comment
    Comment included by student

.. py:attribute:: files
    The files submitted by the user as list of :class: SubmissionFileInfo
"""


FileInfo = namedtuple('SubmissionFileInfo', ['original_name', 'name'])
"""A namedtuple holding information about a specific file.

.. py:attribute:: original_name
    The name provided by the user

.. py:attribute:: name
    The name as stored in the blackboard gradebook
"""


def parse_info_file(file):
    """Parses a blackboard gradebook .txt file.

    :param str file: Path to the file
    :returns: The parsed information
    :rtype: SubmissionInfo
    """
    with open(file, 'r+') as f:
        data = mmap.mmap(f.fileno(), 0)
        match = _txt_fmt.match(data)
        info = Info(
            student_name=match.group('name').decode('utf-8'),
            student_id=int(match.group('id')),
            assignment_name=match.group('assignment').decode('utf-8'),
            created_at=dateparser.parse(
                match.group('datetime').decode('utf-8').replace(
                    " o'clock", "")),
            grade=float(match.group('grade')),
            text=match.group('text').decode('utf-8').rstrip(),
            comment=match.group('comment').decode('utf-8').rstrip(),
            files=[
                FileInfo(org, cur)
                for org, cur in _txt_files_fmt.findall(
                    match.group('files').decode('utf-8'))
            ])
        return info

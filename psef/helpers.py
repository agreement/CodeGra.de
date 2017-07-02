#!/usr/bin/env python3
"""
This module implements generic helpers and convenience functions.
"""
import os
import json
from functools import reduce

from flask import Flask, g, render_template


def get_all_subclasses(cls):
    """Returns all subclasses of the given class.

    Stolen from:
    https://stackoverflow.com/questions/3862310/how-can-i-find-all-subclasses-of-a-class-given-its-name

    :param object cls: The parent class
    :returns: A list of all subclasses
    :rtype: list of object
    """
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def get_request_start_time():
    """Return the start time of the current request.

    :returns: The time as returned by the python time module.
    :rtype: float
    """
    return g.request_start_time


def rgetattr(obj, attr):
    """Recursive implementation of getattr

    :param object obj: Some object
    :param str attr: A string identifying some (nested) attribute
    :returns: The requested attribute
    :rtype: object
    """
    return reduce(getattr, [obj] + attr.split('.'))

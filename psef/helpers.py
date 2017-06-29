#!/usr/bin/env python3
"""
This module implements generic helpers and convenience functions.
"""
import os
import json

from flask import Flask, g, render_template


def get_all_subclasses(cls):
    """
    Stolen from:
    https://stackoverflow.com/questions/3862310/how-can-i-find-all-subclasses-of-a-class-given-its-name
    """
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


def get_request_start_time():
    """
    Return the start time of the current request.

    :returns: The time as returned by the python time module.
    :rtype: float
    """
    return g.request_start_time

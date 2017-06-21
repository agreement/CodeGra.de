# -*- py-isort-options: '("-sg *"); -*-
from flask import Blueprint

api = Blueprint('api', __name__)

from . import (code, login, courses, linters, snippets, assignments,
               permissions, submissions, updateusers)

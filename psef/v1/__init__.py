from flask import Blueprint

api = Blueprint('api', __name__)
from . import (assignments, binary, code, courses, files, linters, login,
               logout, permissions, snippets, submissions, updateusers)
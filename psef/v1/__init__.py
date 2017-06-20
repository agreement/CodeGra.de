from flask import Blueprint

api = Blueprint('api', __name__)
from . import assignments, comments, files, linters, login, logout, permissions, snippets, submissions, updateusers
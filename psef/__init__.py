# -*- py-isort-options: '("-sg *"); -*-
# Import flask and template operators
from flask import Flask, render_template, g
import datetime
import json
from flask_login import LoginManager
import os
import logging

import gevent.monkey

gevent.monkey.patch_all()

from logging.handlers import RotatingFileHandler
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configurations
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Define the database object which is imported
# by modules and controllers
db = SQLAlchemy(app)


# Sample HTTP error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.before_request
def set_request_start_time():
    g.request_start_time = datetime.datetime.utcnow()


login_manager = LoginManager()
login_manager.init_app(app)

with open(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)), '..', 'seed_data',
            'lti_lookups.json'), 'r') as f:
    LTI_ROLE_LOOKUPS = json.load(f)

import psef.auth
import psef.json
import psef.models
import psef.errors
import psef.files
import psef.lti

# Register blueprint(s)
from .v1 import api as api_v1_blueprint
app.register_blueprint(api_v1_blueprint, url_prefix='/api/v1')


def create_app(config=None):
    if config is not None:
        app.config.update(config)
    return app


login_manager.init_app(app)

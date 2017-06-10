#!/usr/bin/env python3

import os
import json

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

import psef.models as m
from psef import db, app

migrate = Migrate(app, db)
manager = Manager(app)

manager.add_command('db', MigrateCommand)


@manager.command
def seed():
    with open('./seed_data/permissions.json', 'r') as perms:
        perms = json.load(perms)
        for perm in perms:
            if m.Permission.query.filter_by(name=perm['name']).first() is None:
                db.session.add(m.Permission(**perm))
    db.session.commit()


if __name__ == '__main__':
    manager.run()

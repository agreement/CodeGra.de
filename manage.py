#!/usr/bin/env python3

import os
import json

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from sqlalchemy_utils import PasswordType

import psef.models as m
from psef import db, app


def render_item(type_, col, autogen_context):
    if type_ == "type" and isinstance(col, PasswordType):
        autogen_context.imports.add("import sqlalchemy_utils")
        return "sqlalchemy_utils.PasswordType"
    else:
        return False

migrate = Migrate(app, db, render_item=render_item)
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


@manager.command
def test_data():
    seed()
    with open('./test_data/courses.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            if m.Course.query.filter_by(name=c['name']).first() is None:
                db.session.add(m.Course(name=c['name']))
    with open('./test_data/roles.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            perms = {
                name: m.Permission.query.filter_by(name=name).first()
                for name in c['permissions']
            }
            r = m.Role.query.filter_by(name=c['name']).first()
            if r is not None:
                r._permissions = perms
                db.session.add(r)
                continue
            else:
                db.session.add(m.Role(name=c['name'], _permissions=perms))
    with open('./test_data/course_roles.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            m.CourseRole.query.filter_by(
                    name=c['name'],
                    course=m.Course.query.filter_by(
                        name=c['course']).first()).delete()
            assert m.Course.query.filter_by(name=c['course']).first()

            perms = {
                name: m.Permission.query.filter_by(name=name).first()
                for name in c['permissions']
            }
            db.session.add(
                m.CourseRole(
                    name=c['name'],
                    _permissions=perms,
                    course=m.Course.query.filter_by(name=c['course']).first()))
    with open('./test_data/assignments.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            m.Assignment.query.filter_by(name=c['name']).delete()
            db.session.add(
                m.Assignment(
                    name=c['name'],
                    description=c['description'],
                    course=m.Course.query.filter_by(name=c['course']).first()))
    with open('./test_data/users.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            m.User.query.filter_by(name=c['name']).delete()
            courses = {
                m.Course.query.filter_by(name=name).first(): role
                for name, role in c['courses'].items()
            }
            perms = {
                course.id: m.CourseRole.query.filter_by(
                    name=name, course_id=course.id).first()
                for course, name in courses.items()
            }
            db.session.add(
                m.User(
                    name=c['name'],
                    courses=perms,
                    email=c['name'].replace(' ', '_').lower() + '@example.com',
                    password=c['name'],
                    role=m.Role.query.filter_by(name=c['role']).first()))
    with open('./test_data/works.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            if m.Work.query.filter(
                m.Work.assignment==m.Assignment.query.filter_by(
                name=c['assignment']).first(),
                m.Work.user==m.User.query.filter_by(
                name=c['user']).first()) is not None:
                continue

            db.session.add(
                m.Work(
                    assignment=m.Assignment.query.filter_by(
                        name=c['assignment']).first(),
                    user=m.User.query.filter_by(name=c['user']).first(),
                    comment=c['comment'],
                    grade=c['grade'],
                    graded=c['graded'],
                    state=c['state'],
                    edit=c['edit']))
    db.session.commit()


if __name__ == '__main__':
    manager.run()

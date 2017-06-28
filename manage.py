#!/usr/bin/env python3

import os
import json
import datetime

from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

import psef.models as m
from psef import db, app
from sqlalchemy_utils import PasswordType


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
            old_perm = m.Permission.query.filter_by(name=perm['name']).first()
            if old_perm is not None:
                old_perm.default_value = perm['default_value']
                old_perm.course_permission = perm['course_permission']
            else:
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
            u = m.CourseRole.query.filter_by(
                name=c['name'],
                course=m.Course.query.filter_by(
                    name=c['course']).first()).first()
            assert m.Course.query.filter_by(name=c['course']).first()

            perms = {
                name: m.Permission.query.filter_by(name=name).first()
                for name in c['permissions']
            }
            if u is not None:
                u.name = c['name']
                u._permissions = perms
                course = m.Course.query.filter_by(name=c['course']).first()
            else:
                db.session.add(
                    m.CourseRole(
                        name=c['name'],
                        _permissions=perms,
                        course=m.Course.query.filter_by(name=c['course'])
                        .first()))
    with open('./test_data/assignments.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            assig = m.Assignment.query.filter_by(name=c['name']).first()
            if assig is None:
                db.session.add(
                    m.Assignment(
                        name=c['name'],
                        deadline=datetime.datetime.utcnow() +
                        datetime.timedelta(days=c['deadline']),
                        state=c['state'],
                        description=c['description'],
                        course=m.Course.query.filter_by(name=c[
                            'course']).first()))
            else:
                assig.description = c['description']
                assig.state = c['state']
                assig.course = m.Course.query.filter_by(
                    name=c['course']).first()
    with open('./test_data/users.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            u = m.User.query.filter_by(name=c['name']).first()
            courses = {
                m.Course.query.filter_by(name=name).first(): role
                for name, role in c['courses'].items()
            }
            perms = {
                course.id: m.CourseRole.query.filter_by(
                    name=name, course_id=course.id).first()
                for course, name in courses.items()
            }
            if u is not None:
                u.name = c['name']
                u.courses = perms
                u.email = c['name'].replace(' ', '_').lower() + '@example.com'
                u.password = c['name']
                u.role = m.Role.query.filter_by(name=c['role']).first()
            else:
                db.session.add(
                    m.User(
                        name=c['name'],
                        courses=perms,
                        email=c['name'].replace(' ', '_').lower() +
                        '@example.com',
                        password=c['name'],
                        role=m.Role.query.filter_by(name=c['role']).first()))
    with open('./test_data/works.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            if m.Work.query.filter_by(
                    assignment=m.Assignment.query.filter_by(
                        name=c['assignment']).first(),
                    user=m.User.query.filter_by(
                        name=c['user']).first()).first() is not None:
                continue

            db.session.add(
                m.Work(
                    assignment=m.Assignment.query.filter_by(
                        name=c['assignment']).first(),
                    user=m.User.query.filter_by(name=c['user']).first(),
                    comment=c['comment'],
                    grade=c['grade'],
                    edit=c['edit']))
    with open('./test_data/snippets.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            user = m.User.query.filter_by(name=c['user']).first()
            snip = m.Snippet.query.filter_by(key=c['key'], user=user).first()
            if snip is None:
                db.session.add(
                    m.Snippet(key=c['key'], value=c['value'], user=user))
            else:
                snip.value = c['value']
    with open('./test_data/rubrics.json', 'r') as c:
        cs = json.load(c)
        for c in cs:
            for row in c['rows']:
                assignment = m.Assignment.query.filter_by(
                    name=c['assignment']).first()
                if assignment is not None:
                    rubric_row = m.RubricRow(
                        header=row['header'],
                        description=row['description'],
                        assignment=assignment)
                    db.session.add(rubric_row)
                    for item in row['items']:
                        rubric_item = m.RubricItem(
                            col=item['col'],
                            description=item['description'],
                            points=item['points'],
                            rubricrow=rubric_row)
                        db.session.add(rubric_item)
                else:
                    print('bah')
    db.session.commit()


if __name__ == '__main__':
    manager.run()

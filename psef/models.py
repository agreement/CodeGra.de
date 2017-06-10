from flask_login import UserMixin
from sqlalchemy.orm.collections import attribute_mapped_collection

from psef import db, app, login_manager

permissions = db.Table('roles-permissions',
                       db.Column('permission_id', db.Integer,
                                 db.ForeignKey('Permission.id')),
                       db.Column('role_id', db.Integer,
                                 db.ForeignKey('Role.id')))

course_permissions = db.Table('course_roles-permissions',
                              db.Column('permission_id', db.Integer,
                                        db.ForeignKey('Permission.id')),
                              db.Column('course_role_id', db.Integer,
                                        db.ForeignKey('Course_Role.id')))

user_course = db.Table('users-courses',
                       db.Column('course_id', db.Integer,
                                 db.ForeignKey('Course_Role.id')),
                       db.Column('user_id', db.Integer,
                                 db.ForeignKey('User.id')))


class Permission(db.Model):
    __tablename__ = 'Permission'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode, unique=True)
    default_value = db.Column('default_value', db.Boolean, default=False)
    course_permission = db.Column('course_permission', db.Boolean)


class CourseRole(db.Model):
    __tablename__ = 'Course_Role'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)
    course_id = db.Column('Course_id', db.Integer, db.ForeignKey('Course.id'))
    _permissions = db.relationship(
        'Permission',
        collection_class=attribute_mapped_collection('name'),
        secondary=course_permissions)

    course = db.relationship('Course', foreign_keys=course_id)

    def has_permission(self, permission):
        if permission in self._permissions:
            perm = self._permissions[permission]
            return perm.course_permission and not perm.default_value
        else:
            permission = Permission.query.filter_by(name=permission).first()
            if permission is None:
                raise KeyError(
                    'The permission "{}" does not exist'.format(permission))
            else:
                return (permission.default_value and
                        permission.course_permission)


class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)
    _permissions = db.relationship(
        'Permission',
        collection_class=attribute_mapped_collection('name'),
        secondary=permissions,
        backref=db.backref('roles', lazy='dynamic'))

    def has_permission(self, permission):
        if permission in self._permissions:
            return not self._permissions[permission].course_permission
        else:
            permission = Permission.query.filter_by(name=permission).first()
            if permission is None:
                raise KeyError(
                    'The permission "{}" does not exist'.format(permission))
            else:
                return (permission.default_value and
                        not permission.course_permission)


class User(db.Model, UserMixin):
    __tablename__ = "User"
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)
    active = db.Column('active', db.Boolean, default=True)
    role_id = db.Column('Role_id', db.Integer, db.ForeignKey('Role.id'))
    courses = db.relationship(
        'CourseRole',
        collection_class=attribute_mapped_collection('course.id'),
        secondary=user_course,
        backref=db.backref('users', lazy='dynamic'))

    role = db.relationship('Role', foreign_keys=role_id)

    def has_permission(self, permission, course_id=None):
        if course_id is None:
            return self.role.has_permission(permission)
        else:
            return (course_id in self.courses and
                    self.courses[course_id].has_permission(permission))

    @property
    def is_active(self):
        return self.active

    @staticmethod
    @login_manager.user_loader
    def load_user(user_id):
        User.query.get(int(user_id))


class Course(db.Model):
    __tablename__ = "Course"
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)


class Work(db.Model):
    __tablename__ = "Work"
    id = db.Column('id', db.Integer, primary_key=True)
    assignment_id = db.Column('Assignment_id', db.Integer,
                              db.ForeignKey('Assignment.id'))
    user_id = db.Column('User_id', db.Integer, db.ForeignKey('User.id'))
    state = db.Column('state', db.Integer)
    edit = db.Column('edit', db.Integer)

    assignment = db.relationship('Assignment', foreign_keys=assignment_id)
    user = db.relationship('User', foreign_keys=user_id)


class File(db.Model):
    __tablename__ = "File"
    id = db.Column('id', db.Integer, primary_key=True)
    work_id = db.Column('Work_id', db.Integer, db.ForeignKey('Work.id'))
    extension = db.Column('extension', db.Unicode)
    description = db.Column('description', db.Unicode)

    work = db.relationship('Work', foreign_keys=work_id)


class Comment(db.Model):
    __tablename__ = "Comment"
    file_id = db.Column('File_id', db.Integer, db.ForeignKey('File.id'))
    user_id = db.Column('User_id', db.Integer, db.ForeignKey('User.id'))
    line = db.Column('line', db.Integer)
    comment = db.Column('comment', db.Unicode)
    db.PrimaryKeyConstraint('file_id', 'line', name='id')

    file = db.relationship('File', foreign_keys=file_id)
    user = db.relationship('User', foreign_keys=user_id)


class Assignment(db.Model):
    __tablename__ = "Assignment"
    id = db.Column('id', db.Integer, primary_key=True)
    description = db.Column('description', db.Unicode)
    course_id = db.Column('Course_id', db.Integer, db.ForeignKey('Course.id'))

    course = db.relationship('Course', foreign_keys=course_id)

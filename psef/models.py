import os
import enum
import datetime

from flask_login import UserMixin
from sqlalchemy_utils import PasswordType
from sqlalchemy.sql.expression import or_, null, false
from sqlalchemy.orm.collections import attribute_mapped_collection

from psef import db, login_manager

permissions = db.Table('roles-permissions',
                       db.Column('permission_id', db.Integer,
                                 db.ForeignKey(
                                     'Permission.id', ondelete='CASCADE')),
                       db.Column('role_id', db.Integer,
                                 db.ForeignKey('Role.id', ondelete='CASCADE')))

course_permissions = db.Table('course_roles-permissions',
                              db.Column('permission_id', db.Integer,
                                        db.ForeignKey(
                                            'Permission.id',
                                            ondelete='CASCADE')),
                              db.Column('course_role_id', db.Integer,
                                        db.ForeignKey(
                                            'Course_Role.id',
                                            ondelete='CASCADE')))

user_course = db.Table('users-courses',
                       db.Column('course_id', db.Integer,
                                 db.ForeignKey(
                                     'Course_Role.id', ondelete='CASCADE')),
                       db.Column('user_id', db.Integer,
                                 db.ForeignKey('User.id', ondelete='CASCADE')))


class Permission(db.Model):
    __tablename__ = 'Permission'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode, unique=True, index=True)
    default_value = db.Column('default_value', db.Boolean, default=False)
    course_permission = db.Column('course_permission', db.Boolean, index=True)


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
        if isinstance(permission, Permission):
            permission_name = permission.name
        else:
            permission_name = permission
        if permission_name in self._permissions:
            perm = self._permissions[permission_name]
            return perm.course_permission and not perm.default_value
        else:
            if not isinstance(permission, Permission):
                permission = Permission.query.filter_by(
                    name=permission).first()
            if permission is None:
                raise KeyError('The permission "{}" does not exist'.format(
                    permission_name))
            else:
                return (permission.default_value and
                        permission.course_permission)

    def get_all_permissions(self):
        """Get all course permissions for this course role.

        :returns: A name boolean mapping where the name is the name of the
                  permission and the value indicates if this user has this
                  permission.
        :rtype: dict[str, bool]
        """
        perms = Permission.query.filter_by(course_permission=True).all()
        result = {}
        for perm in perms:
            if perm.name in self._permissions:
                result[perm.name] = not perm.default_value
            else:
                result[perm.name] = perm.default_value
        return result


class Role(db.Model):
    __tablename__ = 'Role'
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode, unique=True)
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

    def get_all_permissions(self):
        """Get all course permissions for this role.

        :returns: A name boolean mapping where the name is the name of the
                  permission and the value indicates if this user has this
                  permission.
        :rtype: dict[str, bool]
        """
        perms = Permission.query.filter_by(course_permission=False).all()
        result = {}
        for perm in perms:
            if perm.name in self._permissions:
                result[perm.name] = not perm.default_value
            else:
                result[perm.name] = perm.default_value
        return result


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
    email = db.Column('email', db.Unicode, unique=True)
    password = db.Column(
        'password',
        PasswordType(schemes=[
            'pbkdf2_sha512',
        ], deprecated=[]),
        nullable=False)

    role = db.relationship('Role', foreign_keys=role_id)

    def has_permission(self, permission, course_id=None):
        if course_id is None:
            return self.role.has_permission(permission)
        else:
            if isinstance(course_id, Course):
                course_id = course_id.id
            return (course_id in self.courses and
                    self.courses[course_id].has_permission(permission))

    def get_all_permissions(self, course_id=None):
        if isinstance(course_id, Course):
            course_id = course_id.id

        if course_id is None:
            return self.role.get_all_permissions()
        elif course_id in self.courses:
            return self.courses[course_id].get_all_permissions()
        else:
            return {
                perm.name: False
                for perm in Permission.query.filter_by(course_permission=True)
                .all()
            }

    @property
    def is_active(self):
        return self.active

    @staticmethod
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))


class Course(db.Model):
    __tablename__ = "Course"
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)


@enum.unique
class WorkStateEnum(enum.IntEnum):
    initial = 0  # Not looked at
    started = 1  # The TA is working on it
    done = 2  # This is the same as graded would be


class Work(db.Model):
    __tablename__ = "Work"
    id = db.Column('id', db.Integer, primary_key=True)
    assignment_id = db.Column('Assignment_id', db.Integer,
                              db.ForeignKey('Assignment.id'))
    user_id = db.Column('User_id', db.Integer,
                        db.ForeignKey('User.id', ondelete='CASCADE'))
    state = db.Column(
        'state', db.Enum(WorkStateEnum), default=WorkStateEnum.initial)
    edit = db.Column('edit', db.Integer)
    grade = db.Column('grade', db.Float, default=None)
    comment = db.Column('comment', db.Unicode, default=None)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    assignment = db.relationship('Assignment', foreign_keys=assignment_id)
    user = db.relationship('User', single_parent=True, foreign_keys=user_id)

    @property
    def is_graded(self):
        return self.state == WorkStateEnum.done

    def add_file_tree(self, session, tree):
        """Add the given tree to the given db.

        .. warning::
        The db session is not commited!

        :param db: The db object.
        :param tree: The file tree as described by
                     :py:func:`psef.files.rename_directory_structure`
        :returns: Nothing
        :rtype: None
        """
        assert isinstance(tree, dict)
        return self._add_file_tree(session, tree, None)

    def _add_file_tree(self, session, tree, top):
        def ensure_list(item):
            return item if isinstance(item, list) else [item]

        for new_top, children in tree.items():
            new_top = File(
                work=self,
                is_directory=True,
                name=new_top,
                extension=None,
                parent=top)
            session.add(new_top)
            for child in ensure_list(children):
                if isinstance(child, dict):
                    self._add_file_tree(session, child, new_top)
                    continue
                child, filename = child
                name, ext = os.path.splitext(child)
                ext = ext[1:]
                session.add(
                    File(
                        work=self,
                        extension=ext,
                        name=name,
                        filename=filename,
                        is_directory=False,
                        parent=new_top))


class File(db.Model):
    __tablename__ = "File"
    id = db.Column('id', db.Integer, primary_key=True)
    work_id = db.Column('Work_id', db.Integer, db.ForeignKey('Work.id'))
    extension = db.Column('extension', db.Unicode)
    name = db.Column('name', db.Unicode)
    filename = db.Column('path', db.Unicode)
    is_directory = db.Column('is_directory', db.Boolean)
    parent_id = db.Column(db.Integer, db.ForeignKey('File.id'))
    parent = db.relationship('File', remote_side=[id], backref='children')

    work = db.relationship('Work', foreign_keys=work_id)

    __table_args__ = (
        db.CheckConstraint(or_(is_directory == false(), extension == null())),
    )

    def get_filename(self):
        if self.extension != None and self.extension != "":
            return "{}.{}".format(self.name, self.extension)
        else:
            return self.name

    def list_contents(self):
        if self.is_directory == False:
            return {"name": self.get_filename(), "id": self.id}
        else:
            return {
                "name": self.get_filename(),
                "id": self.id,
                "entries": [child.list_contents() for child in self.children]
            }


class Comment(db.Model):
    __tablename__ = "Comment"
    file_id = db.Column('File_id', db.Integer)  # , db.ForeignKey('File.id'))
    user_id = db.Column('User_id', db.Integer)  # , db.ForeignKey('User.id'))
    line = db.Column('line', db.Integer)
    comment = db.Column('comment', db.Unicode)
    __table_args__ = (db.PrimaryKeyConstraint(file_id, line), )

    # Commented out relationships for testing purposes
    # file = db.relationship('File', foreign_keys=file_id)
    # user = db.relationship('User', foreign_keys=user_id)


class Assignment(db.Model):
    __tablename__ = "Assignment"
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)
    description = db.Column('description', db.Unicode, default='')
    course_id = db.Column('Course_id', db.Integer, db.ForeignKey('Course.id'))

    course = db.relationship('Course', foreign_keys=course_id)


class Snippet(db.Model):
    __tablename__ = 'Snippet'
    id = db.Column('id', db.Integer, primary_key=True)
    key = db.Column('key', db.Unicode)
    value = db.Column('value', db.Unicode)
    user_id = db.Column('User_id', db.Integer, db.ForeignKey('User.id'))

    user = db.relationship('User', foreign_keys=user_id)

    @classmethod
    def get_all_snippets(cls, user):
        return cls.query.filter_by(user_id=user.id).all()

    def to_dict(self):
        return {'key': self.key, 'value': self.value, 'id': self.id}

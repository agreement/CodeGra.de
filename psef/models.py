import os
import enum
import json
import uuid
import datetime

from flask_login import UserMixin
from sqlalchemy_utils import PasswordType
from sqlalchemy.sql.expression import or_, and_, func, null, false
from sqlalchemy.orm.collections import attribute_mapped_collection

import psef.auth as auth
from psef import db, app, login_manager
from psef.helpers import get_request_start_time

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


class LTIProvider(db.Model):
    __tablename__ = 'LTIProvider'
    id = db.Column('id', db.Integer, primary_key=True)
    key = db.Column('key', db.Unicode)

    @property
    def secret(self):
        return app.config['LTI_CONSUMER_KEY_SECRETS'][self.key]


class AssignmentResult(db.Model):
    __tablename__ = 'AssignmentResult'
    sourcedid = db.Column('sourdid', db.Unicode)
    user_id = db.Column('User_id', db.Integer,
                        db.ForeignKey('User.id', ondelete='CASCADE'))
    assignment_id = db.Column('Assignment_id', db.Integer,
                              db.ForeignKey(
                                  'Assignment.id', ondelete='CASCADE'))

    __table_args__ = (db.PrimaryKeyConstraint(assignment_id, user_id), )


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

    course = db.relationship('Course', foreign_keys=course_id, backref="roles")

    def __to_json__(self):
        return {
            'name': self.name,
            'course': self.course,
            'id': self.id,
        }

    def set_permission(self, perm, should_have):
        """Set the given permission to the given value.

        :param bool should_have: If this role should have this permission
        :param Permission perm: The permission this role should (not) have.
        :rtype None:
        """
        try:
            if perm.default_value:
                if should_have:
                    self._permissions.pop(perm.name)
                else:
                    self._permissions[perm.name] = perm
            else:
                if should_have:
                    self._permissions[perm.name] = perm
                else:
                    self._permissions.pop(perm.name)
        except KeyError:
            pass

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

    @staticmethod
    def get_default_course_roles():
        res = {}
        for name, c in app.config['DEFAULT_COURSE_ROLES'].items():
            perms = Permission.query.filter_by(course_permission=True).all()
            r_perms = {}
            perms_set = set(c['permissions'])
            for perm in perms:
                if ((perm.default_value and perm.name not in perms_set) or
                    (not perm.default_value and perm.name in perms_set)):
                    r_perms[perm.name] = perm

            res[name] = r_perms
        return res


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
            perm = self._permissions[permission]
            return (not perm.default_value) and (not perm.course_permission)
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

    # All stuff for LTI
    lti_user_id = db.Column(db.Unicode, unique=True)

    name = db.Column('name', db.Unicode)
    active = db.Column('active', db.Boolean, default=True)
    role_id = db.Column('Role_id', db.Integer, db.ForeignKey('Role.id'))
    courses = db.relationship(
        'CourseRole',
        collection_class=attribute_mapped_collection('course_id'),
        secondary=user_course,
        backref=db.backref('users', lazy='dynamic'))
    email = db.Column('email', db.Unicode(collation='NOCASE'), unique=True)
    password = db.Column(
        'password',
        PasswordType(schemes=[
            'pbkdf2_sha512',
        ], deprecated=[]),
        nullable=True)

    assignment_results = db.relationship(
        'AssignmentResult',
        collection_class=attribute_mapped_collection('assignment_id'),
        backref=db.backref('user', lazy='select'))

    role = db.relationship('Role', foreign_keys=role_id)

    def has_permission(self, permission, course_id=None):
        if not self.active:
            return False
        if course_id is None:
            return self.role.has_permission(permission)
        else:
            if isinstance(course_id, Course):
                course_id = course_id.id
            return (course_id in self.courses and
                    self.courses[course_id].has_permission(permission))

    def get_permission_in_courses(self, permission):
        if not isinstance(permission, Permission):
            permission = Permission.query.filter_by(name=permission).first()
        assert permission.course_permission

        course_roles = db.session.query(user_course.c.course_id).join(
            User, User.id == user_course.c.user_id).filter(
                User.id == self.id).subquery('course_roles')

        crp = db.session.query(course_permissions.c.course_role_id).join(
            Permission,
            course_permissions.c.permission_id == Permission.id).filter(
                Permission.id == permission.id).subquery('crp')

        res = db.session.query(course_roles.c.course_id).join(
            crp, course_roles.c.course_id == crp.c.course_role_id).all()

        return {
            course_role.course_id:
            (course_role.id, ) in res != permission.default_value
            for course_role in self.courses.values()
        }

    @property
    def can_see_hidden(self):
        return self.has_course_permission_once('can_see_hidden_assignments')

    def __to_json__(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "hidden": self.can_see_hidden,
        }

    def has_course_permission_once(self, permission):
        if not isinstance(permission, Permission):
            permission = Permission.query.filter_by(name=permission).first()
        assert permission.course_permission

        course_roles = db.session.query(user_course.c.course_id).join(
            User, User.id == user_course.c.user_id).filter(
                User.id == self.id).subquery('course_roles')
        crp = db.session.query(course_permissions.c.course_role_id).join(
            Permission,
            course_permissions.c.permission_id == Permission.id).filter(
                Permission.id == permission.id).subquery('crp')
        res = db.session.query(course_roles.c.course_id).join(
            crp, course_roles.c.course_id == crp.c.course_role_id)
        link = db.session.query(res.exists()).scalar()

        return (not link) if permission.default_value else link

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

    @staticmethod
    def validate_username(username):
        min_len = 3
        if len(username) < min_len:
            return ('use at least {} chars'.format(min_len))
        else:
            return ('')

    @staticmethod
    def validate_password(password):
        min_len = 3
        if len(password) < min_len:
            return ('use at least {} chars'.format(min_len))
        else:
            return ('')


class Course(db.Model):
    __tablename__ = "Course"
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)

    # All stuff for LTI
    lti_course_id = db.Column(db.Unicode, unique=True)

    lti_provider_id = db.Column(db.Integer, db.ForeignKey('LTIProvider.id'))
    lti_provider = db.relationship("LTIProvider")

    assignments = db.relationship(
        "Assignment", back_populates="course", cascade='all,delete')

    def __init__(self, name=None, lti_course_id=None, lti_provider=None):
        self.name = name
        self.lti_course_id = lti_course_id
        self.lti_provider = lti_provider
        for name, perms in CourseRole.get_default_course_roles().items():
            CourseRole(name=name, course=self, _permissions=perms)

    def __to_json__(self):
        return {'id': self.id, 'name': self.name}


class Work(db.Model):
    __tablename__ = "Work"
    id = db.Column('id', db.Integer, primary_key=True)
    assignment_id = db.Column('Assignment_id', db.Integer,
                              db.ForeignKey('Assignment.id'))
    user_id = db.Column('User_id', db.Integer,
                        db.ForeignKey('User.id', ondelete='CASCADE'))
    edit = db.Column('edit', db.Integer)
    _grade = db.Column('grade', db.Float, default=None)
    comment = db.Column('comment', db.Unicode, default=None)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    assigned_to = db.Column('assigned_to', db.Integer,
                            db.ForeignKey('User.id'))

    assignment = db.relationship('Assignment', foreign_keys=assignment_id)
    user = db.relationship('User', single_parent=True, foreign_keys=user_id)
    assignee = db.relationship('User', foreign_keys=assigned_to)

    @property
    def is_graded(self):
        raise NotImplementedError()

    @property
    def grade(self):
        return self._grade

    @grade.setter
    def grade(self, new_grade):
        from psef.lti import LTI
        self._grade = new_grade
        if self.assignment and self.assignment.course.lti_provider:
            lti_provider = self.assignment.course.lti_provider
            LTI.passback_grade(
                lti_provider.key,
                lti_provider.secret,
                self.grade / 10,
                self.assignment.lti_outcome_service_url,
                self.user.assignment_results[self.assignment_id].sourcedid,
                url=('{}/'
                     'courses/{}/assignments/{}/submissions/{}?lti=true'
                     ).format(app.config['EXTERNAL_URL'],
                              self.assignment.course_id, self.assignment_id,
                              self.id))

    def __to_json__(self):
        item = {
            'id': self.id,
            'user': self.user,
            'edit': self.edit,
            'created_at': self.created_at.isoformat(),
        }

        try:
            auth.ensure_permission('can_see_assignee', self.assignment.course_id)
            item['assignee'] = self.assignee
        except auth.PermissionException:
            item['assignee'] = False

        try:
            auth.ensure_can_see_grade(self)
            item['grade'] = self.grade
            item['comment'] = self.comment
        except auth.PermissionException:
            item['grade'] = False
            item['comment'] = False
        return item

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
    parent = db.relationship(
        'File', remote_side=[id], backref=db.backref('children'))

    work = db.relationship('Work', foreign_keys=work_id)

    __table_args__ = (
        db.CheckConstraint(or_(is_directory == false(), extension == null())),
    )

    def get_filename(self):
        if self.extension is not None and self.extension != "":
            return "{}.{}".format(self.name, self.extension)
        else:
            return self.name

    def list_contents(self):
        if not self.is_directory:
            return {"name": self.get_filename(), "id": self.id}
        else:
            return {
                "name": self.get_filename(),
                "id": self.id,
                "entries": [child.list_contents() for child in self.children]
            }

    def __to_json__(self):
        return {
            'name': self.name,
            'extension': self.extension,
        }


class LinterComment(db.Model):
    __tablename__ = "LinterComment"
    file_id = db.Column(
        'File_id', db.Integer, db.ForeignKey('File.id'), index=True)
    linter_id = db.Column(db.Unicode, db.ForeignKey('LinterInstance.id'))

    line = db.Column('line', db.Integer)
    linter_code = db.Column('linter_code', db.Unicode)
    comment = db.Column('comment', db.Unicode)
    __table_args__ = (db.PrimaryKeyConstraint(file_id, line, linter_id), )

    linter = db.relationship("LinterInstance", back_populates="comments")
    file = db.relationship('File', foreign_keys=file_id)

    def __to_json__(self):
        return {
            'code': self.linter_code,
            'line': self.line,
            'msg': self.comment,
        }


class Comment(db.Model):
    __tablename__ = "Comment"
    file_id = db.Column('File_id', db.Integer, db.ForeignKey('File.id'))
    user_id = db.Column('User_id', db.Integer, db.ForeignKey('User.id'))
    line = db.Column('line', db.Integer)
    comment = db.Column('comment', db.Unicode)
    __table_args__ = (db.PrimaryKeyConstraint(file_id, line), )

    file = db.relationship('File', foreign_keys=file_id)
    user = db.relationship('User', foreign_keys=user_id)

    def __to_json__(self):
        return {
            'line': self.line,
            'msg': self.comment,
        }


@enum.unique
class LinterState(enum.IntEnum):
    running = 1
    done = 2
    crashed = 3


class AssignmentLinter(db.Model):
    __tablename__ = 'AssignmentLinter'
    id = db.Column('id', db.Unicode, nullable=False, primary_key=True)
    name = db.Column('name', db.Unicode)
    tests = db.relationship(
        "LinterInstance",
        back_populates="tester",
        cascade='all,delete',
        order_by='LinterInstance.work_id')
    assignment_id = db.Column('Assignment_id', db.Integer,
                              db.ForeignKey('Assignment.id'))

    assignment = db.relationship('Assignment', foreign_keys=assignment_id)

    def __to_json__(self):
        working = 0
        crashed = 0
        done = 0

        for test in self.tests:
            if test.state == LinterState.running:
                working += 1
            elif test.state == LinterState.crashed:
                crashed += 1
            else:
                done += 1

        return {
            'done': done,
            'working': working,
            'crashed': crashed,
            'id': self.id,
            'name': self.name,
        }

    @classmethod
    def create_tester(cls, assignment_id, name):
        id = str(uuid.uuid4())
        while db.session.query(
                AssignmentLinter.query.filter(cls.id == id).exists()).scalar():
            id = str(uuid.uuid4())
        self = cls(id=id, assignment_id=assignment_id, name=name)
        tests = []
        sub = db.session.query(
            Work.user_id.label('user_id'),
            func.max(Work.created_at).label('max_date')).group_by(
                Work.user_id).subquery('sub')
        for work in db.session.query(Work).join(
                sub,
                and_(sub.c.user_id == Work.user_id,
                     sub.c.max_date == Work.created_at)).filter(
                         Work.assignment_id == assignment_id).order_by(
                             Work.id).all():
            tests.append(LinterInstance(work, self))
        self.tests = tests
        return self


class LinterInstance(db.Model):
    __tablename__ = 'LinterInstance'
    id = db.Column('id', db.Unicode, nullable=False, primary_key=True)
    state = db.Column(
        'state',
        db.Enum(LinterState),
        default=LinterState.running,
        nullable=False)
    work_id = db.Column('Work_id', db.Integer, db.ForeignKey('Work.id'))
    tester_id = db.Column(db.Unicode, db.ForeignKey('AssignmentLinter.id'))

    tester = db.relationship("AssignmentLinter", back_populates="tests")
    work = db.relationship('Work', foreign_keys=work_id)

    comments = db.relationship(
        "LinterComment", back_populates="linter", cascade='all,delete')

    def __init__(self, work, tester):
        id = str(uuid.uuid4())
        while db.session.query(
                LinterInstance.query.filter(LinterInstance.id == id)
                .exists()).scalar():
            id = str(uuid.uuid4())
        self.id = id
        self.work = work
        self.tester = tester

    def to_dict(self):
        return {
            'name': self.work.user.name,
            'state': LinterState(self.state).name,
        }


@enum.unique
class _AssignmentStateEnum(enum.IntEnum):
    hidden = 0
    open = 1
    done = 2


class Assignment(db.Model):
    __tablename__ = "Assignment"
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column('name', db.Unicode)
    state = db.Column(
        'state',
        db.Enum(_AssignmentStateEnum),
        default=_AssignmentStateEnum.hidden,
        nullable=False)
    description = db.Column('description', db.Unicode, default='')
    course_id = db.Column('Course_id', db.Integer, db.ForeignKey('Course.id'))
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    deadline = db.Column('deadline', db.DateTime)

    # All stuff for LTI
    lti_assignment_id = db.Column(db.Unicode, unique=True)
    lti_outcome_service_url = db.Column(db.Unicode)

    assignment_results = db.relationship(
        'AssignmentResult',
        collection_class=attribute_mapped_collection('user_id'),
        backref=db.backref('assignment', lazy='select'))

    course = db.relationship(
        'Course', foreign_keys=course_id, back_populates='assignments')

    @property
    def is_open(self):
        if (self.state == _AssignmentStateEnum.open and
                self.deadline >= get_request_start_time()):
            return True
        return False

    @property
    def is_hidden(self):
        return self.state == _AssignmentStateEnum.hidden

    @property
    def is_closed(self):
        return self.state == _AssignmentStateEnum.closed

    @property
    def is_done(self):
        return self.state == _AssignmentStateEnum.done

    @property
    def state_name(self):
        if self.state == _AssignmentStateEnum.open:
            return 'submitting' if self.is_open else 'grading'
        return _AssignmentStateEnum(self.state).name

    def __to_json__(self):
        return {
            'id': self.id,
            'state': self.state_name,
            'open': self.is_open,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat(),
            'name': self.name,
            'course_name': self.course.name,
            'course_id': self.course_id,
        }

    def set_state(self, state):
        """Update the current state.

        You can update the state to hidden, done or open. A assignment can not
        be updated to 'submitting' or 'grading' as this is an assignment with
        state of 'open' and, respectively, a deadline before or after the
        current time.

        :param str state: The new state, can be 'hidden', 'done' or 'open'
        :rtype: None
        """
        if state == 'open':
            self.state = _AssignmentStateEnum.open
        elif state in {'done', 'hidden'}:
            self.state = _AssignmentStateEnum.__members__[state]
        else:
            raise TypeError()

    def get_all_latest_submissions(self):
        sub = db.session.query(
            Work.user_id.label('user_id'),
            func.max(Work.created_at).label('max_date')).group_by(
                Work.user_id).subquery('sub')
        return db.session.query(Work).join(
            sub,
            and_(sub.c.user_id == Work.user_id,
                 sub.c.max_date == Work.created_at)).filter(
                     Work.assignment_id == self.id).all()


class Snippet(db.Model):
    __tablename__ = 'Snippet'
    id = db.Column('id', db.Integer, primary_key=True)
    key = db.Column('key', db.Unicode, nullable=False)
    value = db.Column('value', db.Unicode, nullable=False)
    user_id = db.Column('User_id', db.Integer, db.ForeignKey('User.id'))

    user = db.relationship('User', foreign_keys=user_id)

    @classmethod
    def get_all_snippets(cls, user):
        return cls.query.filter_by(user_id=user.id).all()

    def __to_json__(self):
        return {'key': self.key, 'value': self.value, 'id': self.id}

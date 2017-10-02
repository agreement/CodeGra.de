"""
This module defines all the objects in the database in their relation.
"""

import os
import enum
import uuid
import typing as t
import datetime
import threading
from concurrent import futures

from itsdangerous import URLSafeTimedSerializer
from sqlalchemy_utils import PasswordType
from sqlalchemy.sql.expression import or_, and_, func, null, false
from sqlalchemy.orm.collections import attribute_mapped_collection

import psef.auth as auth
from psef import db, app, jwt
from psef.helpers import get_request_start_time

UUID_LENGTH = 36

if t.TYPE_CHECKING:  # pragma: no cover
    T = t.TypeVar('T')

    class Base:
        query = None  # type: t.ClassVar[t.Any]

        def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
            pass

    class _MyQuery(t.Generic[T], t.Iterable):
        def get(self, *args: t.Any, **kwargs: t.Any) -> t.Union[T, None]:
            ...

        def all(self) -> t.List[T]:
            ...

        def first(self) -> t.Optional[T]:
            ...

        def exists(self) -> bool:
            ...

        def count(self) -> int:
            ...

        def one(self) -> T:
            ...

        def update(self, vals: t.Mapping[str, t.Any]) -> None:
            ...

        def join(self, *args: t.Any, **kwargs: t.Any) -> '_MyQuery[T]':
            ...

        def order_by(self, *args: t.Any, **kwargs: t.Any) -> '_MyQuery[T]':
            ...

        def filter(self, *args: t.Any, **kwargs: t.Any) -> '_MyQuery[T]':
            ...

        def filter_by(self, *args: t.Any, **kwargs: t.Any) -> '_MyQuery[T]':
            ...

        def __iter__(self) -> t.Iterator[T]:
            ...

else:
    import psef
    Base = db.Model

permissions = db.Table(
    'roles-permissions',
    db.Column(
        'permission_id', db.Integer,
        db.ForeignKey('Permission.id', ondelete='CASCADE')
    ),
    db.Column(
        'role_id', db.Integer, db.ForeignKey('Role.id', ondelete='CASCADE')
    )
)

course_permissions = db.Table(
    'course_roles-permissions',
    db.Column(
        'permission_id', db.Integer,
        db.ForeignKey('Permission.id', ondelete='CASCADE')
    ),
    db.Column(
        'course_role_id', db.Integer,
        db.ForeignKey('Course_Role.id', ondelete='CASCADE')
    )
)

user_course = db.Table(
    'users-courses',
    db.Column(
        'course_id', db.Integer,
        db.ForeignKey('Course_Role.id', ondelete='CASCADE')
    ),
    db.Column(
        'user_id', db.Integer, db.ForeignKey('User.id', ondelete='CASCADE')
    )
)

work_rubric_item = db.Table(
    'work_rubric_item',
    db.Column(
        'work_id', db.Integer, db.ForeignKey('Work.id', ondelete='CASCADE')
    ),
    db.Column(
        'rubricitem_id', db.Integer,
        db.ForeignKey('RubricItem.id', ondelete='CASCADE')
    )
)


class LTIProvider(Base):
    """This class defines the handshake with an LTI

    :ivar key: The OAuth consumer key for this LTI provider.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['LTIProvider']]
    __tablename__ = 'LTIProvider'
    id: str = db.Column('id', db.String(UUID_LENGTH), primary_key=True)
    key: str = db.Column('key', db.Unicode, unique=True)

    def __init__(self, key: str) -> None:
        self.key = key
        public_id = str(uuid.uuid4())

        while db.session.query(
            LTIProvider.query.filter_by(id=public_id).exists()
        ).scalar():  # pragma: no cover
            public_id = str(uuid.uuid4())

        self.id = public_id

    @property
    def secret(self) -> str:
        """The OAuth consumer secret for this LTIProvider.

        :getter: Get the OAuth secret.
        :setter: Impossible as all secrets are fixed during startup of
            codegra.de
        """
        return app.config['LTI_CONSUMER_KEY_SECRETS'][self.key]


class AssignmentResult(Base):
    """The class creates the link between an :class:`User` and an
    :class:`Assignment` in the database and the external users LIS sourcedid.

    :ivar sourcedid: The ``sourcedid`` for this user for this assignment.
    :ivar user_id: The id of the user this belongs to.
    :ivar assignment_id: The id of the assignment this belongs to.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['AssignmentResult']]
    __tablename__ = 'AssignmentResult'
    sourcedid: str = db.Column('sourcedid', db.Unicode)
    user_id: int = db.Column(
        'User_id', db.Integer, db.ForeignKey('User.id', ondelete='CASCADE')
    )
    assignment_id: int = db.Column(
        'Assignment_id', db.Integer,
        db.ForeignKey('Assignment.id', ondelete='CASCADE')
    )

    __table_args__ = (db.PrimaryKeyConstraint(assignment_id, user_id), )


class Permission(Base):
    """This class defines permissions by names that are checked in certain
    APIs.

    A permission can be a global- or a course- permission. Global permissions
    describe the ability to do something general, e.g. create a course or the
    usage of snippets. These permissions are connected to a :class:`Role` which
    is hold be a :class:`User`. Similarly course permissions are bound to a
    :class:`CourseRole`. These roles are assigned to users only in the context
    of a single :class:`Course`. Thus a user can hold different permissions in
    different courses.

    :ivar name: The, unique, name of this permission.
    :ivar default_value: The default value for this permission.
    :ivar course_permission: Indicates if this permission is for course
        specific actions. If this is the case a user can have this permission
        for a subset of all the courses. If ``course_permission`` is ``False``
        this permission is global for the entire site.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['Permission']]
    __tablename__ = 'Permission'

    id = db.Column('id', db.Integer, primary_key=True)

    name: str = db.Column('name', db.Unicode, unique=True, index=True)

    default_value: bool  # NOQA
    default_value = db.Column('default_value', db.Boolean, default=False)
    course_permission: bool = db.Column(
        'course_permission', db.Boolean, index=True
    )


class CourseRole(Base):
    """
    A course role is used to describe the abilities of a :class:`User` in a
    :class:`Course`.

    :ivar name: The name of this role in the course.
    :ivar course_id: The :py:class:`Course` this role belongs to.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['CourseRole']]
    __tablename__ = 'Course_Role'
    id = db.Column('id', db.Integer, primary_key=True)
    name: str = db.Column('name', db.Unicode)
    course_id: int = db.Column(
        'Course_id', db.Integer, db.ForeignKey('Course.id')
    )
    _permissions: t.MutableMapping[str, Permission] = db.relationship(
        'Permission',
        collection_class=attribute_mapped_collection('name'),
        secondary=course_permissions
    )

    # Old syntax used to please sphinx
    course = db.relationship(
        'Course', foreign_keys=course_id, backref="roles"
    )  # type: Course

    def __to_json__(self) -> t.MutableMapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.
        """
        return {
            'name': self.name,
            'course': self.course,
            'id': self.id,
        }

    def set_permission(self, perm: Permission, should_have: bool) -> None:
        """Set the given :class:`Permission` to the given value.

        :param should_have: If this role should have this permission
        :param perm: The permission this role should (not) have
        """
        try:
            if perm.default_value ^ should_have:
                self._permissions[perm.name] = perm
            else:
                self._permissions.pop(perm.name)
        except KeyError:
            pass

    def has_permission(self, permission: t.Union[str, Permission]) -> bool:
        """Check whether this course role has the specified
        :class:`Permission`.

        :param permission: The permission or permission name
        :returns: True if the course role has the permission

        :raises KeyError: If the permission parameter is a string and no
            permission with this name exists.
        """
        if isinstance(permission, Permission):
            permission_name = permission.name
        else:
            permission_name = permission

        if permission_name in self._permissions:
            perm = self._permissions[permission_name]
            return perm.course_permission and not perm.default_value
        else:
            if isinstance(permission, str):
                permission = Permission.query.filter_by(  # type: ignore
                    name=permission).first()

            if isinstance(permission, Permission) and permission is not None:
                return (
                    permission.default_value and permission.course_permission
                )
            else:
                raise KeyError(
                    'The permission "{}" does not exist'.
                    format(permission_name)
                )

    def get_all_permissions(self) -> t.Mapping[str, bool]:
        """Get all course :class:`permissions` for this course role.

        :returns: A name boolean mapping where the name is the name of the
                  permission and the value indicates if this user has this
                  permission.
        """
        perms: t.Sequence[Permission] = (
            Permission.query.
            filter_by(  # type: ignore
                course_permission=True
            ).all()
        )
        result: t.MutableMapping[str, bool] = {}
        for perm in perms:
            if perm.name in self._permissions:
                result[perm.name] = not perm.default_value
            else:
                result[perm.name] = perm.default_value
        return result

    @classmethod
    def get_initial_course_role(cls: t.Type['CourseRole'],
                                course: 'Course') -> 'CourseRole':
        """Get the initial course role for a given course.

        :param course: The course to get the initial role for.
        :returns: A course role that should be the role for the user creating
            the course.
        """
        for name, c in app.config['_DEFAULT_COURSE_ROLES'].items():
            if c['initial_role']:
                return cls.query.filter_by(name=name, course=course).one()
        raise ValueError('No initial course role found')

    @staticmethod
    def get_default_course_roles(
    ) -> t.Mapping[str, t.Mapping[str, Permission]]:
        """Get all default course roles as specified in the config and their
        permissions (:class:`Permission`).


        .. code:: python

            {
                'student': {
                    'can_manage_course': <Permission-object>,
                    'can_submit_own_work': <Permission-object>
                }
            }

        :returns: A name dict mapping where the name is the name of the
            course-role and the dict is name permission mapping between the
            name of a permission and the permission object. See above for an
            example.
        """
        res = {}
        for name, c in app.config['_DEFAULT_COURSE_ROLES'].items():
            perms: t.Sequence[Permission] = (
                Permission.query.
                filter_by(  # type: ignore
                    course_permission=True
                ).all()
            )
            r_perms = {}
            perms_set = set(c['permissions'])
            for perm in perms:
                if bool(perm.default_value) ^ bool(perm.name in perms_set):
                    r_perms[perm.name] = perm

            res[name] = r_perms
        return res


class Role(Base):
    """A role defines the set of global permissions :class:`Permission` of a
    :class:`User`.

    :ivar name: The name of the global role.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['Role']]
    __tablename__ = 'Role'
    id: int = db.Column('id', db.Integer, primary_key=True)
    name: str = db.Column('name', db.Unicode, unique=True)
    _permissions: t.MutableMapping[str, Permission] = db.relationship(
        'Permission',
        collection_class=attribute_mapped_collection('name'),
        secondary=permissions,
        backref=db.backref('roles', lazy='dynamic')
    )

    def set_permission(self, perm: Permission, should_have: bool) -> None:
        """Set the given :class:`Permission` to the given value.

        :param should_have: If this role should have this permission
        :param perm: The permission this role should (not) have
        """
        try:
            if perm.default_value ^ should_have:
                self._permissions[perm.name] = perm
            else:
                self._permissions.pop(perm.name)
        except KeyError:
            pass

    def has_permission(self, permission: t.Union[str, Permission]) -> bool:
        """Check whether this role has the specified :class:`Permission`.

        :param permission: The permission to check
        :returns: Whether the role has the permission or not

        :raises KeyEror: If the permission parameter is a string and no
                         permission with this name exists.
        """
        if isinstance(permission, Permission):
            perm_name = permission.name
        else:
            perm_name = permission

        if permission in self._permissions:
            perm = self._permissions[perm_name]
            return (not perm.default_value) and (not perm.course_permission)
        else:
            if not isinstance(permission, Permission):
                permission = (
                    Permission.query.
                    filter_by(  # type: ignore
                        name=permission
                    ).first()
                )
            if isinstance(permission, Permission):
                return (
                    permission.default_value and
                    not permission.course_permission
                )
            else:
                raise KeyError(
                    'The permission "{}" does not exist'.format(permission)
                )

    def get_all_permissions(self) -> t.Mapping[str, bool]:
        """Get all course permissions (:class:`Permission`) for this role.

        :returns: A name boolean mapping where the name is the name of the
            permission and the value indicates if this user has this
            permission.
        """
        perms: t.Sequence[Permission] = (
            Permission.query.
            filter_by(  # type: ignore
                course_permission=False
            ).all()
        )
        result = {}
        for perm in perms:
            if perm.name in self._permissions:
                result[perm.name] = not perm.default_value
            else:
                result[perm.name] = perm.default_value
        return result

    def __to_json__(self) -> t.MutableMapping[str, t.Any]:
        """Creates a JSON serializable representation of a role.

        This object will look like this:

        .. code:: python

            {
                'id':    int, # The id of this role.
                'name':  str, # The name of this role.
            }

        :returns: An object as described above.
        """
        return {
            'name': self.name,
            'id': self.id,
        }


class User(Base):
    """This class describes a user of the system.

    :ivar lti_user_id: The id of this user in a LTI consumer.
    :ivar name: The name of this user.
    :ivar role_id: The id of the role this user has.
    :ivar courses: A mapping between course_id and course-role for all courses
        this user is currently enrolled.
    :ivar email: The e-mail of this user.
    :ivar password: The password of this user, it is automatically hashed.
    :ivar assignment_results: The way this user can do LTI grade passback.
    """
    # Python 3 implicitly set __hash__ to None if we override __eq__
    # We set it back to its default implementation
    __hash__ = object.__hash__
    __tablename__ = "User"

    id: int = db.Column('id', db.Integer, primary_key=True)

    # All stuff for LTI
    lti_user_id: str = db.Column(db.Unicode, unique=True)

    name: str = db.Column('name', db.Unicode)
    active: bool = db.Column('active', db.Boolean, default=True)
    role_id: int = db.Column('Role_id', db.Integer, db.ForeignKey('Role.id'))
    courses: t.MutableMapping[int, CourseRole] = db.relationship(
        'CourseRole',
        collection_class=attribute_mapped_collection('course_id'),
        secondary=user_course,
        backref=db.backref('users', lazy='dynamic')
    )
    username: str = db.Column(
        'username',
        db.Unicode,
        unique=True,
        nullable=False,
        index=True,
    )

    reset_token: str = db.Column(
        'reset_token', db.String(UUID_LENGTH), nullable=True
    )

    email: str = db.Column('email', db.Unicode, unique=False, nullable=False)
    password: str = db.Column(
        'password',
        PasswordType(schemes=[
            'pbkdf2_sha512',
        ], deprecated=[]),
        nullable=True
    )

    assignment_results: t.MutableMapping[
        int, AssignmentResult
    ] = db.relationship(
        'AssignmentResult',
        collection_class=attribute_mapped_collection('assignment_id'),
        backref=db.backref('user', lazy='select')
    )

    role: Role = db.relationship('Role', foreign_keys=role_id, lazy='select')

    def __eq__(self, other: t.Any) -> bool:  # pragma: no cover
        return isinstance(other, User) and self.id == other.id

    def __ne__(self, other: t.Any) -> bool:  # pragma: no cover
        return not self.__eq__(other)

    def has_permission(
        self,
        permission: t.Union[str, Permission],
        course_id: t.Union['Course', int]=None
    ) -> bool:
        """Check whether this user has the specified global or course
        :class:`Permission`.

        To check a course permission the course_id has to be set.

        :param permission: The permission or permission name
        :param course_id: The course or course id
        :returns: Whether the role has the permission or not

        :raises KeyError: If the permission parameter is a string and no
                         permission with this name exists.
        """
        if not self.active:
            return False
        if course_id is None:
            return self.role.has_permission(permission)
        else:
            if isinstance(course_id, Course):
                course_id = course_id.id

            if course_id in self.courses:
                return self.courses[course_id].has_permission(permission)
            elif isinstance(permission, str):
                if Permission.query.filter_by(name=permission).first() is None:
                    raise KeyError(
                        f'The permission "{permission}" does not exist'
                    )
            return False

    def get_permission_in_courses(self, perm: t.Union[str, Permission]
                                  ) -> t.Mapping[int, bool]:
        """Check for a specific course :class:`Permission` in all courses
        (:class:`Course`) the user is enrolled in.

        :param perm: The permission or its name to check for.
        :returns: An int bool mapping where the int is the course id and the
            the bool whether the user has the permission in the course with
            thid id
        """
        permission: Permission
        if isinstance(perm, str):
            permission = Permission.query.filter_by(  # type: ignore
                name=perm).first()
        else:
            permission = perm
        assert permission.course_permission

        course_roles = db.session.query(user_course.c.course_id).join(
            User, User.id == user_course.c.user_id
        ).filter(User.id == self.id).subquery('course_roles')

        crp = db.session.query(course_permissions.c.course_role_id).join(
            Permission, course_permissions.c.permission_id == Permission.id
        ).filter(Permission.id == permission.id).subquery('crp')

        res: t.Sequence[t.Tuple[int]]
        res = db.session.query(course_roles.c.course_id).join(
            crp, course_roles.c.course_id == crp.c.course_role_id
        ).all()

        course_ids: t.Set[int]
        course_ids = set(course_id[0] for course_id in res)

        return {
            course_role.course_id:
            (course_role.id in course_ids) != permission.default_value
            for course_role in self.courses.values()
        }

    @property
    def can_see_hidden(self) -> bool:
        return self.has_course_permission_once('can_see_hidden_assignments')

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.

        This object will look like this:

        .. code:: python

            {
                'id':    int, # The id of this user.
                'name':  str, # The full name of this user.
                'email': str, # The email of this user.
                'username': str, # The username of this user.
            }

        :returns: An object as described above.
        """
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'username': self.username,
        }

    def __extended_to_json__(self) -> t.Mapping[str, t.Any]:
        """Create a extended JSON serializable representation of this object.

        This object will look like this:

        .. code:: python

            {
                'hidden': bool, # indicating if this user can once
                                # see hidden assignments.
                **self.__to_json__()
            }

        :returns: A object as described above.
        """
        return {
            "hidden": self.can_see_hidden,
            **self.__to_json__(),
        }

    def has_course_permission_once(self,
                                   perm: t.Union[str, Permission]) -> bool:
        """Check whether this user has the specified course :class:`Permission`
        in at least one enrolled :class:`Course`.

        :param perm: The permission or permission name
        :returns: True if the user has the permission once
        """

        permission: Permission
        if isinstance(perm, Permission):
            permission = perm
        else:
            permission = Permission.query.filter_by(  # type: ignore
                name=perm).first()
        assert permission.course_permission

        course_roles = db.session.query(user_course.c.course_id).join(
            User, User.id == user_course.c.user_id
        ).filter(User.id == self.id).subquery('course_roles')
        crp = db.session.query(course_permissions.c.course_role_id).join(
            Permission, course_permissions.c.permission_id == Permission.id
        ).filter(Permission.id == permission.id).subquery('crp')
        res = db.session.query(course_roles.c.course_id).join(
            crp, course_roles.c.course_id == crp.c.course_role_id
        )
        link: bool = db.session.query(res.exists()).scalar()

        return (not link) if permission.default_value else link

    def get_all_permissions(self, course_id: t.Union['Course', int]=None
                            ) -> t.Mapping[str, bool]:
        """Get all global permissions (:class:`Permission`) of this user or all
        course permissions of the user in a specific :class:`Course`.

        :param course_id: The course or course id

        :returns: A name boolean mapping where the name is the name of the
            permission and the value indicates if this user has this
            permission.
        """
        if isinstance(course_id, Course):
            course_id = course_id.id

        if course_id is None:
            return self.role.get_all_permissions()
        elif course_id in self.courses:
            return self.courses[course_id].get_all_permissions()
        else:
            perms: t.Sequence[Permission]
            perms = Permission.query.filter_by(  # type: ignore
                course_permission=True).all()
            return {perm.name: False for perm in perms}

    def get_reset_token(self) -> str:
        """Get a token which a user can use to reset his password.

        .. note:: Don't forget to commit the database.

        :returns: A token that can be used in :py:meth:`User.reset_password` to
            reset the password of a user.
        """
        ts = URLSafeTimedSerializer(psef.app.config['SECRET_KEY'])
        self.reset_token = str(uuid.uuid4())
        return str(ts.dumps(self.username, salt=self.reset_token))

    def reset_password(self, token: str, new_password: str) -> None:
        """Reset a users password by using a token.

        .. note:: Don't forget to commit the database.

        :param token: A token as generated by :py:meth:`User.get_reset_token`.
        :param new_password: The new password to set.
        :returns: Nothing.

        :raises psef.auth.PermissionException: If something was wrong with the
            given token.
        """
        ts = URLSafeTimedSerializer(psef.app.config['SECRET_KEY'])
        try:
            username = ts.loads(
                token,
                max_age=psef.app.config['RESET_TOKEN_TIME'],
                salt=self.reset_token
            )
        except:
            import traceback
            traceback.print_exc()
            raise psef.auth.PermissionException(
                'The given token is not valid',
                f'The given token {token} is not valid.',
                psef.errors.APICodes.INVALID_CREDENTIALS, 403
            )

        # This should never happen but better safe than sorry.
        if (username != self.username or
                self.reset_token is None):  # pragma: no cover
            raise psef.auth.PermissionException(
                'The given token is not valid for this user',
                f'The given token {token} is not valid for user "{self.id}".',
                psef.errors.APICodes.INVALID_CREDENTIALS, 403
            )

        self.password = new_password
        self.reset_token = None

    @property
    def is_active(self) -> bool:
        return self.active

    @staticmethod
    @jwt.user_loader_callback_loader
    def load_user(user_id: int) -> t.Optional['User']:
        return User.query.get(int(user_id))


class Course(Base):
    """This class describes a course.

    A course can hold a collection of :class:`Assignment` objects.

    :param name: The name of the course
    :param lti_course_id: The id of the course in LTI
    :param lti_provider: The LTI provider
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['Course']]
    __tablename__ = "Course"
    id: int = db.Column('id', db.Integer, primary_key=True)
    name: str = db.Column('name', db.Unicode)

    created_at: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )

    # All stuff for LTI
    lti_course_id: str = db.Column(db.Unicode, unique=True)

    lti_provider_id: str = db.Column(
        db.String(UUID_LENGTH), db.ForeignKey('LTIProvider.id')
    )
    lti_provider: LTIProvider = db.relationship("LTIProvider")

    assignments = db.relationship(
        "Assignment", back_populates="course", cascade='all,delete'
    )  # type: t.MutableSequence[Assignment]

    def __init__(
        self,
        name: str=None,
        lti_course_id: str=None,
        lti_provider: LTIProvider=None
    ) -> None:
        self.name = name
        self.lti_course_id = lti_course_id
        self.lti_provider = lti_provider
        for name, perms in CourseRole.get_default_course_roles().items():
            CourseRole(name=name, course=self, _permissions=perms)

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.

        This object will look like this:

        .. code:: python

            {
                'name': str, # The name of the course,
                'id': int, # The id of this course.
                'created_at': str, # ISO UTC date.
                'is_lti': bool, # Is the this course a LTI course,
            }

        :returns: A object as described above.
        """
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'is_lti': self.lti_course_id is not None,
        }

    def get_all_visible_assignments(self) -> t.Sequence['Assignment']:
        """Get all visible assignments for the current user for this course.

        :returns: A list of assignments the currently logged in user may see.
        """
        if psef.current_user.has_permission(
            'can_see_hidden_assignments', self.id
        ):
            return sorted(self.assignments, key=lambda item: item.deadline)
        else:
            return sorted(
                (a for a in self.assignments if not a.is_hidden),
                key=lambda item: item.deadline
            )


class GradeHistory(Base):
    """This object is a item in a grade history of a :class:`Work`.

    :ivar changed_at: When was this grade added.
    :ivar is_rubric: Was this grade added as a result of a rubric.
    :ivar passed_back: Was this grade passed back to the LMS through LTI.
    :ivar work: What work does this grade belong to.
    :ivar user: What user added this grade.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['GradeHistory']]
    __tablename__ = "GradeHistory"
    id: int = db.Column('id', db.Integer, primary_key=True)
    changed_at: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    is_rubric: bool = db.Column('is_rubric', db.Boolean)
    grade: float = db.Column('grade', db.Float)
    passed_back: bool = db.Column('passed_back', db.Boolean, default=False)

    work_id: int = db.Column(
        'Work_id', db.Integer, db.ForeignKey('Work.id', ondelete='CASCADE')
    )
    user_id: int = db.Column(
        'User_id', db.Integer, db.ForeignKey('User.id', ondelete='CASCADE')
    )

    work = db.relationship('Work', foreign_keys=work_id)  # type: 'Work'
    user = db.relationship('User', foreign_keys=user_id)  # type: User

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Converts a rubric of a work to a object that is JSON serializable.

        The resulting object will look like this:

        .. code:: python

            {
                'changed_at': str, # The date the history was added.
                'is_rubric': bool, # Was this history items added by a rubric
                                   # grade.
                'grade': float, # The new grade, -1 if the grade was deleted.
                'passed_back': bool, # Is this grade given back to LTI.
                'user': User, # The user that added this grade.
            }

        :returns: A object as described above.
        """
        return {
            'changed_at': self.changed_at.isoformat(),
            'is_rubric': self.is_rubric,
            'grade': self.grade,
            'passed_back': self.passed_back,
            'user': self.user,
        }


class Work(Base):
    """This object describes a single work or submission of a :class:`User` for
    an :class:`Assignment`.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['Work']]
    __tablename__ = "Work"  # type: str
    id = db.Column('id', db.Integer, primary_key=True)  # type: int
    assignment_id: int = db.Column(
        'Assignment_id', db.Integer, db.ForeignKey('Assignment.id')
    )
    user_id: int = db.Column(
        'User_id', db.Integer, db.ForeignKey('User.id', ondelete='CASCADE')
    )
    _grade: float = db.Column('grade', db.Float, default=None)
    comment: str = db.Column('comment', db.Unicode, default=None)
    created_at: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    assigned_to: int = db.Column(
        'assigned_to', db.Integer, db.ForeignKey('User.id')
    )
    selected_items = db.relationship(
        'RubricItem', secondary=work_rubric_item
    )  # type: t.MutableSequence['RubricItem']

    assignment = db.relationship(
        'Assignment', foreign_keys=assignment_id, lazy='joined'
    )  # type: 'Assignment'
    user = db.relationship(
        'User', foreign_keys=user_id, lazy='joined'
    )  # type: User
    assignee = db.relationship(
        'User', foreign_keys=assigned_to, lazy='joined'
    )  # type: User

    def run_linter(self) -> None:
        """Run all linters for the assignment on this work.

        All linters that have been used on the assignment will also run on this
        work.

        :returns: Nothing
        """
        for linter in self.assignment.linters:
            instance = LinterInstance(work=self, tester=linter)

            linter_cls = psef.linters.get_linter_by_name(linter.name)
            if not linter_cls.RUN_LINTER:
                instance.state = LinterState.done

            db.session.add(instance)
            db.session.commit()

            if not linter_cls.RUN_LINTER:
                return

            runner = psef.linters.LinterRunner(linter_cls, linter.config)
            threading.Thread(target=runner.run, args=([instance.id], )).start()

    @property
    def grade(self) -> float:
        """Get the actual current grade for this work.

        This is done by not only checking the ``grade`` field but also checking
        if rubric could be found.

        :returns: The current grade for this work.
        """
        if self._grade is None:
            if not self.selected_items:
                return None
            max_points = self.assignment.max_rubric_points
            selected = sum(item.points for item in self.selected_items)
            return max((selected / max_points) * 10, 0)
        return self._grade

    def set_grade(self, new_grade: float, user: User) -> None:
        """Set the grade to the new grade.

        .. note:: This also passes back the grade to LTI if this is necessary
            (see :py:func:`passback_grade`).

        :param new_grade: The new grade to set
        :param user: The user setting the new grade.
        :returns: Nothing
        """
        self._grade = new_grade
        passback = self.assignment.should_passback
        grade = self.grade
        history = GradeHistory(
            is_rubric=self._grade is None and grade is not None,
            grade=-1 if grade is None else grade,
            passed_back=False,
            work=self,
            user=user
        )
        db.session.add(history)
        db.session.flush()
        if passback:
            self.passback_grade()

    @property
    def selected_rubric_points(self) -> float:
        return sum(item.points for item in self.selected_items)

    def passback_grade(self, initial: bool=False) -> None:
        """Initiates a passback of the grade to the LTI consumer via the
        :class:`LTIProvider`.

        :param initial: Should we do a initial LTI grade passback with no
            result so that the real grade won't show as too late.
        :returns: Nothing
        """
        if self.assignment.lti_outcome_service_url is not None:
            lti_provider = self.assignment.course.lti_provider
            if initial:
                url = (
                    '{}/'
                    'courses/{}/assignments/{}/submissions?inLTI=true'
                ).format(
                    app.config['EXTERNAL_URL'],
                    self.assignment.course_id,
                    self.assignment_id,
                )
            else:
                url = None

            psef.lti.LTI.passback_grade(
                lti_provider.key,
                lti_provider.secret,
                False if initial else self.grade,
                self.assignment.lti_outcome_service_url,
                self.assignment.assignment_results[self.user_id].sourcedid,
                url=url,
            )
            sq = db.session.query(GradeHistory.id).filter_by(
                work_id=self.id
            ).order_by(
                GradeHistory.changed_at.desc(),  # type: ignore
            ).limit(1).with_for_update()
            db.session.query(GradeHistory).filter_by(
                id=sq.as_scalar(),
            ).update(
                {
                    'passed_back': True
                }, synchronize_session='fetch'
            )

    def select_rubric_items(
        self, items: t.List['RubricItem'], user: User, override: bool=False
    ) -> None:
        """ Selects the given :class:`RubricItem`.

        .. note:: This also passes back the grade to LTI if this is necessary.

        .. note:: This also sets the actual grade field to `None`.

        :param item: The item to add.
        :param user: The user selecting the item.
        :returns: Nothing
        """
        if override:
            self.selected_items = []

        for item in items:
            self.selected_items.append(item)

        self.set_grade(None, user)

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Returns the JSON serializable representation of this work.

        The representation is based on the permissions (:class:`Permission`) of
        the logged in :class:`User`. Namely the assignee and feedback
        attributes are only included if the current user can see them.

        :returns: A dict containing JSON serializable representations of the
                  attributes of this work.
        """
        item = {
            'id': self.id,
            'user': self.user,
            'created_at': self.created_at.isoformat(),
        }

        try:
            auth.ensure_permission(
                'can_see_assignee', self.assignment.course_id
            )
            item['assignee'] = self.assignee
        except auth.PermissionException:
            item['assignee'] = False

        try:
            auth.ensure_can_see_grade(self)
        except auth.PermissionException:
            item['grade'] = False
            item['comment'] = False
        else:
            item['grade'] = self.grade
            item['comment'] = self.comment
        return item

    def __rubric_to_json__(self) -> t.Mapping[str, t.Any]:
        """Converts a rubric of a work to a object that is JSON serializable.

        The resulting object will look like this:

        .. code:: python

            {
                'rubrics': t.List[RubricRow] # A list of all the
                                             # rubrics for this work.
                'selected': t.List[RubricItem] # A list of all the
                                               # selected rubric items
                                               # for this work.
                'points': {
                    'max': float # The maximal amount of points
                                 # for this rubric.
                    'selected': float # The amount of point that is
                                      # selected for this work.
                }
            }

        :returns: A object as described above.

        .. todo:: Remove the points object.
        """
        try:
            auth.ensure_can_see_grade(self)

            return {
                'rubrics': self.assignment.rubric_rows,
                'selected': self.selected_items,
                'points':
                    {
                        'max': self.assignment.max_rubric_points,
                        'selected': self.selected_rubric_points,
                    },
            }
        except auth.PermissionException:
            return {
                'rubrics': self.assignment.rubric_rows,
            }

    def add_file_tree(
        self,
        session: 'orm.scoped_session',
        tree: 'psef.files.ExtractFileTree'
    ) -> None:
        """Add the given tree to given session.

        .. warning::

            The db session is not commited!

        :param session: The db session
        :param tree: The file tree as described by
            :py:func:`psef.files.rename_directory_structure`
        :returns: Nothing
        """
        assert isinstance(tree, dict)
        return self._add_file_tree(session, tree, None)

    def _add_file_tree(
        self,
        session: 'orm.scoped_session',
        tree: 'psef.files.ExtractFileTree',
        top: 'File'
    ) -> None:
        """Add the given tree to the session with top as parent.

        :param session: The db session
        :param tree: The file tree as described by
                          :py:func:`psef.files.rename_directory_structure`
        :param top: The parent file
        :returns: Nothing
        """
        for new_top, children in tree.items():
            new_top = File(
                work=self, is_directory=True, name=new_top, parent=top
            )
            session.add(new_top)
            for child in children:
                if isinstance(child, t.MutableMapping):
                    self._add_file_tree(session, child, new_top)
                    continue
                name, filename = child
                session.add(
                    File(
                        work=self,
                        name=name,
                        filename=filename,
                        is_directory=False,
                        parent=new_top
                    )
                )

    def get_all_feedback(self) -> t.Tuple[t.Iterable[str], t.Iterable[str], ]:
        """Get all feedback for this work.

        :returns: A tuple of two iterators both producing human readable
            representations of the given feedback. The first iterator produces
            the feedback given by a person and the second the feedback given by
            the linters.
        """

        def _get_user_feedback() -> t.Iterable[str]:
            comments = Comment.query.filter(
                Comment.file.has(work=self),  # type: ignore
            ).order_by(
                Comment.file_id.asc(),  # type: ignore
                Comment.line.asc(),  # type: ignore
            )
            for c in comments:
                yield f'{c.file.name}:{c.line}:0: {c.comment}'

        def _get_linter_feedback() -> t.Iterable[str]:
            linter_comments = LinterComment.query.filter(
                LinterComment.file.has(work=self)  # type: ignore
            ).order_by(
                LinterComment.file_id.asc(),  # type: ignore
                LinterComment.line.asc(),  # type: ignore
            )
            for lc in linter_comments:
                yield (
                    f'{lc.file.name}:{lc.line}:0: ({lc.linter.tester.name}'
                    f' {lc.linter_code}) {lc.comment}'
                )

        return _get_user_feedback(), _get_linter_feedback()

    def remove_selected_rubric_item(self, row_id: int) -> None:
        """Deselect selected :class:`RubricItem` on row.

        Deselects the selected rubric item on the given row with _row_id_  (if
        there are any selected).

        :param row_id: The id of the RubricRow from which to deselect
                           rubric items
        :returns: Nothing
        """
        rubricitem = db.session.query(RubricItem).join(
            work_rubric_item, RubricItem.id == work_rubric_item.c.rubricitem_id
        ).filter(
            work_rubric_item.c.work_id == self.id,
            RubricItem.rubricrow_id == row_id
        ).first()
        if rubricitem is not None:
            self.selected_items.remove(rubricitem)

    def search_file(
        self,
        pathname: str,
        exclude: 'FileOwner',
    ) -> 'File':
        """Search for a file in the this directory with the given name.

        :param pathname: The path of the file to search for, this may contain
            leading and trailing slashes which do not have any meaning.
        :param exclude: The fileowner to exclude from search, like described in
            :func:`get_zip`.
        :returns: The found file.
        """
        patharr, is_dir = psef.files.split_path(pathname)

        parent: t.Optional[t.Any] = None
        for idx, pathpart in enumerate(patharr[:-1]):
            if parent is not None:
                parent = parent.c.id

            parent = db.session.query(File.id).filter(
                File.name == pathpart,
                File.parent_id == parent,
                File.work_id == self.id,
                File.is_directory,
            ).subquery(f'parent_{idx}')

        if parent is not None:
            parent = parent.c.id

        return psef.helpers.filter_single_or_404(
            File,
            File.work_id == self.id,
            File.name == patharr[-1],
            File.parent_id == parent,
            File.fileowner != exclude,
            File.is_directory == is_dir,
        )


@enum.unique
class FileOwner(enum.IntEnum):
    """Describes to which version of a submission (student's submission or
    teacher's revision) a file belongs. When a student adds or changes a file
    after the deadline for the assignment has passed, the original file's owner
    is set `teacher` and the new file's to `student`.

    :param student: The file is in the student's submission, but changed in the
        teacher's revision.
    :param teacher: The inverse of `student`. The file is added or changed in
        the teacher's revision.
    :param both: The file is not changed in the teacher's revision and belongs
        to both versions.
    """

    student: int = 1
    teacher: int = 2
    both: int = 3


class File(Base):
    """
    This object describes a file or directory that stored is stored on the
    server.

    Files are always connected to :class:`Work` objects. A directory file does
    not physically exist but is stored only in the database to preserve the
    submitted work structure. Each submission should have a single top level
    file. Each other file in a submission should be directly or indirectly
    connected to this file via the parent attribute.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query: t.ClassVar[_MyQuery['File']]
    __tablename__ = "File"
    id: int = db.Column('id', db.Integer, primary_key=True)
    work_id: int = db.Column(
        'Work_id', db.Integer, db.ForeignKey('Work.id', ondelete='CASCADE')
    )
    name: str = db.Column('name', db.Unicode, nullable=False)

    # This is the filename for the original file on the disk
    filename: t.Optional[str]
    filename = db.Column('filename', db.Unicode, nullable=True)
    modification_date = db.Column(
        'modification_date', db.DateTime, default=datetime.datetime.utcnow
    )

    fileowner: FileOwner = db.Column(
        'fileowner',
        db.Enum(FileOwner),
        default=FileOwner.both,
        nullable=False
    )

    is_directory: bool = db.Column('is_directory', db.Boolean)
    parent_id: int = db.Column(db.Integer, db.ForeignKey('File.id'))

    # This variable is generated from the backref from the parent
    children: '_MyQuery["File"]'

    parent = db.relationship(
        'File',
        remote_side=[id],
        backref=db.backref('children', lazy='dynamic')
    )  # type: 'File'

    work = db.relationship('Work', foreign_keys=work_id)  # type: 'Work'

    @staticmethod
    @auth.login_required
    def get_exclude_owner(owner: t.Optional[str], course_id: int) -> FileOwner:
        """Get the :class:`FileOwner` the current user does not want to see
        files for.

        The result will be decided like this, if the given str is not
        `student`, `teacher` or `auto` the result will be `FileOwner.teacher`.
        If the str is `student`, the result will be `FileOwner.teacher`, vica
        versa for `teacher` as input. If the input is auto `student` will be
        returned if the currently logged in user is a teacher, otherwise it
        will be `student`.

        :param owner: The owner that was given in the `GET` paramater.
        :param course_id: The course for which the files are requested.
        :returns: The object determined as described above.
        """
        teacher, student = FileOwner.teacher, FileOwner.student
        if owner == 'student':
            return teacher
        elif owner == 'teacher':
            return student
        elif owner == 'auto':
            if psef.current_user.has_permission(
                'can_edit_others_work', course_id
            ):
                return student
            else:
                return teacher
        else:
            return teacher

    def get_diskname(self) -> str:
        """Get the absolute path on the disk for this file.

        :returns: The absolute path.
        """
        assert not self.is_directory
        return os.path.join(app.config['UPLOAD_DIR'], self.filename)

    def delete_from_disk(self) -> None:
        """Delete the file from disk if it is not a directory.

        :returns: Nothing.
        """
        if not self.is_directory:
            os.remove(self.get_diskname())

    def list_contents(self, exclude: FileOwner) -> 'psef.files.FileTree':
        """List the basic file info and the info of its children.

        If the file is a directory it will return a tree like this:

        .. code:: python

            {
                'name': 'dir_1',
                'id': 1,
                'entries': [
                    {
                        'name': 'file_1',
                        'id': 2
                    },
                    {
                        'name': 'file_2',
                        'id': 3
                    },
                    {
                        'name': 'dir_2',
                        'id': 4,
                        'entries': []
                    }
                ]
            }

        Otherwise it will formatted like one of the file children of the above
        tree.

        :param exclude: The file owner to exclude from the tree.

        :returns: A tree as described above.
        """
        if not self.is_directory:
            return {"name": self.name, "id": self.id}
        else:
            children = sorted(
                (
                    child.list_contents(exclude)
                    for child in
                    self.children.filter(File.fileowner != exclude).all()
                ),
                key=lambda el: el['name']
            )
            return {
                "name": self.name,
                "id": self.id,
                "entries": children,
            }

    def rename_code(
        self,
        new_name: str,
        new_parent: 'File',
        exclude_owner: FileOwner,
    ) -> None:
        """Rename the this file to the given new name.

        :param new_name: The new name to be given to the given file.
        :param new_parent: The new parent of this file.
        :param exclude_owner: The owner to exclude while searching for
            collisions.
        :returns: Nothing.

        :raises APIException: If renaming would result in a naming collision
            (INVALID_STATE).
        """
        if new_parent.children.filter_by(name=new_name).filter(
            File.fileowner != exclude_owner,
        ).first() is not None:
            raise psef.errors.APIException(
                'This file already exists within this directory',
                f'The file "{new_parent.id}" has '
                f'a child with the name "{new_name}"',
                psef.errors.APICodes.INVALID_STATE, 400
            )

        self.name = new_name

    def __to_json__(self) -> t.Mapping[str, t.Union[str, bool, int]]:
        """Creates a JSON serializable representation of this object.


        This object will look like this:

        .. code:: python

            {
                'name': str, # The name of the file or directory.
                'id': int, # The id of this file.
                'is_directory': bool, # Is this file a directory.
            }

        :returns: A object as described above.
        """
        return {
            'name': self.name,
            'is_directory': self.is_directory,
            'id': self.id,
        }


class LinterComment(Base):
    """Describes a comment created by a :class:`LinterInstance`.

    Like a :class:`Comment` it is attached to a specific line in a
    :class:`File`.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['LinterComment']]
    __tablename__ = "LinterComment"  # type: str
    id: int = db.Column('id', db.Integer, primary_key=True)
    file_id: int = db.Column(
        'File_id',
        db.Integer,
        db.ForeignKey('File.id', ondelete='CASCADE'),
        index=True
    )
    linter_id: str = db.Column(db.Unicode, db.ForeignKey('LinterInstance.id'))

    line: int = db.Column('line', db.Integer)
    linter_code: str = db.Column('linter_code', db.Unicode)
    comment: str = db.Column('comment', db.Unicode)

    linter = db.relationship(
        "LinterInstance", back_populates="comments"
    )  # type: 'LinterInstance'
    file: File = db.relationship('File', foreign_keys=file_id)

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.
        """
        return {
            'code': self.linter_code,
            'line': self.line,
            'msg': self.comment,
        }


class Comment(Base):
    """Describes a comment placed in a :class:`File` by a :class:`User` with
    the ability to grade.

    A comment is always linked to a specific line in a file.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['Comment']]
    __tablename__ = "Comment"
    file_id: int = db.Column(
        'File_id', db.Integer, db.ForeignKey('File.id', ondelete='CASCADE')
    )
    user_id: int = db.Column(
        'User_id', db.Integer, db.ForeignKey('User.id', ondelete='CASCADE')
    )
    line: int = db.Column('line', db.Integer)
    comment: str = db.Column('comment', db.Unicode)
    __table_args__ = (db.PrimaryKeyConstraint(file_id, line), )

    file: File = db.relationship('File', foreign_keys=file_id)
    user: User = db.relationship('User', foreign_keys=user_id)

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.
        """
        return {
            'line': self.line,
            'msg': self.comment,
        }


@enum.unique
class LinterState(enum.IntEnum):
    """Describes in what state a :class:`LinterInstance` is.

    :param running: The linter is currently running.
    :param done: The linter has finished without crashing.
    :param crashed: The linter has crashed in some way.
    """
    running: int = 1
    done: int = 2
    crashed: int = 3


class AssignmentLinter(Base):
    """The class is used when a linter (see :py:mod:`psef.linters`) is used on
    a :class:`Assignment`.

    Every :class:`Work` that is tested is attached by a
    :class:`LinterInstance`.

    The name identifies which :class:`.linters.Linter` is used.

    :ivar name: The name of the linter which is the `__name__` of a subclass of
        :py:class:`linters.Linter`.
    :ivar tests: All the linter instances for this linter, this are the
        recordings of the running of the actual linter (so in the case of the
        :py:class:`linters.Flake8` metadata about the `flake8` program).
    :ivar config: The config that was passed to the linter.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['AssignmentLinter']]
    __tablename__ = 'AssignmentLinter'  # type: str
    # This has to be a String object as the id has to be a non guessable uuid.
    id: str = db.Column(
        'id', db.String(UUID_LENGTH), nullable=False, primary_key=True
    )
    name: str = db.Column('name', db.Unicode)
    tests = db.relationship(
        "LinterInstance",
        back_populates="tester",
        cascade='all,delete',
        order_by='LinterInstance.work_id'
    )  # type: t.Sequence[LinterInstance]
    config: str = db.Column(
        'config',
        db.Unicode,
        nullable=False,
    )
    assignment_id = db.Column(
        'Assignment_id',
        db.Integer,
        db.ForeignKey('Assignment.id'),
    )  # type: int

    assignment = db.relationship(
        'Assignment',
        foreign_keys=assignment_id,
        backref=db.backref('linters', uselist=True),
    )  # type: 'Assignment'

    @property
    def linters_crashed(self) -> int:
        return self._amount_linters_in_state(LinterState.crashed)

    @property
    def linters_done(self) -> int:
        return self._amount_linters_in_state(LinterState.done)

    @property
    def linters_running(self) -> int:
        return self._amount_linters_in_state(LinterState.running)

    def _amount_linters_in_state(self, state: LinterState) -> int:
        return LinterInstance.query.filter_by(
            tester_id=self.id, state=state
        ).count()

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Returns the JSON serializable representation of this class.

        This representation also returns a count of the :class:`LinterState` of
        the attached :class:`LinterInstance` objects.

        :returns: A dict containing JSON serializable representations of the
                  attributes and the test state counts of this
                  AssignmentLinter.
        """
        return {
            'done': self.linters_done,
            'working': self.linters_running,
            'crashed': self.linters_crashed,
            'id': self.id,
            'name': self.name,
        }

    @classmethod
    def create_linter(
        cls: t.Type['AssignmentLinter'],
        assignment_id: int,
        name: str,
        config: str,
    ) -> 'AssignmentLinter':
        """Create a new instance of this class for a given :class:`Assignment`
        with a given :py:class:`.linters.Linter`

        :param assignment_id: The id of the assignment
        :param name: Name of the linter
        :returns: The created AssignmentLinter
        """
        id = str(uuid.uuid4())

        # Find a unique id.
        while db.session.query(
            AssignmentLinter.query.filter(cls.id == id).exists()
        ).scalar():  # pragma: no cover
            id = str(uuid.uuid4())

        self = cls(id=id, assignment_id=assignment_id, name=name)
        self.config = config

        self.tests = []
        for work in Assignment.query.get(assignment_id
                                         ).get_all_latest_submissions():
            self.tests.append(LinterInstance(work, self))

        return self


class LinterInstance(Base):
    """Describes the connection between a :class:`AssignmentLinter` and a
    :class:`Work`.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['LinterInstance']]
    __tablename__ = 'LinterInstance'
    id: str = db.Column(
        'id', db.String(UUID_LENGTH), nullable=False, primary_key=True
    )
    state: LinterState = db.Column(
        'state',
        db.Enum(LinterState),
        default=LinterState.running,
        nullable=False
    )
    work_id: int = db.Column(
        'Work_id', db.Integer, db.ForeignKey('Work.id', ondelete='CASCADE')
    )
    tester_id: int = db.Column(
        db.Unicode, db.ForeignKey('AssignmentLinter.id')
    )

    tester: AssignmentLinter = db.relationship(
        "AssignmentLinter", back_populates="tests"
    )
    work: Work = db.relationship('Work', foreign_keys=work_id)

    comments: LinterComment = db.relationship(
        "LinterComment", back_populates="linter", cascade='all,delete'
    )

    def __init__(self, work: Work, tester: AssignmentLinter) -> None:
        # Find a unique id
        id = str(uuid.uuid4())
        while db.session.query(
            LinterInstance.query.filter(LinterInstance.id == id).exists()
        ).scalar():  # pragma: no cover
            id = str(uuid.uuid4())

        self.id = id
        self.work = work
        self.tester = tester

    def add_comments(
        self,
        feedbacks: t.Mapping[int, t.Mapping[int, t.Sequence[t.Tuple[str, str]]]
                             ],
    ) -> t.Iterable[LinterComment]:
        """Add comments written by this instance.

        :param feedbacks: The feedback to add, it should be in form as
            described below.
        :returns: A iterable with comments that have not been added or commited
            to the database yet.

        .. code:: python

            {
                file_id: {
                    line_number: [(linter_code, msg), ...]
                }
            }
        """
        for file_id, feedback in feedbacks.items():
            for line_number, msgs in feedback.items():
                for linter_code, msg in msgs:
                    yield LinterComment(
                        file_id=file_id,
                        line=line_number,
                        linter_code=linter_code,
                        linter_id=self.id,
                        comment=msg,
                    )


@enum.unique
class _AssignmentStateEnum(enum.IntEnum):
    """Describes in what state an :class:`Assignment` is.
    """
    hidden = 0
    open = 1
    done = 2


class Assignment(Base):
    """This class describes a :class:`Course` specific assignment.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type:  t.ClassVar[_MyQuery['Assignment']]
    __tablename__ = "Assignment"
    id: int = db.Column('id', db.Integer, primary_key=True)
    name: str = db.Column('name', db.Unicode)
    state: _AssignmentStateEnum = db.Column(
        'state',
        db.Enum(_AssignmentStateEnum),
        default=_AssignmentStateEnum.hidden,
        nullable=False
    )
    description: str = db.Column('description', db.Unicode, default='')
    course_id: int = db.Column(
        'Course_id', db.Integer, db.ForeignKey('Course.id')
    )
    created_at: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    deadline: datetime.datetime = db.Column('deadline', db.DateTime)

    # All stuff for LTI
    lti_assignment_id: str = db.Column(db.Unicode, unique=True)
    lti_outcome_service_url: str = db.Column(db.Unicode)

    assignment_results: t.MutableMapping[
        int, AssignmentResult
    ] = db.relationship(
        'AssignmentResult',
        collection_class=attribute_mapped_collection('user_id'),
        backref=db.backref('assignment', lazy='select')
    )

    course: Course = db.relationship(
        'Course',
        foreign_keys=course_id,
        back_populates='assignments',
        lazy='joined'
    )

    rubric_rows = db.relationship(
        'RubricRow',
        backref=db.backref('assignment'),
        cascade='delete-orphan, delete',
        order_by="RubricRow.created_at"
    )  # type: t.MutableSequence['RubricRow']

    # This variable is available through a backref
    linters: t.Iterable['AssignmentLinter']

    def _submit_grades(self) -> None:
        if app.config['_USING_SQLITE']:
            for sub in self.get_all_latest_submissions():
                sub.passback_grade()
        # This line is covered using the postgresql tests, however that data
        # won't be send to coveralls so we ignore it.
        else:  # pragma: no cover
            with futures.ThreadPoolExecutor() as pool:
                for sub in self.get_all_latest_submissions():
                    pool.submit(sub.passback_grade)

    @property
    def is_lti(self) -> bool:
        """Is this assignment a LTI assignment.

        :returns: A boolean indicating if this is the case.
        """
        return self.lti_outcome_service_url is not None

    @property
    def max_rubric_points(self) -> t.Optional[float]:
        """Get the maximum amount of points possible for the rubric

        .. note::

          This is always higher than zero (so also not zero).


        :returns: The maximum amount of points.
        """
        sub = db.session.query(func.max(RubricItem.points).label('max_val')
                               ).join(
                                   RubricRow,
                                   RubricRow.id == RubricItem.rubricrow_id
                               ).filter(
                                   RubricRow.assignment_id == self.id
                               ).group_by(RubricRow.id).subquery('sub')
        return db.session.query(func.sum(sub.c.max_val)).scalar()

    @property
    def is_open(self) -> bool:
        if (
            self.state == _AssignmentStateEnum.open and
            self.deadline >= get_request_start_time()):
            return True
        return False

    @property
    def is_hidden(self) -> bool:
        return self.state == _AssignmentStateEnum.hidden

    @property
    def is_done(self) -> bool:
        return self.state == _AssignmentStateEnum.done

    @property
    def should_passback(self) -> bool:
        return self.is_done

    @property
    def state_name(self) -> str:
        if self.state == _AssignmentStateEnum.open:
            return 'submitting' if self.is_open else 'grading'
        return _AssignmentStateEnum(self.state).name

    @property
    def whitespace_linter(self) -> bool:
        """Check if this assignment has an associated MixedWhitespace linter.

        .. note::

            If the assignment is not yet done we check if the ``current_user``
            has the permission ``can_see_grade_before_open``

        :returns: True if there is an :py:class:`.AssignmentLinter` with name
        ``MixedWhitespace`` and ``assignment_id``.
        """
        try:
            if not self.is_done:
                auth.ensure_permission(
                    'can_see_grade_before_open', self.course_id
                )
        except auth.PermissionException:
            return False
        else:
            return db.session.query(
                AssignmentLinter.query.filter(
                    AssignmentLinter.assignment_id == self.id,
                    AssignmentLinter.name == 'MixedWhitespace'
                ).exists()
            ).scalar()

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.

        This object will look like this:

        .. code:: python

            {
                'id': int, # The id of this assignment.
                'state': str, # Current state of this assignment.
                'description': str, # Description of this assignment.
                'created_at': str, # ISO UTC date.
                'deadline': str, # ISO UTC date.
                'name': str, # Assignment name.
                'is_lti': bool, # Is this an LTI assignment.
                'course': models.Course, # Course of this assignment.
                'whitespace_linter': bool, # Has the whitespace linter
                                           # run on this assignment.
            }

        :returns: An object as described above.

        .. todo:: Remove description from Assignment model.
        """
        return {
            'id': self.id,
            'state': self.state_name,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'deadline': self.deadline.isoformat(),
            'name': self.name,
            'is_lti': self.is_lti,
            'course': self.course,
            'whitespace_linter': self.whitespace_linter,
        }

    def set_state(self, state: str) -> None:
        """Update the current state (class:`_AssignmentStateEnum`).

        You can update the state to hidden, done or open. A assignment can not
        be updated to 'submitting' or 'grading' as this is an assignment with
        state of 'open' and, respectively, a deadline before or after the
        current time.

        :param state: The new state, can be 'hidden', 'done' or 'open'
        :returns: Nothing
        """
        if state == 'open':
            self.state = _AssignmentStateEnum.open
        elif state == 'hidden':
            self.state = _AssignmentStateEnum.hidden
        elif state == 'done':
            self.state = _AssignmentStateEnum.done
            if self.lti_outcome_service_url is not None:
                self._submit_grades()
        else:  # pragma: no cover
            raise TypeError

    def get_all_latest_submissions(self) -> '_MyQuery[Work]':
        """Get a list of all the latest submissions (:class:`Work`) by each
        :class:`User` who has submitted at least one work for this assignment.

        :returns: The latest submissions
        """
        sub = db.session.query(
            Work.user_id.label('user_id'),  # type: ignore
            func.max(Work.created_at).label('max_date')
        ).filter_by(assignment_id=self.id
                    ).group_by(Work.user_id).subquery('sub')
        return Work.query.join(
            sub,
            and_(
                sub.c.user_id == Work.user_id,
                sub.c.max_date == Work.created_at
            )
        ).filter(Work.assignment_id == self.id)


class Snippet(Base):
    """Describes a :class:`User` specified mapping from a keyword to some
    string.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['Snippet']]
    __tablename__ = 'Snippet'
    id: int = db.Column('id', db.Integer, primary_key=True)
    key: str = db.Column('key', db.Unicode, nullable=False)
    value: str = db.Column('value', db.Unicode, nullable=False)
    user_id: int = db.Column('User_id', db.Integer, db.ForeignKey('User.id'))

    user: User = db.relationship('User', foreign_keys=user_id)

    @classmethod
    def get_all_snippets(cls: t.Type['Snippet'],
                         user: User) -> t.Sequence['Snippet']:
        """Return all snippets of the given :class:`User`.

        :param user: The user to get the snippets for.
        :returns: List of all snippets of the user.
        """
        return cls.query.filter_by(user_id=user.id).order_by('id').all()

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.
        """
        return {
            'key': self.key,
            'value': self.value,
            'id': self.id,
        }


class RubricRow(Base):
    """Describes a row of some rubric.

    This class forms the link between :class:`Assignment` and
    :class:`RubricItem` and holds information about the row.

    :ivar assignment_id: The assignment id of the assignment that belows to
        this rubric row.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['RubricRow']]
    __tablename__ = 'RubricRow'
    id: int = db.Column('id', db.Integer, primary_key=True)
    assignment_id: int = db.Column(
        'Assignment_id', db.Integer, db.ForeignKey('Assignment.id')
    )
    header: str = db.Column('header', db.Unicode)
    description: str = db.Column('description', db.Unicode, default='')
    created_at: datetime.datetime = db.Column(
        db.DateTime, default=datetime.datetime.utcnow
    )
    items = db.relationship(
        "RubricItem", backref="rubricrow", cascade='delete-orphan, delete'
    )  # type: t.MutableSequence[RubricItem]

    # This is for the type checker and is available because of a backref.
    assignment: Assignment

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.
        """
        return {
            'id': self.id,
            'header': self.header,
            'description': self.description,
            'items': self.items,
        }


class RubricItem(Base):
    """This class holds the information about a single option/item in a
    :class:`RubricRow`.
    """
    if t.TYPE_CHECKING:  # pragma: no cover
        query = Base.query  # type: t.ClassVar[_MyQuery['RubricItem']]

    __tablename__ = 'RubricItem'

    id: int = db.Column('id', db.Integer, primary_key=True)
    rubricrow_id: int = db.Column(
        'Rubricrow_id', db.Integer,
        db.ForeignKey('RubricRow.id', ondelete='CASCADE')
    )
    header: str = db.Column('header', db.Unicode, default='')
    description: str = db.Column('description', db.Unicode, default='')
    points: float = db.Column('points', db.Float)

    # This variable is generated from the backref from RubricRow
    rubricrow: RubricRow

    def __to_json__(self) -> t.Mapping[str, t.Any]:
        """Creates a JSON serializable representation of this object.
        """
        return {
            'id': self.id,
            'description': self.description,
            'header': self.header,
            'points': self.points,
        }


if t.TYPE_CHECKING:  # pragma: no cover
    import psef  # NOQA
    import sqlalchemy.orm as orm  # NOQA

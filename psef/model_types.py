"""
This module DOES NOT define any thing. It is only used for type information
about sqlalchemy.

:license: AGPLv3, see LICENSE for details.
"""

import enum
import typing as t
from datetime import datetime

T = t.TypeVar('T')
Z = t.TypeVar('Z')
Y = t.TypeVar('Y')
U = t.TypeVar('U')
E = t.TypeVar('E', bound=enum.Enum)
DbSelf = t.TypeVar('DbSelf', bound='MyDb')
QuerySelf = t.TypeVar('QuerySelf', bound='_MyQuery')


class MySession:  # pragma: no cover
    def bulk_save_objects(self, objs: t.Sequence['Base']) -> None:
        ...

    @t.overload
    def query(self, __x: 'DbColumn[T]') -> '_MyQuery[T]':
        ...

    @t.overload  # NOQA
    def query(self, __x: 'RawTable') -> '_MyQuery[RawTable]':
        ...

    @t.overload  # NOQA
    def query(self, __x: t.Type[T]) -> '_MyQuery[T]':
        ...

    @t.overload  # NOQA
    def query(self, __x: t.Type[T],
              __y: 'DbColumn[Z]') -> '_MyQuery[t.Tuple[T, Z]]':
        ...

    @t.overload  # NOQA
    def query(self, __x: t.Type[T],
              __y: t.Type[Z]) -> '_MyQuery[t.Tuple[T, Z]]':
        ...

    @t.overload  # NOQA
    def query(
        self,
        __x: T,
        __y: Z,
        __z: Y,
    ) -> '_MyQuery[t.Tuple[T, Z, Y]]':
        ...

    @t.overload  # NOQA
    def query(
        self,
        __x: T,
        __y: Z,
        __z: Y,
        __j: U,
    ) -> '_MyQuery[t.Tuple[T, Z, Y, U]]':
        ...

    def query(self, *args: t.Any) -> '_MyQuery[t.Any]':  # NOQA
        ...

    def add(self, arg: 'Base') -> None:
        ...

    def flush(self) -> None:
        ...

    def commit(self) -> None:
        ...

    def delete(self, arg: 'Base') -> None:
        ...

    def expunge(self, arg: 'Base') -> None:
        ...

    def expire_all(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def begin_nested(self) -> t.ContextManager:
        ...


class DbType(t.Generic[T]):  # pragma: no cover
    ...


class RawTable:  # pragma: no cover
    c: t.Any


class MyDb:  # pragma: no cover
    session: MySession
    Float: DbType[float]
    Integer: DbType[int]
    Unicode: DbType[str]
    DateTime: DbType[datetime]
    Boolean: DbType[bool]
    ForeignKey: t.Callable
    String: t.Callable[[DbSelf, int], DbType[str]]
    Enum: t.Callable[[DbSelf, t.Type[E]], DbType[E]]
    init_app: t.Callable
    engine: t.Any

    def Table(self, name: str, *args: T) -> RawTable:
        ...

    @t.overload
    def Column(self, name: str, type_: DbType[T], *args: t.Any,
               **rest: t.Any) -> T:
        ...

    @t.overload  # NOQA
    def Column(self, type_: DbType[T], *args: t.Any, **rest: t.Any) -> T:
        ...

    def Column(self, *args: t.Any, **kwargs: t.Any) -> t.Any:  # NOQA
        ...

    def PrimaryKeyConstraint(self, *args: t.Any) -> t.Any:
        ...

    @t.overload
    def relationship(self, name: str, *args: t.Any, **kwargs: t.Any) -> t.Any:
        ...

    @t.overload  # NOQA
    def relationship(self, name: t.Type[T], *args: t.Any,
                     **kwargs: t.Any) -> T:
        ...

    def relationship(self, *args: t.Any, **kwargs: t.Any) -> t.Any:  # NOQA
        ...

    def backref(self, name: str, *args: t.Any, **kwargs: t.Any) -> t.Any:
        ...


class DbColumn(t.Generic[T]):  # pragma: no cover
    '''This class is used for type checking only.

    It has no implementation and instantiating an instance raises an error.
    '''

    def __init__(self) -> None:
        raise ValueError

    def in_(self, val: t.Union[t.Iterable[T], 'DbColumn[T]']) -> 'DbColumn[T]':
        ...

    def isnot(self, val: t.Optional[T]) -> 'DbColumn[bool]':
        ...

    def label(self, name: str) -> 'DbColumn[T]':
        ...

    def is_(self, val: t.Optional[T]) -> 'DbColumn[T]':
        ...

    def __invert__(self) -> 'DbColumn[T]':
        ...


class Base:  # pragma: no cover
    query = None  # type: t.ClassVar[t.Any]

    def __init__(self, *args: t.Any, **kwargs: t.Any) -> None:
        pass


class _MyQuery(t.Generic[T], t.Iterable):  # pragma: no cover
    delete: t.Callable[[QuerySelf], None]
    scalar: t.Callable[[QuerySelf], T]
    as_scalar: t.Callable[[QuerySelf], '_MyQuery[T]']
    subquery: t.Callable[[QuerySelf, str], RawTable]
    limit: t.Callable[[QuerySelf, int], '_MyQuery[T]']
    with_for_update: t.Callable[[QuerySelf], '_MyQuery[T]']  # NOQA
    first: t.Callable[[QuerySelf], t.Optional[T]]
    exists: t.Callable[[QuerySelf], DbColumn[bool]]
    count: t.Callable[[QuerySelf], int]
    one: t.Callable[[QuerySelf], T]
    one_or_none: t.Callable[[QuerySelf], t.Optional[T]]
    all: t.Callable[[QuerySelf], t.List[T]]
    __iter__: t.Callable[[QuerySelf], t.Iterator[T]]

    def get(self, arg: t.Any) -> t.Optional[T]:
        ...

    def update(
        self,
        vals: t.Mapping[str, t.Any],
        synchronize_session: str = '__NOT_REAL__'
    ) -> None:
        ...

    def join(self, *args: t.Any, **kwargs: t.Any) -> '_MyQuery[T]':
        ...

    def order_by(self, *args: t.Any, **kwargs: t.Any) -> '_MyQuery[T]':
        ...

    def filter(self, *args: t.Any, **kwargs: t.Any) -> '_MyQuery[T]':
        ...

    def filter_by(self, *args: t.Any, **kwargs: t.Any) -> '_MyQuery[T]':
        ...

    def options(self, *args: t.Any) -> '_MyQuery[T]':
        ...

    def having(self, *args: t.Any) -> '_MyQuery[T]':
        ...

    def group_by(self, arg: t.Any) -> '_MyQuery[T]':
        ...

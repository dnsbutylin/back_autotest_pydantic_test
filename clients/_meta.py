"""Requests meta"""

from functools import wraps
from types import MethodType
from typing import Any, Callable

from ._request import Method, Request
from ._session import Session


class MetaCategory:  # pylint: disable=too-few-public-methods
    """Meta category class"""

    _session: Session

    def __init__(self, session: Session) -> None:
        self._session = session

    @property
    def s(self) -> Session:  # pylint: disable=invalid-name
        """Return session"""
        return self._session


class request:  # noqa pylint: disable=invalid-name
    """Класс с декораторами методов"""

    @classmethod
    def request(cls, method: Method, endpoint: str) -> Callable[..., Any]:
        """Базовый декоратор"""

        def wrapper(func: MethodType) -> property:
            @wraps(func)
            def _request(self: Session | MetaCategory) -> Request:
                return Request(
                    session=self.s if isinstance(self, MetaCategory) else self,
                    method=method,
                    endpoint=endpoint,
                )

            return property(_request, None, None)

        return wrapper

    @classmethod
    def get(cls, endpoint: str) -> Callable[..., Any]:
        """Декоратор GET запроса"""
        return cls.request(method=Method.GET, endpoint=endpoint)

    @classmethod
    def post(cls, endpoint: str) -> Callable[..., Any]:
        """Декоратор POST запроса"""
        return cls.request(method=Method.POST, endpoint=endpoint)

    @classmethod
    def put(cls, endpoint: str) -> Callable[..., Any]:
        """Декоратор PUT запроса"""
        return cls.request(method=Method.PUT, endpoint=endpoint)

    @classmethod
    def delete(cls, endpoint: str) -> Callable[..., Any]:
        """Декоратор DELETE запроса"""
        return cls.request(method=Method.DELETE, endpoint=endpoint)


def category(cls: type[MetaCategory]) -> Callable[..., Any]:
    """Декоратор категории"""

    def wrapper(func: MethodType) -> property:
        """Обертка декоратора"""

        @wraps(func)
        def _category(self: Session | MetaCategory) -> MetaCategory:
            return cls(session=self.s if isinstance(self, MetaCategory) else self)

        return property(_category, None, None)

    return wrapper

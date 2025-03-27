"""Реализация ваимодействия с сессией"""

import logging
from typing import Any, Self

import requests

from src.user_types import Missing

logger = logging.getLogger(__package__)


class Session:
    """Класс сессии"""

    def __init__(self, host: str, *, verify: bool = False, default_path: dict[str, Any] | None = None):
        self._host = host.removesuffix("/")
        self._session = requests.Session()
        self._session.verify = verify
        self._counter = 0
        self._default_path = default_path or {}

    @property
    def host(self) -> str:
        """Возвращает хост сессии"""
        return self._host

    def add_headers(self, headers: dict[str, Any]) -> None:
        """Добавить хедеры в сессию"""
        self._session.headers.update(headers)

    def add_token(self, token: str) -> None:
        """Добавить bearer токен"""
        self.add_headers({"Authorization": f"Bearer {token}", "Content-Type": "application/json; charset=utf-8"})

    def request(self, *, endpoint: str, method: str, extra: dict, **kwargs) -> requests.Response:
        """Запрос в сессии"""
        self._counter += 1
        path = extra.get("path", {})
        endpoint = endpoint.format_map(Missing(self._default_path | path))
        url = f"{self.host}{endpoint}"
        try:
            logger.info(f"{type(self).__name__}({id(self)}) Request {self._counter}: {method} {url} {kwargs}")
            response = self._session.request(method=method, url=url, **kwargs)
        except Exception as error:
            logger.error(f"{type(self).__name__}({id(self)}) Error {self._counter}: {error}")
            raise error
        logger.info(
            f"{type(self).__name__}({id(self)}) Response {self._counter}: "
            f"{response.status_code} {response.request.method} {response.request.url}\n{response.text}",
        )
        return response

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        self._session.close()

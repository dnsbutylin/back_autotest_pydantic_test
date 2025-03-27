"""Реализует отправку запроса и последующую его обработку"""

import logging
import time
import urllib.parse as urlparse
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import StrEnum
from json import loads
from typing import Any, Callable, Final, Self

from box import Box, BoxList

# import marshmallow_dataclass
from pydantic import BaseModel, ValidationError
from requests import Response

from src.cases import step

from ._session import Session

# from src.schemas import Schema


logger = logging.getLogger(__package__)

for log in "urllib3.connectionpool", "charset_normalizer":
    logging.getLogger(log).setLevel(logging.INFO)

DEFAULT_WAIT: Final[int] = 60
DEFAULT_INTERVAL: Final[int] = 1


class Handler:
    """Дефолтные обработчики ответа"""

    @staticmethod
    def json(response: Response) -> Box | BoxList | str:
        """Десериализация json"""
        _json = loads(response.text)
        if isinstance(_json, dict):
            return Box(_json, box_dots=True)
        if isinstance(_json, list):
            return BoxList(_json, box_dots=True)
        return _json


class Method(StrEnum):
    """Enum методов запроса"""

    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"


class WaitRequestError(Exception):
    """Базовый exception для ожидания"""


@dataclass(slots=True, kw_only=True)
class WaitRequest:
    """Ожидание"""

    request: "Request"
    func: Callable[[Any], Any] | None
    timeout: int | float = field(default=DEFAULT_WAIT)
    interval: int | float = field(default=DEFAULT_INTERVAL)
    err_msg: str | None = field(default=None)

    def __call__(  # noqa: CCR001
        self,
        status: int,
        *,
        handler: Callable[[Response], Any] | str | None = Handler.json,
        schema: type[BaseModel] | list[type[BaseModel]] | None = None,
        step_name: str | None = None,
        return_result: bool = False,
    ) -> Any:
        """Выполнить запрос"""
        error = None
        with step(step_name):
            start_time = time.time()
            logger.debug(f"Start wait: timeout: {self.timeout}")
            while time.time() - start_time < self.timeout:
                try:
                    response = self.request(status=status, handler=handler, schema=schema)
                    if result := (self.func(response) if self.func is not None else True):
                        logger.debug("Wait done")
                        return result if return_result else response
                    raise WaitRequestError(self.err_msg or f"{result=} request: {self.request}")
                except Exception as err:  # pylint: disable=broad-exception-caught
                    logger.error(f"Wait error: {err}")
                    error = err
                time.sleep(self.interval)
            raise error  # type: ignore


class Request:
    """Класс запроса"""

    def __init__(self, session: Session, method: Method, endpoint: str):
        """
        :param session: Объект сессии
        :param method: Метод запроса (enum: Method)
        :param endpoint: Конечная точка запроса (без хоста, начинается с /)
        """
        self._method = method
        self._endpoint = endpoint
        self._session = session
        self._args: dict[str, Any] = {}
        self._extra: dict[str, Any] = {}

    @property
    def method(self) -> Method:
        """Возвращает текущий метод запроса"""
        return self._method

    @property
    def endpoint(self) -> str:
        """Возвращает конечную точку запроса"""
        return self._endpoint

    def set_arguments(self, **kwargs) -> Self:
        """Добавление/обновление аргументов для передачи в запрос"""
        self._args.update(kwargs)
        return self

    def query(self, data: Any = None, **kwargs) -> Self:
        """
        Добавление query параметров к запросу
        :param data: Словарь или ДатаКласс
        :param kwargs: Именованные параметры
        """
        arg = self._args.setdefault("params", {})
        if is_dataclass(data):
            arg.update(data.as_dict() if hasattr(data, "as_dict") else asdict(data))
        elif isinstance(data, dict):
            arg.update(data)
        arg.update(kwargs)
        return self

    def path(self, _quote: bool = False, **kwargs) -> Self:
        """
        Подставляет значения в урл
        :param _quote: Экранирование
        """
        path = self._extra.setdefault("path", {})
        if _quote:
            kwargs = {k: urlparse.quote(v, safe="") for k, v in kwargs.items()}
        path.update(kwargs)
        return self

    def form_data(self, _data: Any = None, _set_content_type: bool = False, **kwargs) -> Self:
        """
        Добавляет в запрос данные для отправки как form data
        """
        values = {}
        if is_dataclass(_data):
            values.update(asdict(_data))
        values.update(kwargs)
        self.set_arguments(data=values)
        if _set_content_type:
            self.set_headers({"Content-Type": "application/x-www-form-urlencoded"})
        return self

    def set_headers(self, headers: dict) -> Self:
        """Добавить headers в запрос"""
        arg = self._args.setdefault("headers", {})
        arg.update(headers)
        return self

    def body(self, _data: Any = None, **kwargs) -> Self:
        """Добавляет в запрос данные для отправки в тело запроса"""
        arg = self._args.setdefault("json", {})
        if is_dataclass(_data):
            arg.update(_data.as_dict() if hasattr(_data, "as_dict") else asdict(_data))
        elif isinstance(_data, dict):
            arg.update(_data)
        arg.update(kwargs)
        return self

    def __repr__(self):
        return f"Request <{self._method} {self._endpoint}>"

    def wait(
        self,
        func: Callable[[Any], Any],
        timeout: int | float = DEFAULT_WAIT,
        interval: int | float = DEFAULT_INTERVAL,
        err_msg: str | None = None,
    ) -> WaitRequest:
        """Ожидание"""
        return WaitRequest(request=self, func=func, timeout=timeout, interval=interval, err_msg=err_msg)

    def __call__(
        self,
        status: int,
        *,
        handler: Callable[[Response], Any] | str | None = Handler.json,
        schema: type[BaseModel] | list[type[BaseModel]] | None = None,
        step_name: str | None = None,
    ) -> Any:
        """
        Непосредственый запрос
        :param status: Ожидаемый код ответа
        :param handler: Функция обработчик ответа или имя обработчика из Handlers
        :param step_name: Имя степа для передачи в allure
        :return: Если не указан handler возврацает requests.Response. Если указан handler резльтат обработки
        """
        with step(_title=step_name):
            with step(f"Запрос: {self._method} {self._endpoint}", args=self._args):
                response = self._session.request(
                    endpoint=self.endpoint,
                    method=self.method,
                    extra=self._extra,
                    **self._args,
                )
            with step(f"Проверить код ответа: '{status}'"):
                assert (
                    response.status_code == status
                ), f"{self} Status code error: Expected: '{status}'. Actual: '{response.status_code}'"
            if callable(handler):
                with step(f"Десериализация ответа хендлером: {handler.__name__}"):
                    response = handler(response)  # type: ignore
            elif isinstance(handler, str) and hasattr(Handler, handler):
                with step(f"Десериализация ответа хендлером: {handler}"):
                    response = getattr(Handler, handler)(response)
            if schema is not None:
                self.__validator(response, schema)
            return response

    @staticmethod
    def __validator(data: Any, schema: BaseModel | list[BaseModel]) -> None:
        """Schema validator"""
        if isinstance(data, Box):
            data = data.to_dict()
        elif isinstance(data, BoxList):
            data = [item.to_dict() for item in data]
        elif isinstance(data, Response):
            data = data.json()
        try:
            schema(**data)
        except ValidationError as e:
            for error in e.errors():
                field = error.get("loc", ["unknown"])[0]
                error_type = error.get("type", "unknown")
                message = error.get("msg", "unknown error")
                print(f"Ошибка в поле '{field}': {message} (тип ошибки: {error_type})")

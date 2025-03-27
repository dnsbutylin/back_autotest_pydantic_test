"""Модуль для хранения функций реализующих взаимодействие с allure и тест кейсами"""

from contextlib import nullcontext
from typing import Any

import allure
from allure_commons._allure import StepContext


def _parameters(**kwargs) -> dict[str, str]:
    """Приводит все аргументы к строке"""
    return {str(key): str(value) for key, value in kwargs.items()}


def step(
    _title: str | None,
    _params: dict[Any, Any] | None = None,
    _empty: bool = False,
    **kwargs,
) -> StepContext | nullcontext:
    """
    Менеджер контекста для степа
    :param _title: Название степа
    :param _params: Параметры передаваемые в степ
    :param _empty: Пустой степ не попадает в allure
    :param kwargs: Именовынные параметры передаваемые в степ
    """
    if _empty or _title is None:
        return nullcontext()
    _params = _params or {}
    _params.update(**kwargs)
    params = _parameters(**_params)
    return StepContext(title=_title, params=params)


def case(*, id: int, title: str) -> Any:  # pylint: disable=redefined-builtin
    """
    Декоратор для интеграции c Allure
    :param id: ID Тест кейса
    :param title: Название тест кейса
    """

    def _wrap(func: Any) -> Any:
        func = allure.id(str(id))(func)
        func = allure.title(title)(func)
        func = allure.label("layer", "API")(func)
        if func.__doc__:
            func = allure.description(func.__doc__)(func)
        return func

    return _wrap


__all__ = ["case", "step"]

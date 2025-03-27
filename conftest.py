"""Конфигурационный файл"""

# pylint: disable=redefined-outer-name

import logging
from pathlib import Path
from typing import Iterator

import pytest
import urllib3
from environs import Env
from pytest import Function

from clients import UsersClient
from src.db_client import DataBaseClient
from src.user_types import DBSettings

for i in ("faker.factory",):
    logging.getLogger(i).setLevel(level=logging.ERROR)

urllib3.disable_warnings()

logger = logging.getLogger("pytest")

PROJECT_ROOT = Path(__file__).parent
ALLURE_RESULTS_DIR = PROJECT_ROOT / "allure-results"


def pytest_addoption(parser: pytest.Parser) -> None:
    """Парсер параметров запуска"""
    parser.addoption(
        "--envfile",
        default="test.env",
        help="Полное имя файла из корня проекта",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    """Конфигурирует путь до allure-result внезависимости с какой глубины папки запущен тест"""

    # Создание директории, если она не существует
    ALLURE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Установка опции для Allure
    config.option.allure_report_dir = str(ALLURE_RESULTS_DIR)


@pytest.fixture(scope="session")
def _env(pytestconfig) -> Env:
    """
    Чтение .env файла
    """
    env = Env()
    filename = pytestconfig.getoption("envfile")
    env.read_env(filename)
    return env


@pytest.fixture(scope="module")
def not_authorize_users_client(
    _env: Env,
) -> Iterator[UsersClient]:
    """Не авторизованный клиент Users сервиса"""
    with UsersClient(
        host=_env.str("HOST"),
    ) as session:
        yield session


@pytest.fixture(scope="session")
def db_config(_env: Env) -> DBSettings:
    """Настройки базы"""
    with _env.prefixed("DATABASE_"):
        return DBSettings(
            host=_env.str("HOST"),
            port=_env.int("PORT"),
            name=_env.str("NAME"),
            user=_env.str("USER"),
            password=_env.str("PASSWORD"),
        )


@pytest.fixture(scope="module")
def db_client(db_config: DBSettings) -> DataBaseClient:  # type:ignore[misc]
    """Клиент базы данных"""
    with DataBaseClient(**db_config.get()) as data_base:  # type:ignore[arg-type]
        yield data_base


def pytest_runtest_call(item: Function) -> None:
    """Start test logging"""
    logger.debug(f"Test started: {item.nodeid}")


def pytest_runtest_teardown(item: Function) -> None:
    """End test logging"""
    logger.debug(f"Test finished: {item.nodeid}")

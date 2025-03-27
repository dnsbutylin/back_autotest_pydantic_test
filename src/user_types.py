"""Модуль для хранения пользовательских типов"""

from dataclasses import dataclass, field
from typing import Any


class Missing(dict):
    """Словарь используемый для форматирования строк"""

    def __missing__(self, key: Any) -> str:
        return "{%s}" % key  # pylint: disable=C0209


@dataclass(frozen=True, slots=True, kw_only=True)
class DBSettings:
    """DB connection settings"""

    host: str
    port: int
    name: str
    user: str
    password: str = field(repr=False)

    def get(self) -> dict[str, str | int]:
        """Получить словарь"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.name,
            "user": self.user,
            "password": self.password,
        }

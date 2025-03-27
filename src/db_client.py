import logging
from dataclasses import dataclass, field
from typing import Any, Self

import allure
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from src.models import OrderResponse, UserResponse

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class DataBaseMeta:
    """Коннектор к БД"""

    host: str
    port: int
    database: str
    user: str
    password: str
    engine: Any = field(init=False, default=None)
    session: Session = field(init=False, default=None)

    def connect(self) -> None:
        """Коннект"""
        connection_string = f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
        self.engine = create_engine(connection_string)
        logger.debug(f"Connection DB: {self.host}:{self.port} {self.database} {self.user}")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.session = SessionLocal()
        logger.debug("Create session")

    def __enter__(self) -> Self:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        if self.session is not None:
            logger.debug("Close session")
            self.session.close()
        if self.engine is not None:
            logger.debug("Dispose engine")
            self.engine.dispose()

    def execute(self, statement: str, params: dict = None) -> Any:
        """Выполнить SQL"""
        logger.debug(f"Execute: {statement} {params}")
        try:
            return self.session.execute(statement, params)
        except SQLAlchemyError as err:
            logger.error(f"Execute error: {err}")
            raise err

    def fetchone(self, statement: str, params: dict = None) -> Any:
        """Получить одну строку"""
        logger.debug(f"Fetch one: {statement} {params}")
        try:
            result = self.execute(statement, params)
            return result.fetchone()
        except SQLAlchemyError as err:
            logger.error(f"Fetch one error: {err}")
            raise err

    def commit(self) -> None:
        """Коммит изменений"""
        logger.debug("Commit transaction")
        try:
            self.session.commit()
        except SQLAlchemyError as err:
            logger.error(f"Commit error: {err}")
            self.session.rollback()
            raise err


class DataBaseClient(DataBaseMeta):
    """Клиент БД"""

    @allure.step("Получить пользователя из базы данных по ID")
    def get_user_by_id(self, user_id: int) -> UserResponse:
        """Получить пользователя из базы данных по ID"""
        statement = "SELECT id, username, email, age FROM users WHERE id=:id"
        try:
            result = self.fetchone(statement, {"id": user_id})
            if result is None:
                raise ValueError(f"User with ID {user_id} not found in the database.")
            # Преобразование кортежа в словарь
            return UserResponse.from_db_tuple(result)
        except SQLAlchemyError as err:
            logger.error(f"Error fetching user by ID: {err}")
            raise err
        except ValidationError as err:
            logger.error(f"Validation error for user data: {err}")
            raise err

    @allure.step("Получить заказ из базы данных по ID")
    def get_order_by_id(self, order_id: int) -> OrderResponse:
        """Получить заказ из базы данных по ID"""
        statement = "SELECT id, user_id, product_name, quantity FROM orders WHERE id=:id"
        try:
            result = self.fetchone(statement, {"id": order_id})
            if result is None:
                raise ValueError(f"Order with ID {order_id} not found in the database.")
            # Преобразование кортежа в словарь
            return OrderResponse.from_db_tuple(result)
        except SQLAlchemyError as err:
            logger.error(f"Error fetching order by ID: {err}")
            raise err
        except ValidationError as err:
            logger.error(f"Validation error for order data: {err}")
            raise err

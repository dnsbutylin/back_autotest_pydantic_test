from typing import Tuple, Type, TypeVar

from faker import Faker
from pydantic import BaseModel, EmailStr, Field

fake = Faker()


T = TypeVar("T", bound="BaseModelWithDB")


class BaseModelWithDB(BaseModel):
    @classmethod
    def from_db_tuple(cls: Type[T], db_tuple: Tuple) -> T:
        """Создать объект модели из кортежа, полученного из БД"""
        keys = cls.__fields__.keys()  # Получаем имена полей модели
        data = dict(zip(keys, db_tuple))  # Преобразуем кортеж в словарь
        return cls(**data)  # Валидируем данные через Pydantic


# Модель для создания пользователя
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, pattern="^[a-zA-Z0-9]")
    email: EmailStr
    age: int = Field(..., gt=0, lt=100)

    @classmethod
    def generate(cls) -> "UserCreate":
        """Генерация данных для создания пользователя"""
        return cls(
            username=fake.user_name(),
            email=fake.email(),
            age=fake.random_int(min=1, max=99),
        )


# Модель для ответа о пользователе
class UserResponse(BaseModelWithDB):
    id: int
    username: str
    email: EmailStr
    age: int


# Модель для создания заказа
class OrderCreate(BaseModel):
    user_id: int
    product_name: str
    quantity: int = Field(..., gt=0)

    @classmethod
    def generate(cls, user_id: int) -> "OrderCreate":
        """Генерация данных для создания заказа"""
        return cls(
            user_id=user_id,
            product_name=fake.word(),
            quantity=fake.random_int(min=1, max=10),
        )


# Модель для ответа о заказе
class OrderResponse(BaseModelWithDB):
    id: int
    user_id: int
    product_name: str
    quantity: int


# Модель для обработки ошибок
class UserError(BaseModel):
    error: str

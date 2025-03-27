from http import HTTPStatus

from clients import UsersClient
from src.cases import case, step
from src.db_client import DataBaseClient
from src.models import OrderCreate, OrderResponse, UserCreate, UserError, UserResponse


@case(id=1001, title="Проверка создания пользователя и сохранения данных в БД")
def test_creating_user_and_saving_to_db(
    not_authorize_users_client: UsersClient,
    db_client: DataBaseClient,
):
    """Тест на создание пользователя через API и проверку сохранения данных в БД"""
    user_data = UserCreate.generate()
    with step("Создать пользователя через API"):
        request = not_authorize_users_client.post.create_user.body(
            _data=user_data,
        )
        request(
            status=HTTPStatus.CREATED,
            step_name="Создать пользователя",
            schema=UserResponse,
            handler=None,
        )

    with step("Проверить, что пользователь сохранен в базе данных"):
        # Данные из БД возвращаются в виде кортежа
        user_from_db = db_client.get_user_by_id(user_data.id)
        db_user = UserResponse.from_db_tuple(db_tuple=user_from_db)
        assert db_user == user_data


@case(id=1002, title="Проверка обработки ошибки при создании пользователя с дублирующимся username")
def test_creating_user_with_duplicate_username(
    not_authorize_users_client: UsersClient,
    db_client: DataBaseClient,
):
    """Тест на обработку ошибки при создании пользователя с дублирующимся username"""

    user_data = UserCreate.generate()
    with step("Создать пользователя через API"):
        request = not_authorize_users_client.post.create_user.body(
            _data=user_data,
        )
        request(
            status=HTTPStatus.CREATED,
            step_name="Создать пользователя",
            schema=UserResponse,
            handler=None,
        )
    with step("Проверить, что пользователь сохранен в базе данных"):
        user_from_db = db_client.get_user_by_id(user_data.id)
        db_user = UserResponse.from_db_tuple(db_tuple=user_from_db)
        assert db_user == user_data

    with step("Попытаться создать пользователя с таким же username"):
        duplicate_name_user_data = user_data
        request = not_authorize_users_client.post.create_user.body(
            _data=duplicate_name_user_data,
        )
        response = request(
            status=HTTPStatus.BAD_REQUEST,
            step_name="Создать пользователя с дублирующимся username",
            schema=UserError,
            handler=None,
        )

    with step("Проверить, что ошибка корректно обработана"):
        assert (
            response.json()["error"] == "Username already exists"
        ), f"Expected error message: 'Username already exists', Got: {response.json()['error']}"


@case(id=1003, title="Проверка сохранения заказа в базе данных")
def test_creating_order(
    not_authorize_users_client: UsersClient,
    db_client: DataBaseClient,
):
    """Тест на создание заказа через API и проверку сохранения данных в БД"""

    order_data = OrderCreate.generate(
        user_id=1,
    )
    with step("Создать заказ через API"):
        request = not_authorize_users_client.post.create_order.body(
            _data=order_data,
        )
        request(
            status=HTTPStatus.CREATED,
            step_name="Создать заказ",
            schema=OrderResponse,
            handler=None,
        )

    with step("Проверить, что заказ сохранен в базе данных"):
        order_from_db = db_client.get_order_by_id(order_data.id)  # type: ignore
        assert order_from_db == order_data


@case(id=1004, title="Проверка получения информации о пользователе по ID")
def test_get_user_by_id(
    not_authorize_users_client: UsersClient,
    db_client: DataBaseClient,
):
    """Тест на получение информации о пользователе через API и проверку данных"""

    user_id = 11  # Предполагаем, что пользователь с таким ID существует в базе данных

    with step("Получить информацию о пользователе через API"):
        request = not_authorize_users_client.get.user_by_id(user_id=user_id)
        response = request(
            status=HTTPStatus.OK,
            step_name="Получить информацию о пользователе",
            schema=UserResponse,
            handler=None,
        )
        user_data = UserResponse(**response.json())

    with step("Проверить, что данные пользователя корректны"):
        user_from_db = db_client.get_user_by_id(user_id)
        assert user_data == user_from_db, f"Ожидалось: {user_from_db}, Получено: {user_data}"


@case(id=1005, title="Проверка получения информации о заказе по ID")
def test_get_order_by_id(
    not_authorize_users_client: UsersClient,
    db_client: DataBaseClient,
):
    """Тест на получение информации о заказе через API и проверку данных"""

    order_id = 11  # Предполагаем, что заказ с таким ID существует в базе данных

    with step("Получить информацию о заказе через API"):
        request = not_authorize_users_client.get.get_order.path(order_id=order_id)
        response = request(
            status=HTTPStatus.OK,
            step_name="Получить информацию о заказе",
            schema=OrderResponse,
            handler=None,
        )
        order_data = OrderResponse(**response.json())

    with step("Проверить, что данные заказа корректны"):
        order_from_db = db_client.get_order_by_id(order_id)
        assert order_data == order_from_db, f"Ожидалось: {order_from_db}, Получено: {order_data}"

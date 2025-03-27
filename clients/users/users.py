"""Users Client https://jsonplaceholder.typicode.com"""

from .._meta import MetaCategory, request
from .._request import Request
from .._session import Session


class UsersGet(MetaCategory):
    """Get запросы"""

    @request.get("/users/{user_id}")
    def get_user(self) -> Request:
        """get_address"""

    @request.get("/orders/{order_id}")
    def get_order(self) -> Request:
        """login_info"""


class UsersPost(MetaCategory):
    """Post запросы"""

    @request.post("/users")
    def create_user(self) -> Request:
        """services_price"""

    @request.post("/orders")
    def create_order(self) -> Request:
        """login"""


class UsersClient(Session):
    """Клиент для взаимодействия с сервисом авторизации"""

    @property
    def get(self) -> UsersGet:
        """GET Requests"""
        return UsersGet(self)

    @property
    def post(self) -> UsersPost:
        """POST Requests"""
        return UsersPost(self)

# Auto-generate 2025-03-26 20:44:59 UTC

from .._meta import MetaCategory
from .._request import Request
from .._session import Session

class UsersGet(MetaCategory):
    @property
    def get_user(self) -> Request: ...
    @property
    def get_order(self) -> Request: ...

class UsersPost(MetaCategory):
    @property
    def create_user(self) -> Request: ...
    @property
    def create_order(self) -> Request: ...

class UsersClient(Session):
    @property
    def get(self) -> UsersGet: ...
    @property
    def post(self) -> UsersPost: ...

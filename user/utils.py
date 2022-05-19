import uuid
from rest_framework.response import Response
from rest_framework.serializers import ReturnDict

from django.core.cache import cache

from uuid import uuid4

from .models import User

"""
Token generator class

Handles token generation and caching
"""


class TokenHandler(object):
    __token = None

    def __init__(self):
        self.__token = str(uuid4())

    def create_token(
        self, user_id: int, instance: str, testing: bool = False
    ) -> bool | str:
        cache.set(instance + self.__token, user_id, timeout=1000 * 60 * 60 * 24 * 3)
        if testing:
            return self.__token
        return True

    def token(self) -> str:
        return self.__token

    def retrive_token_data(self, token: str, instance: str) -> User:
        user_id = cache.get(instance + token)
        return User.objects.filter(id=user_id).first()

    def delete_cached_token(self, token: str, instance: str) -> None:
        cache.delete(instance + token)


""""
Create message class
    
Generates messages according to API responses(success, error)
"""


class CreateMessage(object):
    __instance = None

    @classmethod
    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = object.__new__(cls)
            cls.__instance._initialized = False
        return cls.__instance

    def __init__(self, *args, **kwargs):
        if self._initialized:
            return
        self._initialized = True

    @classmethod
    def get(cls):
        if cls.__instance is not None:
            return cls.__instance
        return cls()

    def create_success_response(
        self, message: str | dict | User, status: int
    ) -> Response:
        return Response(
            {"success": message} if type(message) is str else message, status=status
        )

    def create_error_response(self, message: str, status: int) -> Response:
        return Response({"error": message}, status=status)

    def create_user_response(self, data: User | ReturnDict) -> Response:
        if type(data) is ReturnDict:
            return Response(
                {
                    "name": data["first_name"],
                    "last_name": data["last_name"],
                    "email": data["email"],
                }
            )
        return Response(
            {"name": data.first_name, "last_name": data.last_name, "email": data.email}
        )

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.contrib.auth import login, logout
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
from django.middleware.csrf import get_token

from uuid import uuid4

from .serializer import (
    LoginSerializer,
    RegisterSerializer,
    UserSerializer,
    UpdatePasswordSerializer,
    ConfirmAccountSerializer,
)
from .utils import CreateMessage, TokenHandler
from .models import User


class LoginView(APIView):
    permission_classes = (AllowAny,)
    authentication_classes = (SessionAuthentication,)

    def post(self, request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        login(request, user)
        return CreateMessage.get().create_user_response(UserSerializer(user).data)


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request) -> Response:
        logout(request)
        return Response("Logout success")


class RegisterView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request) -> Response:
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CreateMessage.get().create_success_response(
                message="User created successfully", status=200
            )
        return CreateMessage.get().create_error_response(
            message="There was an error while creating your account", status=400
        )


class UpdateUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request) -> Response:
        user = User.objects.get(pk=self.request.user.pk)
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return CreateMessage.get().create_success_response(
                "User updated successfully", status=200
            )
        return CreateMessage.get().create_error_response(
            "There was an error while updating user", status=500
        )


class ConfirmAccountView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, token) -> Response:
        if not token:
            return CreateMessage.get().create_error_response(
                message="No token is provided", status=400
            )
        token_handler = TokenHandler()
        user = token_handler.retrive_token_data(
            token, str(settings.CONFIRM_ACCOUNT_PREFIX)
        )
        if not user:
            return CreateMessage.get().create_error_response("Token expired", 403)
        serializer = ConfirmAccountSerializer(instance=user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return CreateMessage.get().create_success_response(
                "Account activated successfully", status=200
            )
        return CreateMessage.get().create_error_response(
            "Token is expired or not valid", status=400
        )


class CurrentUserView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, *args, **kwargs) -> Response:
        if not self.request.user:
            return CreateMessage.get().create_error_response(
                message="There is no user in session", status=400
            )
        return CreateMessage.get().create_user_response(data=self.request.user)


class ForgotPasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request) -> Response:
        user = User.objects.filter(email=request.data["email"]).first()
        if not user:
            return CreateMessage.get().create_error_response(
                "User does not exist in database!", status=400
            )
        token = TokenHandler()
        token.create_token(user.id, str(settings.FORGOT_PASSWORD_PREFIX))
        send_mail(
            subject="Reset password!",
            message=f"Your link to reset password is: {token.token()}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[
                user.email,
            ],
        )
        return CreateMessage.get().create_success_response(
            "Token is sent to email!", status=200
        )


class ChangePasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, token) -> Response:
        if not token:
            return CreateMessage.get().create_error_response(
                message="No token is provided", status=400
            )

        token_handler = TokenHandler()
        user = token_handler.retrive_token_data(
            token, str(settings.FORGOT_PASSWORD_PREFIX)
        )

        if not user:
            return CreateMessage.get().create_error_response("Token expired", 400)

        serializer = UpdatePasswordSerializer(user, request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return CreateMessage.get().create_success_response(
                "Password changed successfully", status=200
            )
        return CreateMessage.get().create_error_response(
            "There was an error", status=400
        )


class CsrfTokenView(APIView):
    def get(self, request):
        response = Response({"detail": "CSRF cookie set"})
        response["X-CSRFToken"] = get_token(request)
        return response

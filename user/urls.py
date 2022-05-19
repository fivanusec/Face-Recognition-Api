from django.urls import path
from .views import (
    LoginView,
    RegisterView,
    LogoutView,
    UpdateUserView,
    ConfirmAccountView,
    ForgotPasswordView,
    ChangePasswordView,
    CurrentUserView,
    CsrfTokenView,
)

app_name = "users"

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("update-user/", UpdateUserView.as_view(), name="update"),
    path(
        "confirm-account/<str:token>",
        ConfirmAccountView.as_view(),
        name="confirm-account",
    ),
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path(
        "change-password/<str:token>",
        ChangePasswordView.as_view(),
        name="change-password",
    ),
    path("me/", CurrentUserView.as_view()),
    path("csrf/", CsrfTokenView.as_view(), name="csrf"),
]

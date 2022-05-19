from django.test import TestCase
from rest_framework.test import APITestCase

from django.urls import reverse
from django.conf import settings

from .models import User
from .utils import TokenHandler, CreateMessage

from json import loads as json_loads


class LoginTest(APITestCase):
    url = reverse("users:login")
    user = None

    def setUp(self):
        self.user = User.objects.create_user(
            email="foo@bar.com", password="test_test_test124", is_active=True
        )

    def test_authentication_without_password(self):
        response = self.client.post(self.url, {"email": "john@snow.com"})
        self.assertEqual(400, response.status_code)

    def test_authentication_with_wrong_password(self):
        response = self.client.post(
            self.url, {"email": self.user.email, "password": "I_know"}
        )
        self.assertEqual(400, response.status_code)

    def test_authentication_with_user_not_activated(self):
        user = User.objects.create_user(
            email="email@mail.com", password="test123456789"
        )
        response = self.client.post(
            self.url, {"email": user.email, "password": "test123456789"}, format="json"
        )
        self.assertEqual(400, response.status_code)

    def test_authentication_with_valid_data(self):
        response = self.client.post(
            self.url,
            {"email": self.user.email, "password": "test_test_test124"},
            format="json",
        )
        self.assertEqual(200, response.status_code)
        self.assertTrue("email" in json_loads(response.content))


class RegisterTest(APITestCase):
    url = reverse("users:register")

    data = {
        "first_name": "name",
        "last_name": "last name",
        "email": "email@email.com",
        "password": "super_secret_password",
        "password2": "super_secret_password",
        "gender": "M",
        "phone": "273129083",
    }

    def test_register_wrong_password(self):
        false_data = {
            "first_name": "name",
            "last_name": "last name",
            "email": "email@email.com",
            "password": "super_secret_password",
            "password2": "super_secret_password124315",
            "gender": "M",
            "phone": "273129083",
        }
        response = self.client.post(self.url, false_data, format="json")
        self.assertEqual(400, response.status_code)

    def test_register_success(self):
        response = self.client.post(self.url, self.data, format="json")
        self.assertEqual(200, response.status_code)

    def test_unique_email_validator(self):
        response_1 = self.client.post(self.url, self.data, format="json")
        self.assertEqual(200, response_1.status_code)

        data_1 = {
            "first_name": "name1",
            "last_name": "last name2",
            "email": "email@email.com",
            "password": "super_secret_password",
            "password2": "super_secret_password",
            "gender": "M",
            "phone": "273129083",
        }

        response_2 = self.client.post(self.url, data_1, format="json")
        self.assertEqual(400, response_2.status_code)


class UpdateUserTest(APITestCase):
    url = reverse("users:update")
    user = None
    data = {
        "first_name": "name",
        "last_name": "last name",
        "gender": "M",
        "phone": "273129083",
    }

    def setUp(self):
        self.user = User.objects.create_user(
            email="email@email.com", password="password123456789", is_active=True
        )

    def test_update_user_fail(self):
        data = {
            "first_name": "Filip",
            "last_name": "Ivanusec",
            "gender": "M",
            "phone": "273129083",
        }

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(401, response.status_code)

    def test_user_update_pass(self):
        login = self.client.post(
            reverse("users:login"),
            {"email": self.user.email, "password": "password123456789"},
            format="json",
        )
        self.assertEqual(200, login.status_code)
        data = {
            "first_name": "Filip",
            "last_name": "Ivanusec",
            "email": "email@email.com",
            "gender": "M",
            "phone": "273129083",
        }

        response = self.client.post(self.url, data, format="json")
        self.assertEqual(200, response.status_code)


class ForgotPasswordTest(APITestCase):
    url = reverse("users:forgot-password")
    user = None

    def setUp(self) -> None:
        self.user = User.objects.create_user(
            email="email@email.com", password="password123456789", is_active=True
        )

    def test_send_email_token_fail(self):
        response = self.client.post(
            self.url, {"email": "notemail@email.com"}, format="json"
        )
        self.assertEqual(400, response.status_code)

    def test_send_email_token_pass(self):
        response = self.client.post(self.url, {"email": self.user.email}, format="json")
        self.assertEqual(200, response.status_code)


class ConfirmAccountTest(APITestCase):

    user = None

    def setUp(self):
        self.user = User.objects.create_user(
            email="email@email.com", password="password22"
        )

    def test_confirm_account_no_token(self):
        response = self.client.post(
            "v1/users/confirm-account/",
            {},
            format="json",
        )
        self.assertEqual(404, response.status_code)

    def test_confirm_account_fake_token(self):
        response = self.client.post(
            reverse("users:confirm-account", args=["876td87avsd"]),
            {},
            format="json",
        )
        self.assertEqual(403, response.status_code)

    def test_confirm_account_token(self):
        token_handler = TokenHandler()
        test_token = token_handler.create_token(
            testing=True, instance=settings.CONFIRM_ACCOUNT_PREFIX, user_id=self.user.id
        )
        response = self.client.post(
            reverse("users:confirm-account", args=[test_token]), {}, format="json"
        )
        self.assertEqual(200, response.status_code)


class ChangePassword(APITestCase):

    user = None

    data_1 = {
        "first_name": "name1",
        "last_name": "last name2",
        "email": "email@email.com",
        "password": "super_secret_password",
        "password2": "super_secret_password",
        "gender": "M",
        "phone": "273129083",
    }

    def setUp(self):
        self.user = User.objects.create_user(
            email=self.data_1.get("email"),
            password=self.data_1.get("password"),
            is_active=True,
        )

    def test_change_password_no_token(self):
        response = self.client.post(
            "v1/users/change-password/",
            {"password": "aljkhda", "password2": "kaujshdka"},
            format="json",
        )
        self.assertEqual(404, response.status_code)

    def test_change_password_diff_pass(self):
        token_handler = TokenHandler()
        test_token = token_handler.create_token(
            testing=True, instance=settings.FORGOT_PASSWORD_PREFIX, user_id=self.user.id
        )
        response = self.client.post(
            reverse("users:change-password", args=[test_token]),
            {"password": "aujshda", "password2": "sjkdhbankjd"},
            format="json",
        )
        self.assertEqual(400, response.status_code)

    def test_change_password_pass(self):
        token_handler = TokenHandler()
        test_token = token_handler.create_token(
            testing=True, instance=settings.FORGOT_PASSWORD_PREFIX, user_id=self.user.id
        )
        response = self.client.post(
            reverse("users:change-password", args=[test_token]),
            {"password": "password123456789", "password2": "password123456789"},
            format="json",
        )
        self.assertEqual(200, response.status_code)


class TestResponseHandler(TestCase):
    def test_success_message(self):
        response = CreateMessage.get().create_success_response(
            "This is success test message", status=200
        )

        self.assertDictEqual({"success": "This is success test message"}, response.data)
        self.assertTrue(type(response.data) is dict)

    def test_error_message(self):
        response = CreateMessage.get().create_success_response(
            "This is error test message", status=400
        )

        self.assertDictEqual({"success": "This is error test message"}, response.data)
        self.assertTrue(type(response.data) is dict)

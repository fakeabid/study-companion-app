"""
Authentication Tests — written before implementation (TDD).

Tests cover:
  - User registration
  - User login
  - Token refresh
  - Protected route access control
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from apps.users.models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REGISTER_URL = reverse("users:register")
LOGIN_URL = reverse("users:login")
REFRESH_URL = reverse("users:token_refresh")

VALID_REGISTRATION_PAYLOAD = {
    "email": "alice@example.com",
    "password": "SecurePass123!",
    "first_name": "Alice",
    "last_name": "Smith",
}


def register_user(client, payload=None):
    """Helper: register a user and return the response."""
    payload = payload or VALID_REGISTRATION_PAYLOAD
    return client.post(REGISTER_URL, payload, format="json")


def login_user(client, email=None, password=None):
    """Helper: log in and return the response."""
    return client.post(
        LOGIN_URL,
        {
            "email": email or VALID_REGISTRATION_PAYLOAD["email"],
            "password": password or VALID_REGISTRATION_PAYLOAD["password"],
        },
        format="json",
    )


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------


class RegistrationTests(APITestCase):

    def test_successful_registration_returns_201(self):
        """A valid payload creates a user and returns HTTP 201."""
        response = register_user(self.client)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_successful_registration_returns_expected_fields(self):
        """Response body must contain id, email, first_name, last_name, date_joined."""
        response = register_user(self.client)
        data = response.data
        self.assertIn("id", data)
        self.assertIn("email", data)
        self.assertIn("first_name", data)
        self.assertIn("last_name", data)
        self.assertIn("date_joined", data)

    def test_password_is_not_returned_in_response(self):
        """Passwords must never be exposed in API responses."""
        response = register_user(self.client)
        self.assertNotIn("password", response.data)

    def test_duplicate_email_returns_400(self):
        """Registering with an already-used email must fail with HTTP 400."""
        register_user(self.client)
        response = register_user(self.client)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_email_returns_400(self):
        payload = {**VALID_REGISTRATION_PAYLOAD}
        del payload["email"]
        response = register_user(self.client, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_missing_password_returns_400(self):
        payload = {**VALID_REGISTRATION_PAYLOAD}
        del payload["password"]
        response = register_user(self.client, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_invalid_email_format_returns_400(self):
        payload = {**VALID_REGISTRATION_PAYLOAD, "email": "not-an-email"}
        response = register_user(self.client, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_user_is_persisted_in_database(self):
        register_user(self.client)
        self.assertTrue(User.objects.filter(email=VALID_REGISTRATION_PAYLOAD["email"]).exists())

    def test_password_is_hashed_in_database(self):
        """Raw password must not be stored in the database."""
        register_user(self.client)
        user = User.objects.get(email=VALID_REGISTRATION_PAYLOAD["email"])
        self.assertNotEqual(user.password, VALID_REGISTRATION_PAYLOAD["password"])
        self.assertTrue(user.check_password(VALID_REGISTRATION_PAYLOAD["password"]))


# ---------------------------------------------------------------------------
# Login Tests
# ---------------------------------------------------------------------------


class LoginTests(APITestCase):

    def setUp(self):
        register_user(self.client)

    def test_successful_login_returns_200(self):
        response = login_user(self.client)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_successful_login_returns_access_and_refresh_tokens(self):
        response = login_user(self.client)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_tokens_are_non_empty_strings(self):
        response = login_user(self.client)
        self.assertIsInstance(response.data["access"], str)
        self.assertIsInstance(response.data["refresh"], str)
        self.assertTrue(len(response.data["access"]) > 0)
        self.assertTrue(len(response.data["refresh"]) > 0)

    def test_wrong_password_returns_401(self):
        response = login_user(self.client, password="WrongPassword!")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_nonexistent_email_returns_401(self):
        response = login_user(self.client, email="ghost@example.com")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_email_returns_400(self):
        response = self.client.post(
            LOGIN_URL, {"password": "SecurePass123!"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_password_returns_400(self):
        response = self.client.post(
            LOGIN_URL, {"email": "alice@example.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_error_message_does_not_reveal_whether_email_exists(self):
        """
        The error message for wrong password and non-existent email
        should be identical to prevent user enumeration.
        """
        wrong_pass = login_user(self.client, password="BadPassword!")
        no_user = login_user(self.client, email="ghost@example.com")
        # Both must be 401 and carry the same message
        self.assertEqual(wrong_pass.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(no_user.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(str(wrong_pass.data.get("detail")), str(no_user.data.get("detail")))


# ---------------------------------------------------------------------------
# Token Refresh Tests
# ---------------------------------------------------------------------------


class TokenRefreshTests(APITestCase):

    def setUp(self):
        register_user(self.client)
        login_response = login_user(self.client)
        self.refresh_token = login_response.data["refresh"]

    def test_valid_refresh_token_returns_new_access_token(self):
        response = self.client.post(
            REFRESH_URL, {"refresh": self.refresh_token}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_refresh_token_returns_401(self):
        response = self.client.post(
            REFRESH_URL, {"refresh": "this.is.invalid"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_missing_refresh_token_returns_400(self):
        response = self.client.post(REFRESH_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Protected Route Tests
# ---------------------------------------------------------------------------


class ProtectedRouteTests(APITestCase):
    """
    These tests use the /api/auth/me/ endpoint (a simple profile view)
    as a stand-in for any protected resource.
    """

    ME_URL = "/api/auth/me/"

    def setUp(self):
        register_user(self.client)
        login_response = login_user(self.client)
        self.access_token = login_response.data["access"]

    def test_authenticated_request_succeeds(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.get(self.ME_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_token_returns_401(self):
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.here")
        response = self.client.get(self.ME_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
"""
Workspace CRUD Tests — written before implementation (TDD).

Tests cover:
  - Authentication guard on all endpoints
  - List workspaces
  - Create workspace
  - Rename workspace (PATCH)
  - Delete workspace
  - Cross-user isolation
"""

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import User
from workspaces.models import Workspace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

LIST_CREATE_URL = reverse("workspaces:list_create")


def detail_url(workspace_id):
    return reverse("workspaces:detail", args=[workspace_id])


def create_user(email="alice@example.com", password="SecurePass123!"):
    return User.objects.create_user(email=email, password=password)


def auth_client(client, user):
    """Authenticate the test client as the given user via JWT."""
    response = client.post(
        reverse("users:login"),
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )
    token = response.data["access"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def create_workspace(client, name="Machine Learning"):
    return client.post(LIST_CREATE_URL, {"name": name}, format="json")


# ---------------------------------------------------------------------------
# Authentication Guard Tests
# ---------------------------------------------------------------------------


class WorkspaceAuthGuardTests(APITestCase):
    """All workspace endpoints must reject unauthenticated requests."""

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)
        ws = create_workspace(self.client)
        self.workspace_id = ws.data["id"]
        self.client.credentials()  # Clear credentials for guard tests

    def test_list_requires_authentication(self):
        response = self.client.get(LIST_CREATE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_requires_authentication(self):
        response = self.client.post(LIST_CREATE_URL, {"name": "Test"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_requires_authentication(self):
        response = self.client.patch(
            detail_url(self.workspace_id), {"name": "New"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_requires_authentication(self):
        response = self.client.delete(detail_url(self.workspace_id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# List Tests
# ---------------------------------------------------------------------------


class WorkspaceListTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)

    def test_empty_list_returns_200(self):
        response = self.client.get(LIST_CREATE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_returns_own_workspaces(self):
        create_workspace(self.client, "Machine Learning")
        create_workspace(self.client, "Database Systems")
        response = self.client.get(LIST_CREATE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_does_not_return_other_users_workspaces(self):
        # Another user creates a workspace
        other_user = create_user(email="bob@example.com")
        Workspace.objects.create(user=other_user, name="Bob's Workspace")

        response = self.client.get(LIST_CREATE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_response_contains_expected_fields(self):
        create_workspace(self.client, "German Language")
        response = self.client.get(LIST_CREATE_URL)
        workspace = response.data[0]
        self.assertIn("id", workspace)
        self.assertIn("name", workspace)
        self.assertIn("created_at", workspace)
        self.assertIn("updated_at", workspace)
        # user field must not leak — the owner is implied by authentication
        self.assertNotIn("user", workspace)


# ---------------------------------------------------------------------------
# Create Tests
# ---------------------------------------------------------------------------


class WorkspaceCreateTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)

    def test_valid_create_returns_201(self):
        response = create_workspace(self.client, "Machine Learning")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_response_contains_expected_fields(self):
        response = create_workspace(self.client, "Machine Learning")
        self.assertIn("id", response.data)
        self.assertIn("name", response.data)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_workspace_is_persisted_in_database(self):
        create_workspace(self.client, "Machine Learning")
        self.assertTrue(Workspace.objects.filter(name="Machine Learning").exists())

    def test_workspace_is_associated_with_authenticated_user(self):
        create_workspace(self.client, "Machine Learning")
        workspace = Workspace.objects.get(name="Machine Learning")
        self.assertEqual(workspace.user, self.user)

    def test_missing_name_returns_400(self):
        response = self.client.post(LIST_CREATE_URL, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_blank_name_returns_400(self):
        response = self.client.post(LIST_CREATE_URL, {"name": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_whitespace_only_name_returns_400(self):
        response = self.client.post(LIST_CREATE_URL, {"name": "   "}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_name_exceeding_255_chars_returns_400(self):
        response = self.client.post(
            LIST_CREATE_URL, {"name": "x" * 256}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    def test_name_at_255_chars_is_accepted(self):
        response = self.client.post(
            LIST_CREATE_URL, {"name": "x" * 255}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Update (PATCH) Tests
# ---------------------------------------------------------------------------


class WorkspaceUpdateTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)
        response = create_workspace(self.client, "Original Name")
        self.workspace_id = response.data["id"]

    def test_valid_rename_returns_200(self):
        response = self.client.patch(
            detail_url(self.workspace_id), {"name": "Renamed"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_rename_updates_name_in_response(self):
        response = self.client.patch(
            detail_url(self.workspace_id), {"name": "Renamed"}, format="json"
        )
        self.assertEqual(response.data["name"], "Renamed")

    def test_rename_persists_in_database(self):
        self.client.patch(
            detail_url(self.workspace_id), {"name": "Renamed"}, format="json"
        )
        workspace = Workspace.objects.get(id=self.workspace_id)
        self.assertEqual(workspace.name, "Renamed")

    def test_blank_name_returns_400(self):
        response = self.client.patch(
            detail_url(self.workspace_id), {"name": ""}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_whitespace_only_name_returns_400(self):
        response = self.client.patch(
            detail_url(self.workspace_id), {"name": "   "}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_name_exceeding_255_chars_returns_400(self):
        response = self.client.patch(
            detail_url(self.workspace_id), {"name": "x" * 256}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_another_users_workspace_returns_404(self):
        other_user = create_user(email="bob@example.com")
        other_ws = Workspace.objects.create(user=other_user, name="Bob's Workspace")
        response = self.client.patch(
            detail_url(other_ws.id), {"name": "Hijacked"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_nonexistent_workspace_returns_404(self):
        import uuid
        response = self.client.patch(
            detail_url(uuid.uuid4()), {"name": "Ghost"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Delete Tests
# ---------------------------------------------------------------------------


class WorkspaceDeleteTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)
        response = create_workspace(self.client, "To Be Deleted")
        self.workspace_id = response.data["id"]

    def test_delete_own_workspace_returns_204(self):
        response = self.client.delete(detail_url(self.workspace_id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_removes_workspace_from_database(self):
        self.client.delete(detail_url(self.workspace_id))
        self.assertFalse(Workspace.objects.filter(id=self.workspace_id).exists())

    def test_delete_another_users_workspace_returns_404(self):
        other_user = create_user(email="bob@example.com")
        other_ws = Workspace.objects.create(user=other_user, name="Bob's Workspace")
        response = self.client.delete(detail_url(other_ws.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_another_users_workspace_does_not_delete_it(self):
        other_user = create_user(email="bob@example.com")
        other_ws = Workspace.objects.create(user=other_user, name="Bob's Workspace")
        self.client.delete(detail_url(other_ws.id))
        self.assertTrue(Workspace.objects.filter(id=other_ws.id).exists())

    def test_delete_nonexistent_workspace_returns_404(self):
        import uuid
        response = self.client.delete(detail_url(uuid.uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Cross-User Isolation Test
# ---------------------------------------------------------------------------


class CrossUserIsolationTests(APITestCase):
    """
    Full integration test: two users, each with their own workspaces.
    Confirms complete data isolation at every operation.
    """

    def setUp(self):
        self.alice = create_user(email="alice@example.com")
        self.bob = create_user(email="bob@example.com")

    def _alice_client(self):
        from rest_framework.test import APIClient
        client = APIClient()
        auth_client(client, self.alice)
        return client

    def _bob_client(self):
        from rest_framework.test import APIClient
        client = APIClient()
        auth_client(client, self.bob)
        return client

    def test_each_user_only_sees_their_own_workspaces(self):
        alice = self._alice_client()
        bob = self._bob_client()

        alice.post(LIST_CREATE_URL, {"name": "Alice WS 1"}, format="json")
        alice.post(LIST_CREATE_URL, {"name": "Alice WS 2"}, format="json")
        bob.post(LIST_CREATE_URL, {"name": "Bob WS 1"}, format="json")

        alice_list = alice.get(LIST_CREATE_URL)
        bob_list = bob.get(LIST_CREATE_URL)

        self.assertEqual(len(alice_list.data), 2)
        self.assertEqual(len(bob_list.data), 1)

        alice_names = {ws["name"] for ws in alice_list.data}
        bob_names = {ws["name"] for ws in bob_list.data}

        self.assertEqual(alice_names, {"Alice WS 1", "Alice WS 2"})
        self.assertEqual(bob_names, {"Bob WS 1"})
        # Confirm no leakage either way
        self.assertTrue(alice_names.isdisjoint(bob_names))
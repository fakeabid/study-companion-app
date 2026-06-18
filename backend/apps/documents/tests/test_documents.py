"""
Document Management Tests — Phase 2.

Covers:
  - File upload (valid, invalid type, quota exceeded, wrong workspace)
  - Document listing with sorting
  - Document detail
  - Document deletion (file removed from disk, storage updates)
  - Storage usage endpoint
  - Cross-user access prevention
"""

import io
import os
import uuid
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.users.models import User
from apps.workspaces.models import Workspace
from apps.documents.models import Document
from apps.documents.validators import QUOTA_BYTES

import tempfile

# Use a temp directory for media files during tests so we don't
# pollute the real MEDIA_ROOT and always start clean.
TEMP_MEDIA = tempfile.mkdtemp()


def make_file(name="notes.pdf", size=1024, content=b"x"):
    """Create an in-memory uploaded file for testing."""
    return SimpleUploadedFile(name, content * size, content_type="application/pdf")


def create_user(email="alice@example.com", password="SecurePass123!"):
    return User.objects.create_user(email=email, password=password)


def auth_client(client, user):
    response = client.post(
        reverse("users:login"),
        {"email": user.email, "password": "SecurePass123!"},
        format="json",
    )
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


def create_workspace(user, name="ML"):
    return Workspace.objects.create(user=user, name=name)


UPLOAD_URL = reverse("documents:upload")
STORAGE_URL = reverse("documents:storage")


def list_url(workspace_id):
    return reverse("documents:workspace_documents", args=[workspace_id])


def detail_url(doc_id):
    return reverse("documents:detail", args=[doc_id])


def delete_url(doc_id):
    return reverse("documents:delete", args=[doc_id])


# ---------------------------------------------------------------------------
# Upload Tests
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DocumentUploadTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)
        self.workspace = create_workspace(self.user)

    def _upload(self, filename="notes.pdf", workspace_id=None, size=1024):
        workspace_id = workspace_id or self.workspace.id
        f = make_file(name=filename, size=size)
        return self.client.post(
            UPLOAD_URL,
            {"file": f, "workspace_id": str(workspace_id)},
            format="multipart",
        )

    def test_valid_pdf_upload_returns_201(self):
        response = self._upload("lecture.pdf")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_valid_pptx_upload_accepted(self):
        response = self._upload("slides.pptx")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_valid_docx_upload_accepted(self):
        response = self._upload("essay.docx")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_valid_txt_upload_accepted(self):
        response = self._upload("notes.txt")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_valid_md_upload_accepted(self):
        response = self._upload("readme.md")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_response_contains_expected_fields(self):
        response = self._upload("lecture.pdf")
        data = response.data
        self.assertIn("id", data)
        self.assertIn("original_filename", data)
        self.assertIn("file_type", data)
        self.assertIn("file_size", data)
        self.assertIn("uploaded_at", data)
        self.assertIn("workspace_id", data)

    def test_original_filename_preserved(self):
        response = self._upload("my_lecture_notes.pdf")
        self.assertEqual(response.data["original_filename"], "my_lecture_notes.pdf")

    def test_file_type_stored_as_extension(self):
        response = self._upload("notes.pdf")
        self.assertEqual(response.data["file_type"], "pdf")

    def test_file_size_stored_correctly(self):
        response = self._upload("notes.pdf", size=2048)
        # size param * len(b"x") = 2048 bytes
        self.assertEqual(response.data["file_size"], 2048)

    def test_unsupported_file_type_returns_400(self):
        response = self._upload("video.mp4")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_file_type_error_mentions_allowed_types(self):
        response = self._upload("image.png")
        error = str(response.data)
        self.assertIn("PDF", error)

    def test_missing_file_returns_400(self):
        response = self.client.post(
            UPLOAD_URL,
            {"workspace_id": str(self.workspace.id)},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_workspace_id_returns_400(self):
        f = make_file()
        response = self.client.post(UPLOAD_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_to_another_users_workspace_returns_403(self):
        other = create_user("bob@example.com")
        other_ws = create_workspace(other, "Bob WS")
        response = self._upload(workspace_id=other_ws.id)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_to_nonexistent_workspace_returns_404(self):
        response = self._upload(workspace_id=uuid.uuid4())
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_document_record_created_in_database(self):
        self._upload("lecture.pdf")
        self.assertTrue(
            Document.objects.filter(
                workspace=self.workspace, uploaded_by=self.user
            ).exists()
        )

    def test_file_stored_on_disk(self):
        self._upload("lecture.pdf")
        doc = Document.objects.get(workspace=self.workspace)
        self.assertTrue(doc.file.storage.exists(doc.file.name))

    def test_storage_increases_after_upload(self):
        from documents.validators import get_storage_info
        before = get_storage_info(self.user)["used_bytes"]
        self._upload("notes.pdf", size=2048)
        after = get_storage_info(self.user)["used_bytes"]
        self.assertGreater(after, before)

    def test_unauthenticated_upload_returns_401(self):
        self.client.credentials()
        response = self._upload()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_quota_exceeded_returns_400(self):
        # Create a document that fills the quota, then try to upload more
        Document.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            file="fake/path.pdf",
            original_filename="big.pdf",
            file_type="pdf",
            file_size=QUOTA_BYTES,  # Exactly at quota
        )
        response = self._upload("one_more.pdf")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quota", str(response.data).lower())


# ---------------------------------------------------------------------------
# List Tests
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DocumentListTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)
        self.workspace = create_workspace(self.user)

    def _make_doc(self, name="notes.pdf", size=1024, file_type="pdf"):
        return Document.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            file="fake/path.pdf",
            original_filename=name,
            file_type=file_type,
            file_size=size,
        )

    def test_empty_workspace_returns_200_with_empty_list(self):
        response = self.client.get(list_url(self.workspace.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_returns_documents_in_workspace(self):
        self._make_doc("a.pdf")
        self._make_doc("b.pdf")
        response = self.client.get(list_url(self.workspace.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_does_not_return_documents_from_other_workspaces(self):
        other_ws = create_workspace(self.user, "Other WS")
        self._make_doc("in_target.pdf")
        Document.objects.create(
            workspace=other_ws,
            uploaded_by=self.user,
            file="fake/other.pdf",
            original_filename="in_other.pdf",
            file_type="pdf",
            file_size=512,
        )
        response = self.client.get(list_url(self.workspace.id))
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["original_filename"], "in_target.pdf")

    def test_listing_another_users_workspace_returns_404(self):
        other = create_user("bob@example.com")
        other_ws = create_workspace(other, "Bob WS")
        response = self.client.get(list_url(other_ws.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_contains_expected_fields(self):
        self._make_doc("notes.pdf")
        response = self.client.get(list_url(self.workspace.id))
        doc = response.data[0]
        self.assertIn("id", doc)
        self.assertIn("original_filename", doc)
        self.assertIn("file_type", doc)
        self.assertIn("file_size", doc)
        self.assertIn("uploaded_at", doc)

    def test_sort_by_name(self):
        self._make_doc("zebra.pdf")
        self._make_doc("alpha.pdf")
        response = self.client.get(list_url(self.workspace.id) + "?sort=name")
        names = [d["original_filename"] for d in response.data]
        self.assertEqual(names, sorted(names))

    def test_sort_by_size(self):
        self._make_doc("small.pdf", size=100)
        self._make_doc("large.pdf", size=9000)
        response = self.client.get(list_url(self.workspace.id) + "?sort=size")
        sizes = [d["file_size"] for d in response.data]
        self.assertEqual(sizes, sorted(sizes))

    def test_sort_by_date_default(self):
        self._make_doc("first.pdf")
        self._make_doc("second.pdf")
        response = self.client.get(list_url(self.workspace.id))
        # Default ordering is newest first
        dates = [d["uploaded_at"] for d in response.data]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_invalid_sort_param_falls_back_to_default(self):
        self._make_doc("notes.pdf")
        response = self.client.get(list_url(self.workspace.id) + "?sort=invalid")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Detail Tests
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DocumentDetailTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)
        self.workspace = create_workspace(self.user)
        self.doc = Document.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            file="fake/path.pdf",
            original_filename="lecture.pdf",
            file_type="pdf",
            file_size=2048,
        )

    def test_returns_200_with_full_metadata(self):
        response = self.client.get(detail_url(self.doc.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_response_contains_workspace_info(self):
        response = self.client.get(detail_url(self.doc.id))
        self.assertIn("workspace_id", response.data)
        self.assertIn("workspace_name", response.data)
        self.assertEqual(response.data["workspace_name"], self.workspace.name)

    def test_response_contains_uploader_email(self):
        response = self.client.get(detail_url(self.doc.id))
        self.assertIn("uploaded_by_email", response.data)
        self.assertEqual(response.data["uploaded_by_email"], self.user.email)

    def test_another_users_document_returns_404(self):
        other = create_user("bob@example.com")
        other_ws = create_workspace(other)
        other_doc = Document.objects.create(
            workspace=other_ws,
            uploaded_by=other,
            file="fake/other.pdf",
            original_filename="other.pdf",
            file_type="pdf",
            file_size=512,
        )
        response = self.client.get(detail_url(other_doc.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_document_returns_404(self):
        response = self.client.get(detail_url(uuid.uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Delete Tests
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DocumentDeleteTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)
        self.workspace = create_workspace(self.user)

    def _upload_real_file(self, filename="notes.pdf"):
        """Upload via API so a real file exists on disk."""
        f = make_file(name=filename, size=1024)
        response = self.client.post(
            UPLOAD_URL,
            {"file": f, "workspace_id": str(self.workspace.id)},
            format="multipart",
        )
        return Document.objects.get(id=response.data["id"])

    def test_delete_own_document_returns_204(self):
        doc = self._upload_real_file()
        response = self.client.delete(delete_url(doc.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_removes_database_record(self):
        doc = self._upload_real_file()
        self.client.delete(delete_url(doc.id))
        self.assertFalse(Document.objects.filter(id=doc.id).exists())

    def test_delete_removes_file_from_disk(self):
        doc = self._upload_real_file()
        file_name = doc.file.name
        storage = doc.file.storage
        self.assertTrue(storage.exists(file_name))
        self.client.delete(delete_url(doc.id))
        self.assertFalse(storage.exists(file_name))

    def test_storage_decreases_after_delete(self):
        from documents.validators import get_storage_info
        doc = self._upload_real_file()
        before = get_storage_info(self.user)["used_bytes"]
        self.client.delete(delete_url(doc.id))
        after = get_storage_info(self.user)["used_bytes"]
        self.assertLess(after, before)

    def test_delete_another_users_document_returns_404(self):
        other = create_user("bob@example.com")
        other_ws = create_workspace(other)
        other_doc = Document.objects.create(
            workspace=other_ws,
            uploaded_by=other,
            file="fake/other.pdf",
            original_filename="other.pdf",
            file_type="pdf",
            file_size=512,
        )
        response = self.client.delete(delete_url(other_doc.id))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_another_users_document_does_not_remove_it(self):
        other = create_user("bob@example.com")
        other_ws = create_workspace(other)
        other_doc = Document.objects.create(
            workspace=other_ws,
            uploaded_by=other,
            file="fake/other.pdf",
            original_filename="other.pdf",
            file_type="pdf",
            file_size=512,
        )
        self.client.delete(delete_url(other_doc.id))
        self.assertTrue(Document.objects.filter(id=other_doc.id).exists())

    def test_delete_nonexistent_document_returns_404(self):
        response = self.client.delete(delete_url(uuid.uuid4()))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Storage Usage Tests
# ---------------------------------------------------------------------------

@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class StorageUsageTests(APITestCase):

    def setUp(self):
        self.user = create_user()
        auth_client(self.client, self.user)
        self.workspace = create_workspace(self.user)

    def test_returns_200(self):
        response = self.client.get(STORAGE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_zero_used_when_no_documents(self):
        response = self.client.get(STORAGE_URL)
        self.assertEqual(response.data["used_bytes"], 0)

    def test_returns_expected_fields(self):
        response = self.client.get(STORAGE_URL)
        for field in [
            "used_bytes", "used_display",
            "remaining_bytes", "remaining_display",
            "quota_bytes", "quota_display",
            "percent_used",
        ]:
            self.assertIn(field, response.data)

    def test_quota_is_1gb(self):
        response = self.client.get(STORAGE_URL)
        self.assertEqual(response.data["quota_bytes"], 1 * 1024 * 1024 * 1024)

    def test_used_bytes_correct_after_upload(self):
        Document.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            file="fake/a.pdf",
            original_filename="a.pdf",
            file_type="pdf",
            file_size=500_000,
        )
        response = self.client.get(STORAGE_URL)
        self.assertEqual(response.data["used_bytes"], 500_000)

    def test_remaining_is_quota_minus_used(self):
        Document.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            file="fake/a.pdf",
            original_filename="a.pdf",
            file_type="pdf",
            file_size=200_000,
        )
        response = self.client.get(STORAGE_URL)
        expected_remaining = QUOTA_BYTES - 200_000
        self.assertEqual(response.data["remaining_bytes"], expected_remaining)

    def test_used_decreases_after_delete(self):
        doc = Document.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            file="fake/a.pdf",
            original_filename="a.pdf",
            file_type="pdf",
            file_size=300_000,
        )
        before = self.client.get(STORAGE_URL).data["used_bytes"]
        doc.delete()
        after = self.client.get(STORAGE_URL).data["used_bytes"]
        self.assertLess(after, before)

    def test_percent_used_is_accurate(self):
        Document.objects.create(
            workspace=self.workspace,
            uploaded_by=self.user,
            file="fake/a.pdf",
            original_filename="a.pdf",
            file_type="pdf",
            file_size=QUOTA_BYTES // 2,  # Exactly 50%
        )
        response = self.client.get(STORAGE_URL)
        self.assertEqual(response.data["percent_used"], 50.0)

    def test_unauthenticated_request_returns_401(self):
        self.client.credentials()
        response = self.client.get(STORAGE_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_does_not_count_other_users_storage(self):
        other = create_user("bob@example.com")
        other_ws = create_workspace(other)
        Document.objects.create(
            workspace=other_ws,
            uploaded_by=other,
            file="fake/other.pdf",
            original_filename="other.pdf",
            file_type="pdf",
            file_size=999_999,
        )
        response = self.client.get(STORAGE_URL)
        self.assertEqual(response.data["used_bytes"], 0)
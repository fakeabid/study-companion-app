"""
Document model.

Designed with Phase 3 in mind:
- The commented-out fields show exactly what Phase 3 will add.
  Adding them is an ALTER TABLE ADD COLUMN — no structural change.
- `processing_status` uses a choices field so the API can filter by status.
- `uploaded_by` is indexed for the storage aggregation query.
- `workspace` is indexed for the document listing query.
"""

import uuid
from django.conf import settings
from django.db import models
from .storage import document_upload_path


class Document(models.Model):

    # ── Phase 3: processing status choices (defined now, used later) ─────
    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETE = "complete", "Complete"
        FAILED = "failed", "Failed"

    # ── Core fields ──────────────────────────────────────────────────────

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    workspace = models.ForeignKey(
        "workspaces.Workspace",
        on_delete=models.CASCADE,
        related_name="documents",
        db_index=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="documents",
        db_index=True,
    )

    # The file on disk — UUID-named via document_upload_path
    file = models.FileField(upload_to=document_upload_path)

    # What the user sees
    original_filename = models.CharField(max_length=255)

    # e.g. "pdf", "docx" — stored lowercase without the dot
    file_type = models.CharField(max_length=10)

    # Bytes — BIGINT in Postgres
    file_size = models.BigIntegerField()

    uploaded_at = models.DateTimeField(auto_now_add=True)

    # ── Phase 3 fields (commented out — add via migration when needed) ───
    #
    # processing_status = models.CharField(
    #     max_length=20,
    #     choices=ProcessingStatus.choices,
    #     default=ProcessingStatus.PENDING,
    #     db_index=True,
    # )
    # extracted_text = models.TextField(blank=True, null=True)
    # chunk_count = models.IntegerField(null=True, blank=True)
    # embedded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "documents"
        ordering = ["-uploaded_at"]
        indexes = [
            # Composite index: ownership checks (workspace + user together)
            models.Index(
                fields=["workspace", "uploaded_by"],
                name="doc_workspace_user_idx",
            ),
        ]
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"{self.original_filename} ({self.uploaded_by.email})"

    def delete(self, *args, **kwargs):
        """
        Override delete to remove the file from storage when the
        database record is deleted.

        This ensures storage is always reclaimed — even if delete()
        is called directly on a queryset member rather than via the API.

        Note: bulk QuerySet.delete() does NOT call this method. The
        view uses instance.delete() explicitly to guarantee this runs.
        """
        storage = self.file.storage
        path = self.file.name
        super().delete(*args, **kwargs)
        # Delete file after DB record is removed so we don't orphan
        # a deleted record with a dangling file reference
        if path and storage.exists(path):
            storage.delete(path)
"""
Storage path and filename logic for uploaded documents.

Design decisions:
- Files are stored under MEDIA_ROOT/documents/<user_id>/<uuid>.<ext>
- The user_id subdirectory makes it trivial to find and delete all files
  for a given user (GDPR right-to-erasure, account deletion).
- The filename on disk is a UUID — never the original filename. This
  prevents path traversal attacks, filename collisions, and leaks of
  internal naming conventions.
- The original filename is preserved in the database only, and returned
  to the user via the API.

When we switch to Cloudflare R2, this function becomes the S3 key
generator — the rest of the codebase is unchanged.
"""

import uuid
import os


def document_upload_path(instance, filename):
    """
    Generate a safe storage path for an uploaded document.

    Called by Django's FileField `upload_to` parameter.

    Args:
        instance: The Document model instance (may not be saved yet).
        filename: The original filename from the upload.

    Returns:
        str: Path relative to MEDIA_ROOT, e.g.
             "documents/abc-123/f47ac10b-58cc.pdf"
    """
    ext = os.path.splitext(filename)[1].lower()  # e.g. ".pdf"
    safe_name = f"{uuid.uuid4()}{ext}"
    return os.path.join("documents", str(instance.uploaded_by_id), safe_name)
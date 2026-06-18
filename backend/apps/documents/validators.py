"""
Validators for document uploads.

Keeping validators here (not in the serializer body) means:
1. They can be unit tested in isolation.
2. They can be reused by management commands or future batch upload endpoints.
3. The serializer stays clean and readable.
"""

from django.core.exceptions import ValidationError
from django.db.models import Sum

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

QUOTA_BYTES = 1 * 1024 * 1024 * 1024  # 1 GB in bytes

ALLOWED_EXTENSIONS = {"pdf", "pptx", "docx", "txt", "md"}

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    # Some browsers send these variants
    "application/octet-stream",  # generic fallback — extension check is the authority
}

# Human-readable names for error messages
ALLOWED_EXTENSIONS_DISPLAY = ", ".join(sorted(ALLOWED_EXTENSIONS)).upper()


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------

def validate_file_type(file):
    """
    Validate that the uploaded file has an allowed extension.

    We validate by extension (not MIME type alone) because MIME types
    are client-supplied and trivially spoofed. Extension is still spoofable,
    but combined with server-side processing in Phase 3 (text extraction)
    we get real content validation for free.

    Raises:
        ValidationError: If the extension is not in ALLOWED_EXTENSIONS.
    """
    import os
    ext = os.path.splitext(file.name)[1].lstrip(".").lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '.{ext}'. "
            f"Allowed types: {ALLOWED_EXTENSIONS_DISPLAY}."
        )
    return ext  # Return the clean extension for storage in the DB


def validate_quota(user, incoming_file_size):
    """
    Check that uploading a file of incoming_file_size bytes would not
    exceed the user's 1 GB storage quota.

    We calculate dynamically (Option B) — see architecture notes.

    Args:
        user: The authenticated User instance.
        incoming_file_size: Size in bytes of the file being uploaded.

    Raises:
        ValidationError: If the upload would exceed the quota.
    """
    from apps.documents.models import Document

    result = Document.objects.filter(uploaded_by=user).aggregate(
        total=Sum("file_size")
    )
    used = result["total"] or 0
    remaining = QUOTA_BYTES - used

    if incoming_file_size > remaining:
        raise ValidationError(
            f"Storage quota exceeded. "
            f"File size: {_human_readable(incoming_file_size)}. "
            f"Remaining storage: {_human_readable(remaining)}."
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_storage_info(user):
    """
    Return a dict of storage usage stats for the given user.
    Used by the storage endpoint and by serializers.
    """
    from apps.documents.models import Document

    result = Document.objects.filter(uploaded_by=user).aggregate(
        total=Sum("file_size")
    )
    used = result["total"] or 0
    remaining = QUOTA_BYTES - used
    percent = round((used / QUOTA_BYTES) * 100, 1) if used > 0 else 0.0

    return {
        "used_bytes": used,
        "used_display": _human_readable(used),
        "remaining_bytes": remaining,
        "remaining_display": _human_readable(remaining),
        "quota_bytes": QUOTA_BYTES,
        "quota_display": _human_readable(QUOTA_BYTES),
        "percent_used": percent,
    }


def _human_readable(size_bytes):
    """Convert bytes to a human-readable string (KB, MB, GB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.1f} GB"
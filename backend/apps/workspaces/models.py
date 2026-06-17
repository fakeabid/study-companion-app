import uuid
from django.conf import settings
from django.db import models


class Workspace(models.Model):
    """
    A personal workspace belonging to a single user.

    Design decisions:
    - UUID PK: consistent with User model; safe to expose in URLs.
    - ForeignKey to settings.AUTH_USER_MODEL (not User directly): this is
      the Django-recommended pattern. It decouples the model from a hardcoded
      import path and works correctly regardless of how AUTH_USER_MODEL is set.
    - on_delete=CASCADE: deleting a user removes all their workspaces.
      This is the correct default for owned resources.
    - updated_at uses auto_now=True: always reflects the last save, no manual
      tracking needed.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="workspaces",
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "workspaces"
        verbose_name = "Workspace"
        verbose_name_plural = "Workspaces"
        ordering = ["-created_at"]  # Newest first — standard for dashboard lists

    def __str__(self):
        return f"{self.name} ({self.user.email})"
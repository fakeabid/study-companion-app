from rest_framework import serializers
from .models import Workspace


class WorkspaceSerializer(serializers.ModelSerializer):
    """
    Serializer for creating, reading, and updating Workspaces.

    Design decisions:
    - `user` is excluded from the output entirely. The owner is implied
      by the authenticated request — exposing it would be redundant and
      could leak user IDs unnecessarily.
    - `name` has an explicit validator that rejects whitespace-only strings.
      CharField's blank=False only catches empty strings at the DB level;
      a name of "   " would pass through without this validator.
    - `id`, `created_at`, `updated_at` are read-only: they are set by the
      system and must never be writable by the client.
    """

    name = serializers.CharField(max_length=255)

    class Meta:
        model = Workspace
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_name(self, value):
        """Reject names that are blank or contain only whitespace."""
        if not value.strip():
            raise serializers.ValidationError("Workspace name cannot be blank.")
        return value
"""
Document serializers.

Three serializers for three distinct concerns:
- DocumentUploadSerializer   → write path (multipart upload)
- DocumentListSerializer     → read path (list view, lightweight)
- DocumentDetailSerializer   → read path (detail view, full metadata)

Keeping upload separate from read serializers is important:
the upload serializer handles file validation and workspace ownership;
the read serializers are simple and never expose the raw file path.
"""

from rest_framework import serializers
from .models import Document
from .validators import validate_file_type, validate_quota


class DocumentUploadSerializer(serializers.Serializer):
    """
    Handles multipart document upload.

    Uses a plain Serializer (not ModelSerializer) because the creation
    logic is complex — we need to validate file type, check quota, and
    verify workspace ownership before saving. Keeping this in the
    serializer keeps the view thin.
    """

    file = serializers.FileField()
    workspace_id = serializers.UUIDField()

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user
        file = attrs["file"]
        workspace_id = attrs["workspace_id"]

        # ── 1. Validate file type ────────────────────────────────────
        try:
            file_ext = validate_file_type(file)
        except Exception as e:
            raise serializers.ValidationError({"file": str(e)})

        # ── 2. Validate workspace ownership ─────────────────────────
        from apps.workspaces.models import Workspace
        from rest_framework.exceptions import NotFound, PermissionDenied

        try:
            workspace = Workspace.objects.get(pk=workspace_id)
        except Workspace.DoesNotExist:
            raise NotFound("Workspace not found.")

        if workspace.user != user:
            raise PermissionDenied("You do not have access to this workspace.")

        # ── 3. Validate storage quota ────────────────────────────────
        try:
            validate_quota(user, file.size)
        except Exception as e:
            raise serializers.ValidationError({"file": str(e)})

        # Attach resolved objects for use in create()
        attrs["workspace"] = workspace
        attrs["file_ext"] = file_ext
        return attrs

    def create(self, validated_data):
        request = self.context["request"]
        file = validated_data["file"]

        return Document.objects.create(
            workspace=validated_data["workspace"],
            uploaded_by=request.user,
            file=file,
            original_filename=file.name,
            file_type=validated_data["file_ext"],
            file_size=file.size,
        )


class DocumentListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for document list views.
    Does not expose the raw file path.
    """

    class Meta:
        model = Document
        fields = [
            "id",
            "original_filename",
            "file_type",
            "file_size",
            "uploaded_at",
        ]
        read_only_fields = fields


class DocumentDetailSerializer(serializers.ModelSerializer):
    """
    Full metadata serializer for the detail endpoint.
    Adds workspace info and uploader email.
    """

    workspace_id = serializers.UUIDField(source="workspace.id", read_only=True)
    workspace_name = serializers.CharField(source="workspace.name", read_only=True)
    uploaded_by_email = serializers.EmailField(source="uploaded_by.email", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "original_filename",
            "file_type",
            "file_size",
            "uploaded_at",
            "workspace_id",
            "workspace_name",
            "uploaded_by_email",
        ]
        read_only_fields = fields
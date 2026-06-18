"""
Document views.

Five views, each with a single clear responsibility:

  DocumentUploadView       POST /api/documents/upload/
  WorkspaceDocumentListView GET /api/workspaces/<id>/documents/
  DocumentDetailView        GET /api/documents/<id>/
  DocumentDeleteView        DELETE /api/documents/<id>/
  StorageUsageView          GET /api/storage/
"""

from rest_framework import status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Document
from .serializers import (
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer,
)
from .validators import get_storage_info

# Valid sort fields mapped to ORM field names
SORT_FIELDS = {
    "name": "original_filename",
    "size": "file_size",
    "date": "-uploaded_at",  # Default: newest first
}


class DocumentUploadView(APIView):
    """
    POST /api/documents/upload/

    Accepts multipart/form-data with:
      - file: the document file
      - workspace_id: UUID of the target workspace

    Validates file type, workspace ownership, and storage quota
    before persisting the file and database record.
    """

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = DocumentUploadSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        document = serializer.save()

        return Response(
            DocumentDetailSerializer(document).data,
            status=status.HTTP_201_CREATED,
        )


class WorkspaceDocumentListView(APIView):
    """
    GET /api/workspaces/<workspace_id>/documents/

    Lists all documents in a workspace, scoped to the authenticated user.
    Returns 404 if the workspace doesn't exist or belongs to another user
    (same behaviour as workspace detail — don't confirm resource existence).

    Query params:
      ?sort=name|size|date   (default: date, descending)
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        # Validate workspace ownership first
        from apps.workspaces.models import Workspace
        try:
            workspace = Workspace.objects.get(pk=workspace_id, user=request.user)
        except Workspace.DoesNotExist:
            raise NotFound()

        sort_param = request.query_params.get("sort", "date")
        order_field = SORT_FIELDS.get(sort_param, "-uploaded_at")

        documents = Document.objects.filter(
            workspace=workspace,
            uploaded_by=request.user,
        ).order_by(order_field)

        serializer = DocumentListSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentDetailView(APIView):
    """
    GET /api/documents/<id>/

    Returns full metadata for a single document.
    Returns 404 if not found or owned by another user.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Document.objects.get(pk=pk, uploaded_by=user)
        except Document.DoesNotExist:
            raise NotFound()

    def get(self, request, pk):
        document = self.get_object(pk, request.user)
        serializer = DocumentDetailSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentDeleteView(APIView):
    """
    DELETE /api/documents/<id>/

    Deletes the document record and removes the file from storage.
    Storage usage updates automatically (calculated dynamically).

    Uses instance.delete() (not queryset.delete()) to ensure our
    overridden delete() method runs and the file is removed from disk.
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Document.objects.get(pk=pk, uploaded_by=user)
        except Document.DoesNotExist:
            raise NotFound()

    def delete(self, request, pk):
        document = self.get_object(pk, request.user)
        document.delete()  # Triggers file removal via overridden delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StorageUsageView(APIView):
    """
    GET /api/storage/

    Returns the authenticated user's current storage usage.
    Calculated dynamically via SUM(file_size) — always accurate.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        info = get_storage_info(request.user)
        return Response(info, status=status.HTTP_200_OK)
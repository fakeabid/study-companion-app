from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Workspace
from .serializers import WorkspaceSerializer


class WorkspaceListCreateView(APIView):
    """
    GET  /api/workspaces/   — list all workspaces for the authenticated user
    POST /api/workspaces/   — create a new workspace

    Ownership is enforced at the queryset level: we always filter by
    request.user, so it is structurally impossible for this view to return
    another user's data — even if the queryset logic changes in the future,
    the filter is the first operation.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Return only workspaces belonging to the authenticated user."""
        return Workspace.objects.filter(user=self.request.user)

    def get(self, request):
        workspaces = self.get_queryset()
        serializer = WorkspaceSerializer(workspaces, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = WorkspaceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # We inject the user here — the client never sends it.
        # This is the correct pattern: trust the token, not the body.
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class WorkspaceDetailView(APIView):
    """
    PATCH  /api/workspaces/<id>/  — rename a workspace
    DELETE /api/workspaces/<id>/  — delete a workspace

    get_object() raises Http404 if the workspace doesn't exist OR if it
    belongs to a different user. The caller cannot distinguish between the
    two cases — this is intentional (avoids confirming resource existence).
    """

    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        """
        Fetch a workspace by PK, scoped to the authenticated user.

        Raises Http404 if not found or not owned by the requester.
        We do NOT use get_object_or_404 from django.shortcuts because it
        only filters by PK; we need the user filter too.
        """
        try:
            return Workspace.objects.get(pk=pk, user=self.request.user)
        except Workspace.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound()

    def patch(self, request, pk):
        workspace = self.get_object(pk)
        serializer = WorkspaceSerializer(
            workspace,
            data=request.data,
            partial=True,  # Only update supplied fields
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        workspace = self.get_object(pk)
        workspace.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
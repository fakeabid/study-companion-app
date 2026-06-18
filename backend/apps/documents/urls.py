from django.urls import path
from .views import (
    DocumentUploadView,
    WorkspaceDocumentListView,
    DocumentDetailView,
    DocumentDeleteView,
    StorageUsageView,
)

app_name = "documents"

urlpatterns = [
    path("documents/upload/", DocumentUploadView.as_view(), name="upload"),
    path("documents/<uuid:pk>/", DocumentDetailView.as_view(), name="detail"),
    path("documents/<uuid:pk>/delete/", DocumentDeleteView.as_view(), name="delete"),
    path("storage/", StorageUsageView.as_view(), name="storage"),
    # Nested under workspaces to reflect the data hierarchy
    path(
        "workspaces/<uuid:workspace_id>/documents/",
        WorkspaceDocumentListView.as_view(),
        name="workspace_documents",
    ),
]
from django.urls import path
from .views import WorkspaceDetailView, WorkspaceListCreateView

app_name = "workspaces"

urlpatterns = [
    path("", WorkspaceListCreateView.as_view(), name="list_create"),
    path("<uuid:pk>/", WorkspaceDetailView.as_view(), name="detail"),
]
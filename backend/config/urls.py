from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.users.urls", namespace="users")),
    path("api/workspaces/", include("apps.workspaces.urls", namespace="workspaces")),
]
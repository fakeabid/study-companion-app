from django.contrib import admin
from .models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "user__email"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
from django.contrib import admin
from .models import Document


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "original_filename",
        "file_type",
        "file_size",
        "uploaded_by",
        "workspace",
        "uploaded_at",
    ]
    list_filter = ["file_type", "uploaded_at"]
    search_fields = ["original_filename", "uploaded_by__email", "workspace__name"]
    ordering = ["-uploaded_at"]
    readonly_fields = ["id", "file_size", "file_type", "uploaded_at"]
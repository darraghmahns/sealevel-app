# files/admin.py

from django.contrib import admin
from .models import File, FileAccess

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'uploaded_file')
    search_fields = ('owner__email', 'uploaded_file')
    list_filter = ('uploaded_date',)
    ordering = ('-uploaded_date',)

@admin.register(FileAccess)
class FileAccessAdmin(admin.ModelAdmin):
    list_display = ('file', 'user', 'access_granted_at')
    search_fields = ('file__file', 'user__email')
    list_filter = ('access_granted_at',)
    ordering = ('-access_granted_at',)
from django.contrib import admin
from .models import AccessLog

@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'file', 'action', 'timestamp')
    search_fields = ('user__email', 'file__file')
    list_filter = ('action', 'timestamp')
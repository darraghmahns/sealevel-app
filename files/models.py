from django.db import models
from django.conf import settings

class File(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_files'
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return f"File {self.file.name} associated with {self.owner}"
    
class FileAccess(models.Model):
    file = models.ForeignKey(
        File,
        on_delete=models.CASCADE,
        related_name='access_list'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_access'
    )
    access_granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('file', 'user')

    def __str__(self):
        return f"{self.user.email} has viewer access to {self.file.file.name}"


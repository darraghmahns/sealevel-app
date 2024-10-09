# files/models.py

from django.db import models
from django.conf import settings
from users.models import User

class File(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_files')
    uploaded_file = models.FileField(upload_to='user_files/')
    transaction_ids = models.JSONField(default=list)
    shared_with = models.ManyToManyField(User, related_name='shared_files')
    uploaded_date = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_files', null=True, blank=True)

    def __str__(self):
        return self.uploaded_file.name

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
        return f"{self.user.email} has viewer access to {self.uploaded_file.name}"

# class File(models.Model):
#     owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='files')
#     file = models.FileField(upload_to='uploads/%Y/%m/%d/')
#     uploaded_at = models.DateTimeField(auto_now_add=True)
#     uploaded_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='uploaded_files'
#     )
#     description = models.TextField(blank=True)
#     solana_account_pubkey = models.CharField(max_length=44, unique=True, null=True, blank=True)
#     transaction_ids = models.JSONField(default=list)

#     def __str__(self):
#         return f"File {self.file.name} associated with {self.owner}"
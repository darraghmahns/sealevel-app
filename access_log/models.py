from django.db import models
from django.conf import settings  # Use settings to get AUTH_USER_MODEL
from files.models import File  # Import the File model from the files app

class AccessLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.file} - {self.action} - {self.timestamp}"
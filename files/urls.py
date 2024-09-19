from django.urls import path
from .views import (
    file_upload_view,
    file_list_view,
    file_download_view,
    share_file_view,
    revoke_access_view,
    file_access_log_view
)

urlpatterns = [
    path('upload/', file_upload_view, name='file-upload'),
    path('list/', file_list_view, name='file-list'),
    path('download/<int:pk>/', file_download_view, name='file-download'),
    path('share/<int:pk>/', share_file_view, name='file-share'),
    path('revoke/<int:file_id>/<int:user_id>/', revoke_access_view, name='revoke-access'),
    path('access-log/<int:pk>/', file_access_log_view, name='file-access-log'),
]
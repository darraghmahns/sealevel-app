from django.utils.deprecation import MiddlewareMixin
from .models import AccessLog, File
from solana_utils import log_access

class AccessLogMiddleware(MiddlewareMixin):
	def process_view(self, request, view_func, view_args, view_kwargs):
		if request.user.is_authenticated:
			file_id = request.GET.get('file_id')
			if file_id:
				try:
					file = File.objects.get(id=file_id)
					# Log to the database
					AccessLog.objects.create(user=request.user, file=file, action=request.path)

					# Log to Solana
					log_access(request.user.id, file_id, request.path)
				except File.DoesNotExist:
					pass
		return None
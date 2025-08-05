from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

class AccessLogMiddleware(MiddlewareMixin):
	def process_view(self, request, view_func, view_args, view_kwargs):
		# Only process if Solana is enabled and user is authenticated
		if getattr(settings, 'SOLANA_ENABLED', False) and request.user.is_authenticated:
			file_id = request.GET.get('file_id')
			if file_id:
				try:
					# Conditional imports only when needed
					from .models import File
					from .solana_utils import log_access
					
					file = File.objects.get(id=file_id)
					# Log to Solana
					log_access(request.user.id, file_id, request.path)
				except (ImportError, File.DoesNotExist):
					# Silently fail if Solana packages not available or file not found
					pass
		return None
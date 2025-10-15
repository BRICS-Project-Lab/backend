from django.utils.deprecation import MiddlewareMixin
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog
import json

class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware для логирования действий пользователей.
    Сохраняет IP адрес и User-Agent в request,
    чтобы потом можно было использовать при аудите.
    """
    
    def process_request(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            request.ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            request.ip_address = request.META.get('REMOTE_ADDR')
        
        request.user_agent = request.META.get('HTTP_USER_AGENT', '')
        return None

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware для добавления заголовков безопасности в ответы.
    """

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response

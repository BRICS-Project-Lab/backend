from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """Кастомный обработчик исключений для API"""
    
    # Получаем стандартный ответ
    response = exception_handler(exc, context)
    
    if response is not None:
        # Логируем ошибку
        view = context.get('view')
        request = context.get('request')
        
        logger.error(
            f"API Error in {view.__class__.__name__}: {exc}",
            extra={
                'request': request,
                'view': view,
                'exception': exc
            }
        )
        
        # Стандартизируем формат ошибок
        custom_response_data = {
            'error': True,
            'message': 'An error occurred',
            'details': response.data,
            'status_code': response.status_code
        }
        
        # Специальная обработка разных типов ошибок
        if response.status_code == 400:
            custom_response_data['message'] = 'Invalid request data'
        elif response.status_code == 401:
            custom_response_data['message'] = 'Authentication required'
        elif response.status_code == 403:
            custom_response_data['message'] = 'Permission denied'
        elif response.status_code == 404:
            custom_response_data['message'] = 'Resource not found'
        elif response.status_code == 405:
            custom_response_data['message'] = 'Method not allowed'
        elif response.status_code == 429:
            custom_response_data['message'] = 'Too many requests'
        elif response.status_code >= 500:
            custom_response_data['message'] = 'Internal server error'
            # Не показываем детали серверных ошибок в продакшене
            if not context.get('request').debug:
                custom_response_data['details'] = 'An internal error occurred'
        
        response.data = custom_response_data
    
    # Обработка Django ValidationError
    elif isinstance(exc, DjangoValidationError):
        custom_response_data = {
            'error': True,
            'message': 'Validation error',
            'details': exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
            'status_code': 400
        }
        response = Response(custom_response_data, status=status.HTTP_400_BAD_REQUEST)
    
    return response

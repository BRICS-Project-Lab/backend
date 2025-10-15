from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.utils import timezone
import sys
import platform

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Проверка здоровья приложения
    
    Проверяет:
    - Работоспособность Django
    - Подключение к базе данных
    - Основные зависимости
    """
    health_status = {
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Проверка базы данных
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['status'] = 'error'
        health_status['checks']['database'] = f'error: {str(e)}'
    
    # Проверка Django
    health_status['checks']['django'] = 'ok'
    
    # Проверка импортов
    try:
        from apps.ai_modules.models import AIModule
        from apps.accounts.models import User
        health_status['checks']['models'] = 'ok'
    except Exception as e:
        health_status['status'] = 'error'
        health_status['checks']['models'] = f'error: {str(e)}'
    
    status_code = 200 if health_status['status'] == 'ok' else 503
    
    return JsonResponse(health_status, status=status_code)

@csrf_exempt
@require_http_methods(["GET"])
def ping(request):
    """
    Простой ping endpoint для проверки доступности
    """
    return JsonResponse({
        'status': 'pong',
        'timestamp': timezone.now().isoformat()
    })

@csrf_exempt
@require_http_methods(["GET"])
def system_info(request):
    """
    Информация о системе (доступно только администраторам)
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'error': 'Authentication required'
        }, status=401)
    
    if not (hasattr(request.user, 'is_admin') and request.user.is_admin()):
        return JsonResponse({
            'error': 'Admin access required'
        }, status=403)
    
    # Подсчет объектов
    from apps.ai_modules.models import AIModule
    from apps.accounts.models import User
    from apps.publications.models import Publication
    from apps.tags.models import Tag
    
    system_data = {
        'system': {
            'python_version': sys.version,
            'platform': platform.platform(),
            'django_version': import_django_version(),
        },
        'database': {
            'engine': connection.settings_dict['ENGINE'],
            'name': connection.settings_dict['NAME'],
        },
        'statistics': {
            'total_modules': AIModule.objects.count(),
            'active_modules': AIModule.objects.filter(status=AIModule.Status.ACTIVE).count(),
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True, is_blocked=False).count(),
            'total_publications': Publication.objects.count(),
            'total_tags': Tag.objects.filter(is_active=True).count(),
        },
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(system_data)

@csrf_exempt
@require_http_methods(["GET"])
def version_info(request):
    """
    Информация о версии приложения
    """
    version_data = {
        'application': 'BRICS AI Registry',
        'version': '1.0.0',
        'api_version': 'v1',
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        'django_version': import_django_version(),
        'timestamp': timezone.now().isoformat()
    }
    
    return JsonResponse(version_data)

def import_django_version():
    """Получение версии Django"""
    try:
        import django
        return django.get_version()
    except:
        return 'unknown'

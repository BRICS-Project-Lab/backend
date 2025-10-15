from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, Q, Avg
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.utils import timezone
from datetime import timedelta, datetime
from apps.ai_modules.models import AIModule, AIModuleLike
from apps.tags.models import Tag, TagCategory
from apps.publications.models import Publication
from apps.accounts.models import User
from apps.common.models import Country, AuditLog

class OverviewAnalyticsView(APIView):
    """Общая аналитика системы"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @method_decorator(cache_page(60 * 15))  # Кэш на 15 минут
    def get(self, request):
        now = timezone.now()
        last_month = now - timedelta(days=30)
        
        # Общие метрики
        total_modules = AIModule.objects.filter(status=AIModule.Status.ACTIVE).count()
        total_users = User.objects.filter(is_active=True, is_blocked=False).count()
        total_publications = Publication.objects.count()
        total_likes = AIModuleLike.objects.count()
        
        # Новые за месяц
        new_modules_month = AIModule.objects.filter(
            created_at__gte=last_month,
            status=AIModule.Status.ACTIVE
        ).count()
        
        new_users_month = User.objects.filter(
            created_at__gte=last_month,
            is_active=True
        ).count()
        
        # Топ стран
        top_countries = AIModule.objects.filter(
            status=AIModule.Status.ACTIVE
        ).values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Топ тегов
        top_tags = Tag.objects.annotate(
            usage_count=Count('aimoduletag')
        ).order_by('-usage_count')[:10]
        
        data = {
            'overview': {
                'total_modules': total_modules,
                'total_users': total_users,
                'total_publications': total_publications,
                'total_likes': total_likes,
                'new_modules_month': new_modules_month,
                'new_users_month': new_users_month,
            },
            'top_countries': [
                {'country': item['country'], 'count': item['count']}
                for item in top_countries
            ],
            'top_tags': [
                {'id': tag.id, 'name': tag.name, 'count': tag.usage_count}
                for tag in top_tags
            ]
        }
        
        return Response(data)

class ModulesAnalyticsView(APIView):
    """Аналитика по модулям"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        # Фильтры из параметров запроса
        country = request.query_params.get('country')
        date_from = request.query_params.get('date_from')
        date_to = request.query_params.get('date_to')
        
        queryset = AIModule.objects.filter(status=AIModule.Status.ACTIVE)
        
        if country:
            queryset = queryset.filter(country=country)
        
        if date_from:
            try:
                date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=date_from)
            except ValueError:
                pass
        
        if date_to:
            try:
                date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=date_to)
            except ValueError:
                pass
        
        # Статистика по статусам
        status_stats = dict(
            AIModule.objects.values('status').annotate(
                count=Count('id')
            ).values_list('status', 'count')
        )
        
        # Распределение по количеству параметров
        param_ranges = [
            ('< 1M', queryset.filter(params_count__lt=1000000).count()),
            ('1M - 10M', queryset.filter(params_count__gte=1000000, params_count__lt=10000000).count()),
            ('10M - 100M', queryset.filter(params_count__gte=10000000, params_count__lt=100000000).count()),
            ('> 100M', queryset.filter(params_count__gte=100000000).count()),
        ]
        
        # Средние метрики
        avg_params = queryset.aggregate(avg=Avg('params_count'))['avg'] or 0
        avg_likes = queryset.annotate(
            like_count=Count('likes')
        ).aggregate(avg=Avg('like_count'))['avg'] or 0
        
        # Топ лайкнутых модулей
        most_liked = queryset.annotate(
            like_count=Count('likes')
        ).order_by('-like_count')[:5]
        
        data = {
            'total_count': queryset.count(),
            'status_distribution': status_stats,
            'parameter_ranges': param_ranges,
            'averages': {
                'parameters': round(avg_params),
                'likes': round(avg_likes, 2)
            },
            'most_liked': [
                {
                    'id': module.id,
                    'name': module.name,
                    'company': module.company,
                    'like_count': module.like_count
                }
                for module in most_liked
            ]
        }
        
        return Response(data)

class TagsAnalyticsView(APIView):
    """Аналитика по тегам"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @method_decorator(cache_page(60 * 30))  # Кэш на 30 минут
    def get(self, request):
        # Статистика по категориям
        category_stats = []
        for category in TagCategory.objects.filter(is_active=True):
            tags_count = category.tags.filter(is_active=True).count()
            usage_count = sum(
                tag.aimoduletag_set.count() 
                for tag in category.tags.filter(is_active=True)
            )
            
            category_stats.append({
                'id': category.id,
                'name': category.name,
                'tags_count': tags_count,
                'total_usage': usage_count
            })
        
        # Самые используемые теги
        popular_tags = Tag.objects.filter(is_active=True).annotate(
            usage_count=Count('aimoduletag')
        ).order_by('-usage_count')[:15]
        
        # Неиспользуемые теги
        unused_tags = Tag.objects.filter(
            is_active=True,
            aimoduletag__isnull=True
        ).count()
        
        data = {
            'categories': category_stats,
            'popular_tags': [
                {
                    'id': tag.id,
                    'name': tag.name,
                    'category': tag.category.name,
                    'usage_count': tag.usage_count,
                    'color': tag.get_color_or_default()
                }
                for tag in popular_tags
            ],
            'unused_tags_count': unused_tags,
            'total_tags': Tag.objects.filter(is_active=True).count()
        }
        
        return Response(data)

class UsersAnalyticsView(APIView):
    """Аналитика по пользователям"""
    permission_classes = [permissions.IsAdminUser]  # Только админы
    
    def get(self, request):
        # Общая статистика пользователей
        total_users = User.objects.filter(is_active=True).count()
        blocked_users = User.objects.filter(is_blocked=True).count()
        
        # Распределение по ролям
        role_distribution = dict(
            User.objects.filter(is_active=True).values('role').annotate(
                count=Count('id')
            ).values_list('role', 'count')
        )
        
        # Активность по странам
        country_activity = User.objects.filter(
            is_active=True
        ).values('country').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Пользователи с наибольшим количеством модулей
        top_contributors = User.objects.filter(
            is_active=True
        ).annotate(
            modules_count=Count('ai_modules', filter=Q(ai_modules__status=AIModule.Status.ACTIVE))
        ).order_by('-modules_count')[:10]
        
        # Новые пользователи за последние дни
        last_week = timezone.now() - timedelta(days=7)
        new_users_week = User.objects.filter(
            created_at__gte=last_week,
            is_active=True
        ).count()
        
        data = {
            'summary': {
                'total_users': total_users,
                'blocked_users': blocked_users,
                'new_users_week': new_users_week
            },
            'role_distribution': role_distribution,
            'country_activity': [
                {'country': item['country'], 'count': item['count']}
                for item in country_activity
            ],
            'top_contributors': [
                {
                    'id': user.id,
                    'username': user.username,
                    'organization': user.organization,
                    'modules_count': user.modules_count
                }
                for user in top_contributors if user.modules_count > 0
            ]
        }
        
        return Response(data)

class ModulesTrendsView(APIView):
    """Тренды создания модулей по времени"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @method_decorator(cache_page(60 * 30))  # Кэш на 30 минут
    def get(self, request):
        # Параметры периода
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Генерируем даты
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Собираем данные по дням
        trends_data = []
        for date in date_range:
            modules_created = AIModule.objects.filter(
                created_at__date=date
            ).count()
            
            modules_activated = AIModule.objects.filter(
                published_at__date=date,
                status=AIModule.Status.ACTIVE
            ).count()
            
            trends_data.append({
                'date': date.isoformat(),
                'created': modules_created,
                'activated': modules_activated
            })
        
        # Суммарная статистика за период
        period_stats = {
            'total_created': AIModule.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).count(),
            'total_activated': AIModule.objects.filter(
                published_at__date__gte=start_date,
                published_at__date__lte=end_date,
                status=AIModule.Status.ACTIVE
            ).count(),
        }
        
        return Response({
            'trends': trends_data,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            },
            'stats': period_stats
        })

class TagUsageView(APIView):
    """Детальная статистика использования тегов"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get(self, request):
        # Фильтр по категории (опционально)
        category_id = request.query_params.get('category_id')
        
        queryset = Tag.objects.filter(is_active=True)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Аннотируем использование
        tags_with_usage = queryset.annotate(
            usage_count=Count('aimoduletag')
        ).order_by('-usage_count')
        
        data = [
            {
                'id': tag.id,
                'name': tag.name,
                'category': tag.category.name,
                'usage_count': tag.usage_count,
                'color': tag.get_color_or_default()
            }
            for tag in tags_with_usage
        ]
        
        return Response(data)

class UserActivityView(APIView):
    """Активность пользователей по времени"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Генерируем даты
        date_range = []
        current_date = start_date
        while current_date <= end_date:
            date_range.append(current_date)
            current_date += timedelta(days=1)
        
        # Собираем активность
        activity_data = []
        for date in date_range:
            new_users = User.objects.filter(
                created_at__date=date
            ).count()
            
            active_users = AuditLog.objects.filter(
                timestamp__date=date
            ).values('performed_by').distinct().count()
            
            activity_data.append({
                'date': date.isoformat(),
                'new_users': new_users,
                'active_users': active_users
            })
        
        return Response({
            'activity': activity_data,
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days
            }
        })

class CountriesAnalyticsView(APIView):
    """Аналитика по странам"""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    @method_decorator(cache_page(60 * 60))  # Кэш на 1 час
    def get(self, request):
        # Модули по странам
        modules_by_country = AIModule.objects.filter(
            status=AIModule.Status.ACTIVE
        ).values('country').annotate(
            modules_count=Count('id'),
            avg_params=Avg('params_count'),
            total_likes=Count('likes')
        ).order_by('-modules_count')
        
        # Пользователи по странам
        users_by_country = User.objects.filter(
            is_active=True
        ).values('country').annotate(
            users_count=Count('id')
        )
        users_dict = {item['country']: item['users_count'] for item in users_by_country}
        
        # Объединяем данные
        countries_data = []
        for item in modules_by_country:
            if item['country']:
                countries_data.append({
                    'country': item['country'],
                    'modules_count': item['modules_count'],
                    'users_count': users_dict.get(item['country'], 0),
                    'avg_params': round(item['avg_params'] or 0),
                    'total_likes': item['total_likes']
                })
        
        # Страны БРИКС отдельно
        brics_countries = ['Brazil', 'Russia', 'India', 'China', 'South Africa']
        brics_stats = [c for c in countries_data if c['country'] in brics_countries]
        
        return Response({
            'all_countries': countries_data,
            'brics_countries': brics_stats,
            'total_countries': len(countries_data)
        })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticatedOrReadOnly])
@cache_page(60 * 60)  # Кэш на 1 час
def get_activity_timeline(request):
    """Временная шкала активности системы"""
    
    days = int(request.GET.get('days', 30))
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Генерируем даты
    date_range = []
    current_date = start_date
    while current_date <= end_date:
        date_range.append(current_date)
        current_date += timedelta(days=1)
    
    # Собираем статистику по дням
    timeline_data = []
    for date in date_range:
        modules_created = AIModule.objects.filter(
            created_at__date=date
        ).count()
        
        users_registered = User.objects.filter(
            created_at__date=date
        ).count()
        
        publications_added = Publication.objects.filter(
            created_at__date=date
        ).count()
        
        timeline_data.append({
            'date': date.isoformat(),
            'modules_created': modules_created,
            'users_registered': users_registered,
            'publications_added': publications_added
        })
    
    return Response({
        'timeline': timeline_data,
        'period': {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'days': days
        }
    })

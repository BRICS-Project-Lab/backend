from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.pagination import PageNumberPagination
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Prefetch
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.utils import timezone

from apps.ai_modules.models import AIModule, AIModuleLike, AIModuleFile
from apps.tags.models import Tag, TagCategory, AIModuleTag
from apps.publications.models import Publication
from apps.accounts.models import User
from apps.common.models import Country, AuditLog

from .serializers import (
    AIModuleListSerializer, AIModuleDetailSerializer, AIModuleCreateSerializer,
    TagSerializer, TagCategorySerializer, PublicationSerializer,
    UserProfileSerializer, CountrySerializer, AIModuleFileSerializer
)
from .filters import AIModuleFilter, TagFilter, PublicationFilter
from .permissions import IsOwnerOrReadOnly, IsAdminOrReadOnly, IsOwnerOrAdminOrReadOnly
from .pagination import CustomPageNumberPagination
from .throttling import BurstRateThrottle

class AIModuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet для управления ИИ-модулями.
    
    Предоставляет стандартные CRUD операции плюс дополнительные действия:
    - like/unlike модуля
    - экспорт данных
    - статистика
    - поиск похожих модулей
    """
    
    serializer_class = AIModuleDetailSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = AIModuleFilter
    search_fields = ['name', 'company', 'task_short_description', 'details__description']
    ordering_fields = ['created_at', 'name', 'params_count', 'like_count']
    ordering = ['-created_at']
    pagination_class = CustomPageNumberPagination
    throttle_classes = [AnonRateThrottle, UserRateThrottle, BurstRateThrottle]
    
    def get_permissions(self):
        """Настройка разрешений в зависимости от действия"""
        if self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['update', 'partial_update', 'destroy']:
            permission_classes = [IsOwnerOrAdminOrReadOnly]
        elif self.action in ['like', 'unlike']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от действия"""
        if self.action == 'list':
            return AIModuleListSerializer
        elif self.action == 'create':
            return AIModuleCreateSerializer
        return AIModuleDetailSerializer
    
    def get_queryset(self):
        """Оптимизированный QuerySet с prefetch_related"""
        queryset = AIModule.objects.select_related(
            'created_by'
        ).prefetch_related(
            'likes',
            Prefetch(
                'aimoduletag_set',
                queryset=AIModuleTag.objects.select_related('tag__category')
            )
        )
        
        # Фильтр по статусу для обычных пользователей
        if not (self.request.user.is_authenticated and self.request.user.is_admin()):
            queryset = queryset.filter(status=AIModule.Status.ACTIVE)
        
        # Для детального просмотра добавляем дополнительные связи
        if self.action == 'retrieve':
            queryset = queryset.select_related('details').prefetch_related(
                'publications',
                'files'
            )
        
        # Аннотация количества лайков
        queryset = queryset.annotate(
            like_count=Count('likes', distinct=True)
        )
        
        return queryset
    
    def perform_create(self, serializer):
        """Создание модуля с автоматическим назначением создателя"""
        serializer.save(
            created_by=self.request.user,
            status=AIModule.Status.DRAFT
        )
        
        # Логируем создание
        AuditLog.objects.create(
            content_object=serializer.instance,
            action=AuditLog.Action.CREATE,
            performed_by=self.request.user,
            ip_address=getattr(self.request, 'ip_address', None),
            comment=f"Created AI module '{serializer.instance.name}'"
        )
    
    def perform_update(self, serializer):
        """Обновление с логированием изменений"""
        old_status = self.get_object().status
        instance = serializer.save()
        
        # Логируем изменения
        if old_status != instance.status:
            AuditLog.objects.create(
                content_object=instance,
                action=AuditLog.Action.UPDATE,
                performed_by=self.request.user,
                ip_address=getattr(self.request, 'ip_address', None),
                comment=f"Status changed from {old_status} to {instance.status}"
            )
    
    @action(detail=True, methods=['post'])
    def like(self, request, pk=None):
        """Поставить лайк модулю"""
        module = self.get_object()
        
        like, created = AIModuleLike.objects.get_or_create(
            user=request.user,
            ai_module=module
        )
        
        if created:
            # Логируем лайк
            AuditLog.objects.create(
                content_object=module,
                action=AuditLog.Action.LIKE,
                performed_by=request.user,
                ip_address=getattr(request, 'ip_address', None)
            )
            
            return Response({
                'liked': True,
                'like_count': module.likes.count(),
                'message': 'Module liked successfully'
            })
        else:
            return Response({
                'liked': True,
                'like_count': module.likes.count(),
                'message': 'Already liked'
            })
    
    @action(detail=True, methods=['delete'])
    def unlike(self, request, pk=None):
        """Убрать лайк с модуля"""
        module = self.get_object()
        
        try:
            like = AIModuleLike.objects.get(user=request.user, ai_module=module)
            like.delete()
            
            # Логируем убирание лайка
            AuditLog.objects.create(
                content_object=module,
                action=AuditLog.Action.UNLIKE,
                performed_by=request.user,
                ip_address=getattr(request, 'ip_address', None)
            )
            
            return Response({
                'liked': False,
                'like_count': module.likes.count(),
                'message': 'Like removed successfully'
            })
        except AIModuleLike.DoesNotExist:
            return Response({
                'liked': False,
                'like_count': module.likes.count(),
                'message': 'Not liked'
            })
    
    @action(detail=True, methods=['get'])
    def similar(self, request, pk=None):
        """Получить похожие модули по тегам"""
        module = self.get_object()
        
        # Кешируем результат на 1 час
        cache_key = f"similar_modules_{module.id}"
        similar_modules = cache.get(cache_key)
        
        if similar_modules is None:
            module_tags = module.aimoduletag_set.values_list('tag_id', flat=True)
            
            similar_modules = AIModule.objects.filter(
                aimoduletag_set__tag_id__in=module_tags,
                status=AIModule.Status.ACTIVE
            ).exclude(
                id=module.id
            ).annotate(
                common_tags_count=Count('aimoduletag_set__tag_id', 
                    filter=Q(aimoduletag_set__tag_id__in=module_tags))
            ).order_by('-common_tags_count')[:5]
            
            cache.set(cache_key, similar_modules, 3600)  # 1 час
        
        serializer = AIModuleListSerializer(similar_modules, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 15))  # Кеш на 15 минут
    def stats(self, request):
        """Статистика по модулям"""
        queryset = self.filter_queryset(self.get_queryset())
        
        stats = {
            'total_modules': queryset.count(),
            'by_country': dict(
                queryset.values('country').annotate(
                    count=Count('id')
                ).order_by('-count').values_list('country', 'count')[:10]
            ),
            'by_status': dict(
                queryset.values('status').annotate(
                    count=Count('id')
                ).values_list('status', 'count')
            ),
            'total_likes': AIModuleLike.objects.filter(
                ai_module__in=queryset
            ).count(),
            'most_liked': AIModuleListSerializer(
                queryset.order_by('-like_count')[:5],
                many=True,
                context={'request': request}
            ).data
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Экспорт модулей в различных форматах"""
        format_type = request.query_params.get('format', 'json')
        
        if format_type not in ['json', 'csv', 'xlsx']:
            return Response(
                {'error': 'Unsupported format. Use: json, csv, xlsx'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.filter_queryset(self.get_queryset())
        
        if format_type == 'json':
            serializer = AIModuleListSerializer(
                queryset, many=True, context={'request': request}
            )
            return Response({
                'count': queryset.count(),
                'results': serializer.data,
                'exported_at': timezone.now().isoformat()
            })
        
        # CSV/XLSX экспорт
        from apps.common.utils import export_queryset_to_csv, export_queryset_to_xlsx
        
        fields = [
            ('name', 'Name'),
            ('company', 'Company'),
            ('country', 'Country'),
            ('params_count', 'Parameters Count'),
            ('task_short_description', 'Description'),
            ('status', 'Status'),
            ('created_at', 'Created At'),
            ('like_count', 'Likes')
        ]
        
        if format_type == 'csv':
            return export_queryset_to_csv(queryset, fields, 'ai_modules.csv')
        else:  # xlsx
            return export_queryset_to_xlsx(queryset, fields, 'ai_modules.xlsx')
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrAdminOrReadOnly])
    def approve(self, request, pk=None):
        """Одобрить модуль (только администраторы)"""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only administrators can approve modules'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        module = self.get_object()
        
        if module.status != AIModule.Status.ON_REVIEW:
            return Response(
                {'error': 'Only modules under review can be approved'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        module.status = AIModule.Status.ACTIVE
        module.published_at = timezone.now()
        module.save()
        
        # Логируем одобрение
        AuditLog.objects.create(
            content_object=module,
            action=AuditLog.Action.APPROVE,
            performed_by=request.user,
            ip_address=getattr(request, 'ip_address', None),
            comment=request.data.get('comment', '')
        )
        
        # Уведомляем автора
        from apps.common.utils import send_notification_email
        send_notification_email(
            user=module.created_by,
            subject='Your AI module has been approved',
            template_name='module_approved',
            context={'module': module}
        )
        
        return Response({
            'message': 'Module approved successfully',
            'status': module.status
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsOwnerOrAdminOrReadOnly])
    def reject(self, request, pk=None):
        """Отклонить модуль (только администраторы)"""
        if not request.user.is_admin():
            return Response(
                {'error': 'Only administrators can reject modules'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        module = self.get_object()
        comment = request.data.get('comment', '')
        
        if not comment:
            return Response(
                {'error': 'Comment is required for rejection'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        module.status = AIModule.Status.REJECTED
        module.save()
        
        # Логируем отклонение
        AuditLog.objects.create(
            content_object=module,
            action=AuditLog.Action.REJECT,
            performed_by=request.user,
            ip_address=getattr(request, 'ip_address', None),
            comment=comment
        )
        
        # Уведомляем автора
        from apps.common.utils import send_notification_email
        send_notification_email(
            user=module.created_by,
            subject='Your AI module has been rejected',
            template_name='module_rejected',
            context={'module': module, 'comment': comment}
        )
        
        return Response({
            'message': 'Module rejected successfully',
            'status': module.status,
            'comment': comment
        })

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для тегов (только чтение).
    Создание и редактирование тегов доступно только через админку.
    """
    
    queryset = Tag.objects.filter(is_active=True).select_related('category')
    serializer_class = TagSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = TagFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'usage_count']
    ordering = ['category__order', 'name']
    pagination_class = CustomPageNumberPagination
    
    def get_queryset(self):
        """Добавляем аннотацию количества использований"""
        return super().get_queryset().annotate(
            usage_count=Count('aimoduletag', distinct=True)
        )
    
    @action(detail=False, methods=['get'])
    @method_decorator(cache_page(60 * 30))  # Кеш на 30 минут
    def popular(self, request):
        """Популярные теги"""
        popular_tags = self.get_queryset().order_by('-usage_count')[:20]
        serializer = self.get_serializer(popular_tags, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Теги сгруппированные по категориям"""
        categories = TagCategory.objects.filter(is_active=True).prefetch_related('tags')
        
        result = []
        for category in categories:
            tags = category.tags.filter(is_active=True).annotate(
                usage_count=Count('aimoduletag', distinct=True)
            ).order_by('name')
            
            result.append({
                'id': category.id,
                'name': category.name,
                'description': category.description,
                'tags': TagSerializer(tags, many=True, context={'request': request}).data
            })
        
        return Response(result)

class TagCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для категорий тегов"""
    
    queryset = TagCategory.objects.filter(is_active=True).prefetch_related('tags')
    serializer_class = TagCategorySerializer
    ordering = ['order', 'name']
    pagination_class = None  # Отключаем пагинацию для категорий

class PublicationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для публикаций (только чтение).
    Публикации создаются через интерфейс модулей.
    """
    
    queryset = Publication.objects.select_related('ai_module', 'added_by')
    serializer_class = PublicationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PublicationFilter
    search_fields = ['title', 'authors', 'journal_conference', 'abstract']
    ordering_fields = ['publication_date', 'citation_count', 'created_at']
    ordering = ['-publication_date']
    pagination_class = CustomPageNumberPagination

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для пользователей (только чтение публичных данных).
    Регистрация и управление профилем через отдельные эндпоинты.
    """
    
    queryset = User.objects.filter(is_active=True).select_related('profile')
    serializer_class = UserProfileSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['username', 'first_name', 'last_name', 'organization']
    ordering_fields = ['username', 'created_at']
    ordering = ['username']
    pagination_class = CustomPageNumberPagination
    
    def get_queryset(self):
        """Скрываем заблокированных пользователей"""
        return super().get_queryset().filter(is_blocked=False)
    
    @action(detail=True, methods=['get'])
    def modules(self, request, pk=None):
        """Модули пользователя"""
        user = self.get_object()
        modules = AIModule.objects.filter(
            created_by=user,
            status=AIModule.Status.ACTIVE
        ).annotate(like_count=Count('likes'))
        
        serializer = AIModuleListSerializer(
            modules, many=True, context={'request': request}
        )
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Статистика пользователя"""
        user = self.get_object()
        
        stats = {
            'total_modules': user.ai_modules.filter(status=AIModule.Status.ACTIVE).count(),
            'total_likes_received': AIModuleLike.objects.filter(
                ai_module__created_by=user
            ).count(),
            'total_publications': Publication.objects.filter(
                ai_module__created_by=user
            ).count(),
            'member_since': user.created_at.isoformat()
        }
        
        return Response(stats)

class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet для стран"""
    
    queryset = Country.objects.all().order_by('name')
    serializer_class = CountrySerializer
    pagination_class = None
    
    @action(detail=False, methods=['get'])
    def brics(self, request):
        """Только страны БРИКС"""
        brics_countries = self.get_queryset().filter(is_brics_member=True)
        serializer = self.get_serializer(brics_countries, many=True)
        return Response(serializer.data)

class AIModuleFileViewSet(viewsets.ModelViewSet):
    """ViewSet для файлов ИИ-модулей"""
    
    serializer_class = AIModuleFileSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    
    def get_queryset(self):
        ai_module_pk = self.kwargs.get('ai_module_pk')
        if ai_module_pk:
            return AIModuleFile.objects.filter(ai_module_id=ai_module_pk)
        return AIModuleFile.objects.none()
    
    def perform_create(self, serializer):
        ai_module_pk = self.kwargs.get('ai_module_pk')
        ai_module = get_object_or_404(AIModule, pk=ai_module_pk)
        
        # Проверяем права доступа
        if not ai_module.can_edit(self.request.user):
            raise PermissionDenied("You don't have permission to add files to this module")
        
        serializer.save(
            ai_module=ai_module,
            uploaded_by=self.request.user
        )

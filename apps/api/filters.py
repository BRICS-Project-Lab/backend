import django_filters
from django.db.models import Q, Count
from django_filters import rest_framework as filters
from apps.ai_modules.models import AIModule
from apps.tags.models import Tag, TagCategory
from apps.publications.models import Publication
from apps.accounts.models import User

class AIModuleFilter(django_filters.FilterSet):
    """Расширенные фильтры для ИИ-модулей"""
    
    # Текстовые фильтры
    name = django_filters.CharFilter(lookup_expr='icontains')
    # company = django_filters.CharFilter(lookup_expr='icontains')
    companies = django_filters.BaseInFilter(field_name='company', lookup_expr='in')
    country_names = django_filters.BaseInFilter(
        field_name='country__name',
        lookup_expr='in'
    )



    tags = django_filters.BaseInFilter(
        field_name='aimoduletag__tag',
        lookup_expr='in'
    )

    
    tags = django_filters.ModelMultipleChoiceFilter(
        field_name='aimoduletag__tag',
        queryset=Tag.objects.filter(is_active=True),
        distinct=True,
        conjoined=False  # OR вместо AND
    )
    
    tags_all = django_filters.ModelMultipleChoiceFilter(
        field_name='aimoduletag__tag',
        queryset=Tag.objects.filter(is_active=True),
        distinct=True,
        conjoined=True  # AND - все указанные теги должны быть
    )
    
    ability = django_filters.BaseInFilter(
        field_name='details__ability',
        lookup_expr='in'
    )

    detailed_status = django_filters.BaseInFilter(
        field_name='details__status',
        lookup_expr='in'
    )
    
    # Комплексный поиск
    search = django_filters.CharFilter(
        method='filter_search'
    )

    has_publications = django_filters.BooleanFilter(
        method='filter_has_publications'
    )
    
    class Meta:
        model = AIModule
        fields = [
            'status', 'country',
        ]

    def filter_min_likes(self, queryset, name, value):
        """Фильтр по минимальному количеству лайков"""
        return queryset.annotate(
            likes_count=Count('likes')
        ).filter(likes_count__gte=value)
    
    def filter_search(self, queryset, name, value):
        """Комплексный поиск по всем текстовым полям"""
        if value:
            return queryset.filter(
                Q(name__icontains=value) |
                Q(company__icontains=value) |
                Q(task_short_description__icontains=value) |
                Q(details__description__icontains=value) |
                Q(details__technical_info__icontains=value) |
                Q(aimoduletag__tag__name__icontains=value)
            ).distinct()
        return queryset
    
    def filter_my_modules(self, queryset, name, value):
        """Фильтр только моих модулей"""
        if value and self.request.user.is_authenticated:
            return queryset.filter(created_by=self.request.user)
        return queryset
    
    def filter_has_publications(self, queryset, name, value):
        """Фильтр по наличию публикаций"""
        if value is True:
            return queryset.filter(publications__isnull=False).distinct()
        elif value is False:
            return queryset.filter(publications__isnull=True)
        return queryset

class TagFilter(django_filters.FilterSet):
    """Фильтры для тегов"""
    
    name = django_filters.CharFilter(lookup_expr='icontains')
    category_name = django_filters.CharFilter(
        field_name='category__name',
        lookup_expr='icontains'
    )
    
    # Фильтр по популярности
    min_usage = django_filters.NumberFilter(
        method='filter_min_usage'
    )
    
    class Meta:
        model = Tag
        fields = ['category', 'is_active']
    
    def filter_min_usage(self, queryset, name, value):
        """Фильтр по минимальному использованию"""
        return queryset.annotate(
            usage_count=Count('aimoduletag')
        ).filter(usage_count__gte=value)

class PublicationFilter(django_filters.FilterSet):
    """Фильтры для публикаций"""
    
    title = django_filters.CharFilter(lookup_expr='icontains')
    authors = django_filters.CharFilter(lookup_expr='icontains')
    journal_conference = django_filters.CharFilter(lookup_expr='icontains')
    
    # Временные фильтры
    published_after = django_filters.DateFilter(
        field_name='publication_date',
        lookup_expr='gte'
    )
    published_before = django_filters.DateFilter(
        field_name='publication_date',
        lookup_expr='lte'
    )
    published_year = django_filters.NumberFilter(
        field_name='publication_date__year'
    )
    
    # Фильтр по модулю
    ai_module_name = django_filters.CharFilter(
        field_name='ai_module__name',
        lookup_expr='icontains'
    )
    
  
    
    class Meta:
        model = Publication
        fields = ['ai_module', 'authors',]

class UserFilter(django_filters.FilterSet):
    """Фильтры для пользователей"""
    
    username = django_filters.CharFilter(lookup_expr='icontains')
    organization = django_filters.CharFilter(lookup_expr='icontains')
    
    # Фильтр по активности
    has_modules = django_filters.BooleanFilter(
        method='filter_has_modules'
    )
    
    class Meta:
        model = User
        fields = ['role', 'country', 'is_active']
    
    def filter_has_modules(self, queryset, name, value):
        """Фильтр пользователей с модулями"""
        if value is True:
            return queryset.filter(ai_modules__isnull=False).distinct()
        elif value is False:
            return queryset.filter(ai_modules__isnull=True)
        return queryset

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.ai_modules.models import AIModule, AIModuleDetail, AIModuleLike, AIModuleFile
from apps.tags.models import Tag, TagCategory, AIModuleTag
from apps.publications.models import Publication
from apps.accounts.models import UserProfile
from apps.common.models import Country

User = get_user_model()

class DynamicFieldsMixin:
    """Миксин для динамического выбора полей в сериализаторе"""
    
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        exclude = kwargs.pop('exclude', None)
        
        super().__init__(*args, **kwargs)
        
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
        
        if exclude is not None:
            for field_name in exclude:
                self.fields.pop(field_name, None)

class CountrySerializer(serializers.ModelSerializer):
    """Сериализатор для стран"""
    
    class Meta:
        model = Country
        fields = ['id', 'name', 'code', 'is_brics_member', 'flag_emoji']

class UserProfileSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""
    
    avatar_url = serializers.SerializerMethodField()
    expertise_list = serializers.SerializerMethodField()
    modules_count = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email',
            'organization', 'country', 'role', 'created_at',
            'avatar_url', 'expertise_list', 'modules_count', 'total_likes'
        ]
        read_only_fields = ['id', 'created_at', 'role']
    
    def get_avatar_url(self, obj):
        if hasattr(obj, 'profile') and obj.profile.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.profile.avatar.url)
        return None
    
    def get_expertise_list(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.get_expertise_list()
        return []
    
    def get_modules_count(self, obj):
        return obj.ai_modules.filter(status=AIModule.Status.ACTIVE).count()
    
    def get_total_likes(self, obj):
        return AIModuleLike.objects.filter(ai_module__created_by=obj).count()

class TagSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Сериализатор для тегов"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    usage_count = serializers.SerializerMethodField()
    color_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Tag
        fields = [
            'id', 'name', 'slug', 'description', 'color', 'color_display',
            'category_name', 'usage_count', 'is_active'
        ]
    
    def get_usage_count(self, obj):
        if hasattr(obj, 'usage_count'):
            return obj.usage_count
        return obj.aimoduletag_set.count()
    
    def get_color_display(self, obj):
        return obj.get_color_or_default()

class TagCategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий тегов"""
    
    tags = TagSerializer(many=True, read_only=True, fields=['id', 'name', 'color_display'])
    tags_count = serializers.SerializerMethodField()
    
    class Meta:
        model = TagCategory
        fields = ['id', 'name', 'slug', 'description', 'order', 'tags', 'tags_count']
    
    def get_tags_count(self, obj):
        return obj.tags.filter(is_active=True).count()

class PublicationSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Сериализатор для публикаций"""
    
    authors_list = serializers.SerializerMethodField()
    citation_url = serializers.SerializerMethodField()
    formatted_citation = serializers.SerializerMethodField()
    ai_module_name = serializers.CharField(source='ai_module.name', read_only=True)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'authors', 'authors_list', 'journal_conference',
            'publication_date', 'doi', 'url', 'abstract', 'keywords',
            'citation_count', 'citation_url', 
            'formatted_citation', 'ai_module_name', 'created_at'
        ]
    
    def get_authors_list(self, obj):
        return obj.get_authors_list()
    
    def get_citation_url(self, obj):
        return obj.get_citation_url()
    
    def get_formatted_citation(self, obj):
        return obj.format_citation()

class AIModuleFileSerializer(serializers.ModelSerializer):
    """Сериализатор для файлов модулей"""
    
    file_url = serializers.SerializerMethodField()
    file_size_display = serializers.SerializerMethodField()
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)
    
    class Meta:
        model = AIModuleFile
        fields = [
            'id', 'name', 'file', 'file_url', 'file_type', 'description',
            'size', 'file_size_display', 'uploaded_by_name', 'uploaded_at'
        ]
        read_only_fields = ['id', 'size', 'uploaded_by_name', 'uploaded_at']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
        return None
    
    def get_file_size_display(self, obj):
        return obj.get_file_size_display()

class AIModuleDetailSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Сериализатор для детальной информации модуля"""
    
    metrics_display = serializers.SerializerMethodField()
    supported_languages_display = serializers.SerializerMethodField()
    
    class Meta:
        model = AIModuleDetail
        fields = [
            'description', 'technical_info', 'architecture',
            'training_data_description', 'metrics', 'metrics_display',
            'supported_languages', 'supported_languages_display',
            'requirements', 'installation_guide',
        ]
    
    def get_metrics_display(self, obj):
        return obj.get_metrics_display()
    
    def get_supported_languages_display(self, obj):
        return obj.get_supported_languages_list()

class AIModuleTagSerializer(serializers.ModelSerializer):
    """Сериализатор для связей модуль-тег"""
    
    tag = TagSerializer(read_only=True, fields=['id', 'name', 'color_display', 'category_name'])
    tag_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = AIModuleTag
        fields = ['id', 'tag', 'tag_id', 'confidence', 'assigned_at']
        read_only_fields = ['id', 'assigned_at']

class AIModuleListSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Сериализатор для списка модулей (краткий)"""
    
    created_by = UserProfileSerializer(
        read_only=True, 
        fields=['id', 'username', 'first_name', 'last_name', 'organization']
    )
    tags = TagSerializer(
        source='get_tags', 
        many=True, 
        read_only=True,
        fields=['id', 'name', 'color_display', 'category_name']
    )
    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = AIModule
        fields = [
            'id', 'name', 'slug', 'company', 'country', 'params_count',
            'task_short_description', 'status', 'status_display', 'version', 
            'license_type', 'created_by', 'created_at', 'updated_at',
            'published_at', 'tags', 'like_count', 'is_liked'
        ]
    
    def get_like_count(self, obj):
        if hasattr(obj, 'like_count'):
            return obj.like_count
        return obj.likes.count()
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_liked_by(request.user)
        return False

class AIModuleDetailFullSerializer(AIModuleListSerializer):
    """Полный сериализатор модуля для детального просмотра"""
    
    details = AIModuleDetailSerializer(read_only=True)
    publications = PublicationSerializer(many=True, read_only=True)
    files = AIModuleFileSerializer(many=True, read_only=True)
    tags_by_category = serializers.SerializerMethodField()
    
    class Meta(AIModuleListSerializer.Meta):
        fields = AIModuleListSerializer.Meta.fields + [
            'meta_description', 'details', 'publications', 'files', 'tags_by_category'
        ]
    
    def get_tags_by_category(self, obj):
        """Группировка тегов по категориям"""
        tags_dict = {}
        for amt in obj.aimoduletag_set.select_related('tag__category'):
            category_name = amt.tag.category.name
            if category_name not in tags_dict:
                tags_dict[category_name] = []
            tags_dict[category_name].append({
                'id': amt.tag.id,
                'name': amt.tag.name,
                'color': amt.tag.get_color_or_default(),
                'confidence': amt.confidence
            })
        return tags_dict

class AIModuleCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания модуля"""
    
    # Детальная информация встроенная
    details = AIModuleDetailSerializer(required=False, allow_null=True)
    
    # Теги как список ID
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        allow_empty=True
    )
    
    # Публикации встроенные
    publications = PublicationSerializer(many=True, required=False, allow_empty=True)
    
    class Meta:
        model = AIModule
        fields = [
            'name', 'company', 'country', 'params_count',
            'task_short_description', 'version', 'license_type',
            'meta_description', 'details', 'tag_ids', 'publications'
        ]
    
    def validate_tag_ids(self, value):
        """Валидация тегов"""
        if value:
            existing_tags = Tag.objects.filter(
                id__in=value, 
                is_active=True
            ).count()
            if existing_tags != len(value):
                raise serializers.ValidationError(
                    "Some tags do not exist or are inactive"
                )
        return value
    
    def validate_params_count(self, value):
        """Валидация количества параметров"""
        if value <= 0:
            raise serializers.ValidationError(
                "Parameters count must be greater than 0"
            )
        return value
    
    def validate(self, attrs):
        """Комплексная валидация"""
        # Проверяем соответствие тегов требованиям категорий
        tag_ids = attrs.get('tag_ids', [])
        if tag_ids:
            tags = Tag.objects.filter(id__in=tag_ids).select_related('category')
            
            # Группируем по категориям
            category_tags = {}
            for tag in tags:
                category = tag.category
                if category.id not in category_tags:
                    category_tags[category.id] = {
                        'category': category,
                        'tags': []
                    }
                category_tags[category.id]['tags'].append(tag)
            
            # Проверяем ограничения категорий
            for cat_id, data in category_tags.items():
                category = data['category']
                tag_count = len(data['tags'])
                
                if tag_count < category.min_tags:
                    raise serializers.ValidationError(
                        f"Category '{category.name}' requires at least {category.min_tags} tags"
                    )
                
                if tag_count > category.max_tags:
                    raise serializers.ValidationError(
                        f"Category '{category.name}' allows maximum {category.max_tags} tags"
                    )
        
        return attrs
    
    def create(self, validated_data):
        """Создание модуля с вложенными объектами"""
        details_data = validated_data.pop('details', None)
        tag_ids = validated_data.pop('tag_ids', [])
        publications_data = validated_data.pop('publications', [])
        
        # Создаем модуль
        ai_module = AIModule.objects.create(**validated_data)
        
        # Создаем детальную информацию
        if details_data:
            AIModuleDetail.objects.create(
                ai_module=ai_module,
                **details_data
            )
        
        # Назначаем теги
        for tag_id in tag_ids:
            try:
                tag = Tag.objects.get(id=tag_id, is_active=True)
                AIModuleTag.objects.create(
                    ai_module=ai_module,
                    tag=tag,
                    assigned_by=self.context['request'].user
                )
            except Tag.DoesNotExist:
                pass  # Тег уже проверен в валидации
        
        # Создаем публикации
        for pub_data in publications_data:
            Publication.objects.create(
                ai_module=ai_module,
                added_by=self.context['request'].user,
                **pub_data
            )
        
        return ai_module

class AIModuleUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления модуля"""
    
    details = AIModuleDetailSerializer(required=False)
    tag_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = AIModule
        fields = [
            'name', 'company', 'country', 'params_count',
            'task_short_description', 'version', 'license_type',
            'meta_description', 'details', 'tag_ids'
        ]
    
    def update(self, instance, validated_data):
        """Обновление модуля с вложенными объектами"""
        details_data = validated_data.pop('details', None)
        tag_ids = validated_data.pop('tag_ids', None)
        
        # Обновляем основные поля
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Обновляем детальную информацию
        if details_data is not None:
            if hasattr(instance, 'details'):
                for attr, value in details_data.items():
                    setattr(instance.details, attr, value)
                instance.details.save()
            else:
                AIModuleDetail.objects.create(
                    ai_module=instance,
                    **details_data
                )
        
        # Обновляем теги
        if tag_ids is not None:
            # Удаляем старые связи
            instance.aimoduletag_set.all().delete()
            
            # Создаем новые
            for tag_id in tag_ids:
                try:
                    tag = Tag.objects.get(id=tag_id, is_active=True)
                    AIModuleTag.objects.create(
                        ai_module=instance,
                        tag=tag,
                        assigned_by=self.context['request'].user
                    )
                except Tag.DoesNotExist:
                    pass
        
        return instance

# Специальные сериализаторы для статистики
class ModuleStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики модулей"""
    
    total_modules = serializers.IntegerField()
    by_country = serializers.DictField()
    by_status = serializers.DictField()
    total_likes = serializers.IntegerField()
    most_liked = AIModuleListSerializer(many=True)

class UserStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики пользователя"""
    
    total_modules = serializers.IntegerField()
    total_likes_received = serializers.IntegerField()
    total_publications = serializers.IntegerField()
    member_since = serializers.DateTimeField()

# Сериализаторы для экспорта
class AIModuleExportSerializer(serializers.ModelSerializer):
    """Сериализатор для экспорта модулей"""
    
    created_by_name = serializers.CharField(source='created_by.username')
    tags_list = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display')
    
    class Meta:
        model = AIModule
        fields = [
            'id', 'name', 'company', 'country', 'params_count',
            'task_short_description', 'status', 'status_display',
            'version', 'license_type', 'created_by_name', 'created_at',
            'tags_list'
        ]
    
    def get_tags_list(self, obj):
        return ', '.join([tag.name for tag in obj.get_tags()])

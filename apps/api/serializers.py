from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.ai_modules.models import AIModule, AIModuleDetail, AIModuleLike, AIModuleFile
from apps.tags.models import Tag, TagCategory, AIModuleTag
from apps.publications.models import Publication
from apps.accounts.models import UserProfile
from apps.common.models import Country
from transliterate import translit

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
        fields = ['id', 'name', 'name_ru', 'code', 'is_brics_member', 'flag_emoji']

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
            'id', 'name', 'name_ru', 'slug', 'description', 'color', 'color_display',
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
        fields = ['id', 'name','name_ru', 'slug', 'description', 'order', 'tags', 'tags_count']
    
    def get_tags_count(self, obj):
        return obj.tags.filter(is_active=True).count()

class PublicationSerializer(DynamicFieldsMixin, serializers.ModelSerializer):
    """Сериализатор для публикаций"""
  
    ai_module_name = serializers.CharField(source='ai_module.name', read_only=True)
    
    class Meta:
        model = Publication
        fields = [
            'id', 'title', 'authors', 'journal_conference',
            'publication_date', 'doi', 'url',
            'ai_module_name', 'created_at'
        ]
    
   

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
        
    class Meta:
        model = AIModuleDetail
        fields = [
            'description', 'technical_info', 'status',
            'registration_system', 'registration_number', 'ability'
        ]

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
        fields=['username', 'first_name', 'last_name', 'organization']
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
            'details', 'publications', 'files', 'tags_by_category'
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
             'details', 'tag_ids', 'publications'
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
            'details', 'tag_ids'
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
            'id', 'name','name_ru', 'company', 'country', 'params_count',
            'task_short_description', 'status', 'status_display',
            'version', 'license_type', 'created_by_name', 'created_at',
            'tags_list'
        ]
    
    def get_tags_list(self, obj):
        return ', '.join([tag.name for tag in obj.get_tags()])






###############




class EstimatorAvailabilitySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    name_ru = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class EstimatorGenericStatusSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    name_ru = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class PublicationForEstimatorSerializer(serializers.ModelSerializer):
    journal_or_conference = serializers.CharField(source='journal_conference', allow_blank=True, required=False)
    publication_year = serializers.SerializerMethodField()
    abstract = serializers.SerializerMethodField()

    class Meta:
        model = Publication
        fields = ('id', 'title', 'authors', 'abstract', 'journal_or_conference',
                  'publication_year', 'doi', 'url', 'created_at', 'updated_at')

    def get_publication_year(self, obj):
        if obj.publication_date:
            return str(obj.publication_date.year)
        return None

    def get_abstract(self, obj):
        return getattr(obj, 'abstract', '') or ''


class SimpleTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'name_ru', 'created_at', 'updated_at')


class EstimatorSerializer(serializers.ModelSerializer):
    # owner
    owner = serializers.SerializerMethodField()

    # страны (синтезируем из строки ai_module.country)
    developer_country = serializers.SerializerMethodField()
    application_country = serializers.SerializerMethodField()

    # одиночные объекты (не null, но могут быть пустыми объектами)
    availability = serializers.SerializerMethodField()
    usage_status = serializers.SerializerMethodField()

    # массивы тегов по категориям
    tasks = serializers.SerializerMethodField()
    anatomical_areas = serializers.SerializerMethodField()
    technologies = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()

    # публикации
    scientific_papers = PublicationForEstimatorSerializer(source='publications', many=True, read_only=True)

    # простые маппинги
    title = serializers.CharField(source='name', read_only=True)
    developer_company = serializers.CharField(source='company', read_only=True)
    parameter_count = serializers.IntegerField(source='params_count', read_only=True)
    key_characteristics = serializers.SerializerMethodField()

    class Meta:
        model = AIModule
        fields = (
            'id',
            'owner',
            'developer_country',
            'application_country',
            'availability',
            'usage_status',
            'tasks',
            'anatomical_areas',
            'technologies',
            'scientific_papers',
            'languages',
            'created_at',
            'updated_at',
            'title',
            'developer_company',
            'parameter_count',
            'task_short_description',
            'key_characteristics',
        )

    def get_owner(self, obj):
        u = getattr(obj, 'created_by', None)
        if not u:
            return {
                'id': 0,
                'username': '',
                'email': '',
                'first_name': '',
                'last_name': '',
                'is_staff': False,
                'is_active': False,
                'date_joined': obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
            }
        return {
            'id': u.id,
            'username': u.username or '',
            'email': getattr(u, 'email', '') or '',
            'first_name': getattr(u, 'first_name', '') or '',
            'last_name': getattr(u, 'last_name', '') or '',
            'is_staff': getattr(u, 'is_staff', False),
            'is_active': getattr(u, 'is_active', True),
            'date_joined': getattr(u, 'date_joined', obj.created_at).isoformat() if hasattr(getattr(u, 'date_joined', obj.created_at), 'isoformat') else str(getattr(u, 'date_joined', obj.created_at)),
        }

    def get_developer_country(self, obj):
        return {
            'id': obj.country.id,
            'name': obj.country.name,
            'name_ru': obj.country.name_ru,
            'created_at': obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
            'updated_at': obj.updated_at.isoformat() if hasattr(obj.updated_at, 'isoformat') else str(obj.updated_at),
            'code': obj.country.code,
        }

    def get_application_country(self, obj):
        return {
            'id': obj.country.id,
            'name': obj.country.name,
            'name_ru': obj.country.name_ru,
            'created_at': obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
            'updated_at': obj.updated_at.isoformat() if hasattr(obj.updated_at, 'isoformat') else str(obj.updated_at),
            'code': obj.country.code,
        }

        # return synth_country_from_str(country_str, obj.created_at, obj.updated_at) or {
        #     'id': 0,
        #     'name': '',
        #     'name_ru': '',
        #     'created_at': obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
        #     'updated_at': obj.updated_at.isoformat() if hasattr(obj.updated_at, 'isoformat') else str(obj.updated_at),
        #     'code': '',
        # }

    def _first_or_none(self, qs):
        item = qs.first()
        if not item:
            return None
        return SimpleTagSerializer(item).data

    def _tags_by_cat(self, obj, names: list[str]):
        from django.db.models import Q
        return Tag.objects.filter(
            aimoduletag__ai_module=obj, is_active=True
        ).filter(
            Q(category__name__in=names) | Q(category__name_ru__in=names)
        ).order_by('name')

    def get_availability(self, obj):
        # Берём первый тег из категории Доступности, отдаём как одиночный объект
        tag = self._first_or_none(self._tags_by_cat(obj, ['Availability Status', 'Доступность', 'Статусы доступности']))
        if tag:
            return tag
        # Фоллбек: из details.ability
        details = getattr(obj, 'details', None)
        name_ru = getattr(details, 'ability', None) if details else None
        if not name_ru:
            return {
                'id': 0,
                'name': '',
                'name_ru': '',
                'created_at': obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
                'updated_at': obj.updated_at.isoformat() if hasattr(obj.updated_at, 'isoformat') else str(obj.updated_at),
            }
        try:
            name_en = translit(name_ru, 'ru', reversed=True)
        except Exception:
            name_en = name_ru
        return {
            'id': 0,
            'name': name_en,
            'name_ru': name_ru,
            'created_at': obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
            'updated_at': obj.updated_at.isoformat() if hasattr(obj.updated_at, 'isoformat') else str(obj.updated_at),
        }

    def get_usage_status(self, obj):
        # Если есть теговая категория статусов — берём 1-й тег
        tag = self._first_or_none(self._tags_by_cat(obj, ['Statuses', 'Статусы', 'Generic Status']))
        if tag:
            return tag
        # Фоллбек: из details.status или поля obj.status
        details = getattr(obj, 'details', None)
        status_ru = (getattr(details, 'status', None) if details else None) or getattr(obj, 'status', None)
        if not status_ru:
            return {
                'id': 0,
                'name': '',
                'name_ru': '',
                'created_at': obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
                'updated_at': obj.updated_at.isoformat() if hasattr(obj.updated_at, 'isoformat') else str(obj.updated_at),
            }
        try:
            status_en = translit(str(status_ru), 'ru', reversed=True)
        except Exception:
            status_en = str(status_ru)
        return {
            'id': 0,
            'name': status_en,
            'name_ru': str(status_ru),
            'created_at': obj.created_at.isoformat() if hasattr(obj.created_at, 'isoformat') else str(obj.created_at),
            'updated_at': obj.updated_at.isoformat() if hasattr(obj.updated_at, 'isoformat') else str(obj.updated_at),
        }

    def get_tasks(self, obj):
        return SimpleTagSerializer(self._tags_by_cat(obj, ['Tasks', 'Задачи']), many=True).data or []

    def get_anatomical_areas(self, obj):
        return SimpleTagSerializer(self._tags_by_cat(obj, ['Anatomical Areas', 'Анатомические области']), many=True).data or []

    def get_technologies(self, obj):
        return SimpleTagSerializer(self._tags_by_cat(obj, ['Technologies', 'Технологии', 'Тип технологии']), many=True).data or []

    def get_languages(self, obj):
        return SimpleTagSerializer(self._tags_by_cat(obj, ['Languages', 'Языки']), many=True).data or []

    def get_key_characteristics(self, obj):
        details = getattr(obj, 'details', None)
        for f in ('technical_info', 'description'):
            v = getattr(details, f, None) if details else None
            if v:
                return v
        return ''
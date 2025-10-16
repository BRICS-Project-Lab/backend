from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils.text import slugify

User = get_user_model()

class AIModule(models.Model):
    """Основная модель для ИИ-сервиса"""
    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        if getattr(user, 'is_admin', None) and user.is_admin():
            return True
        return self.created_by_id == user.id

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ON_REVIEW = 'on_review', _('On Review')
        ACTIVE = 'active', _('Active')
        REJECTED = 'rejected', _('Rejected')
        BLOCKED = 'blocked', _('Blocked')
    
    # Основные поля
    name = models.CharField(max_length=255, verbose_name=_('Name'))
    slug = models.SlugField(max_length=255, unique=True)
    company = models.CharField(max_length=255, verbose_name=_('Company'))
    country = models.CharField(max_length=100, verbose_name=_('Country'))
    params_count = models.BigIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Parameters Count')
    )
    task_short_description = models.TextField(
        max_length=500,
        verbose_name=_('Short Description')
    )
    
    # Статус и модерация
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('Status')
    )
    
    # Связи
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_modules',
        verbose_name=_('Created by')
    )
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Published At')
    )
    
    # SEO и поиск
    meta_description = models.TextField(max_length=300, blank=True)
    search_vector = models.TextField(blank=True)  # Для полнотекстового поиска
    
    version = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Version')
    )

    license_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('License Type'),
        help_text=_('Type of license, e.g., MIT, Apache 2.0')
    )

    class Meta:
        verbose_name = _('AI Module')
        verbose_name_plural = _('AI Modules')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['country']),
            models.Index(fields=['slug']),
        ]
    
    def is_liked_by(self, user):
        if not getattr(user, 'is_authenticated', False):
            return False
        return self.likes.filter(user_id=user.id).exists()

    def __str__(self):
        return f"{self.name} ({self.company})"

    def _generate_unique_slug(self):
        base = slugify(self.name or '')
        slug = base or 'module'
        qs = AIModule.objects.exclude(pk=self.pk)
        i = 1
        unique = slug
        while qs.filter(slug=unique).exists():
            i += 1
            unique = f'{slug}-{i}'
        return unique

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._generate_unique_slug()
        super().save(*args, **kwargs)

class AIModuleDetail(models.Model):
    """Детальная информация о модели"""
    ai_module = models.OneToOneField(
        AIModule,
        on_delete=models.CASCADE,
        related_name='details'
    )
    
    # Описание
    description = models.TextField(verbose_name=_('Description'))
    technical_info = models.TextField(verbose_name=_('Technical Information'))
    
    # Архитектурные детали
    architecture = models.TextField(blank=True, verbose_name=_('Architecture'))
    training_data_description = models.TextField(
        blank=True,
        verbose_name=_('Training Data Description')
    )
    metrics = models.JSONField(default=dict, blank=True, verbose_name=_('Metrics'))
    
    # Дополнительные поля
    supported_languages = models.JSONField(default=list, blank=True)
    requirements = models.TextField(blank=True, verbose_name=_('System Requirements'))
    
    installation_guide = models.TextField(
        blank=True,
        verbose_name=_('Installation Guide')
    )
    class Meta:
        verbose_name = _('AI Module Details')
        verbose_name_plural = _('AI Module Details')

class AIModuleLike(models.Model):
    """Система лайков для моделей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ai_module = models.ForeignKey(AIModule, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'ai_module')
        verbose_name = _('AI Module Like')
        verbose_name_plural = _('AI Module Likes')



class AIModuleFile(models.Model):
    """Файлы, связанные с ИИ-модулем"""
    
    class FileType(models.TextChoices):
        DOCUMENTATION = 'doc', _('Documentation')
        MODEL_FILE = 'model', _('Model File')
        DATASET = 'dataset', _('Dataset')
        CODE = 'code', _('Code')
        OTHER = 'other', _('Other')
    
    ai_module = models.ForeignKey(
        AIModule,
        on_delete=models.CASCADE,
        related_name='files'
    )
    name = models.CharField(max_length=255, verbose_name=_('File Name'))
    file = models.FileField(
        upload_to='ai_modules/files/%Y/%m/',
        verbose_name=_('File')
    )
    file_type = models.CharField(
        max_length=10,
        choices=FileType.choices,
        default=FileType.OTHER,
        verbose_name=_('File Type')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description')
    )
    size = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('File Size (bytes)')
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Uploaded by')
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = _('AI Module File')
        verbose_name_plural = _('AI Module Files')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['ai_module', 'file_type']),
        ]
    
    def get_file_type_display(self):
        return dict(self.FileType.choices).get(self.file_type, self.file_type)
    
    def __str__(self):
        return f"{self.name} ({self.get_file_type_display()}) {self. get_file_size_display()}"
    
    def save(self, *args, **kwargs):
        if self.file and not self.size:
            self.size = self.file.size
        super().save(*args, **kwargs)
    
    def get_file_size_display(self):
        """Человекочитаемый размер файла"""
        if self.size:
            if self.size < 1024:
                return f"{self.size} B"
            elif self.size < 1024 * 1024:
                return f"{self.size / 1024:.1f} KB"
            elif self.size < 1024 * 1024 * 1024:
                return f"{self.size / (1024 * 1024):.1f} MB"
            else:
                return f"{self.size / (1024 * 1024 * 1024):.1f} GB"
        return _('Unknown size')
    
    def delete(self, *args, **kwargs):
        # Удаляем файл с диска при удалении записи
        if self.file:
            self.file.delete(save=False)
        super().delete(*args, **kwargs)
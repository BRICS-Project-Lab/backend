from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class TagCategory(models.Model):
    """Категории тегов"""
    
    name = models.CharField(max_length=1024, unique=True, verbose_name=_('Name'))
    slug = models.SlugField(max_length=1024, unique=True)
    description = models.TextField(blank=True, verbose_name=_('Description'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    
    class Meta:
        verbose_name = _('Tag Category')
        verbose_name_plural = _('Tag Categories')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Tag(models.Model):
    """Теги для ИИ-моделей"""
    
    category = models.ForeignKey(
        TagCategory,
        on_delete=models.CASCADE,
        related_name='tags'
    )
    name = models.CharField(max_length=1024, verbose_name=_('Name'))
    slug = models.SlugField(max_length=1024)
    description = models.TextField(blank=True, verbose_name=_('Description'))
    color = models.CharField(max_length=7, blank=True, verbose_name=_('Color'))  # HEX цвет
    
    # Модерация
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Created by')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_tags',
        verbose_name=_('Approved by')
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Tags')
        unique_together = ('category', 'slug')
        ordering = ['category', 'name']
        indexes = [
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['slug']),
        ]
    
    def get_color_or_default(self):
        return self.color or '#999999'
    def __str__(self):
        return f"{self.category.name}: {self.name}"

class AIModuleTag(models.Model):
    """Связь между ИИ-модулями и тегами"""
    
    ai_module = models.ForeignKey(
        'ai_modules.AIModule',
        on_delete=models.CASCADE
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)
    
    # Метаинформация
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Assigned by')
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('ai_module', 'tag')
        verbose_name = _('AI Module Tag')
        verbose_name_plural = _('AI Module Tags')
        indexes = [
            models.Index(fields=['ai_module', 'tag']),
        ]

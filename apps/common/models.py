from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class AuditLog(models.Model):
    """Журнал аудита всех действий в системе"""
    
    class Action(models.TextChoices):
        CREATE = 'create', _('Created')
        UPDATE = 'update', _('Updated')
        DELETE = 'delete', _('Deleted')
        APPROVE = 'approve', _('Approved')
        REJECT = 'reject', _('Rejected')
        BLOCK = 'block', _('Blocked')
        UNBLOCK = 'unblock', _('Unblocked')
    
    # Полиморфная связь с любым объектом
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Информация о действии
    action = models.CharField(max_length=20, choices=Action.choices)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Дополнительная информация
    comment = models.TextField(blank=True, verbose_name=_('Comment'))
    old_values = models.JSONField(default=dict, blank=True)  # Старые значения
    new_values = models.JSONField(default=dict, blank=True)  # Новые значения
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['performed_by', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

class Country(models.Model):
    """Справочник стран БРИКС"""
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=3, unique=True)  # BRA, RUS, IND, CHN, ZAF
    is_brics_member = models.BooleanField(default=True)
    flag_emoji = models.CharField(max_length=10, blank=True)
    
    class Meta:
        verbose_name = _('Country')
        verbose_name_plural = _('Countries')
        ordering = ['name']
    
    def __str__(self):
        return self.name

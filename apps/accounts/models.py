from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    """Расширенная модель пользователя"""
    
    class Role(models.TextChoices):
        GUEST = 'guest', _('Guest')
        USER = 'user', _('User') 
        ADMIN = 'admin', _('Administrator')
    
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
        verbose_name=_('Role')
    )
    
    # Дополнительные поля
    organization = models.CharField(max_length=255, blank=True, verbose_name=_('Organization'))
    country = models.CharField(max_length=100, blank=True, verbose_name=_('Country'))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_('Phone'))
    is_blocked = models.BooleanField(default=False, verbose_name=_('Is blocked'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class UserProfile(models.Model):
    """Профиль пользователя с дополнительной информацией"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, verbose_name=_('Biography'))
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    expertise_areas = models.TextField(blank=True, verbose_name=_('Expertise Areas'))
    
    class Meta:
        verbose_name = _('User Profile')
        verbose_name_plural = _('User Profiles')

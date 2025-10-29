from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

class Publication(models.Model):
    """Научная публикация, связанная с ИИ-моделью"""
    
    ai_module = models.ForeignKey(
        'ai_modules.AIModule',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='publications',
        verbose_name=_('AI Module')
    )
    
    title = models.CharField(max_length=500, verbose_name=_('Title'))
    authors = models.TextField(verbose_name=_('Authors'), blank=True)  # JSON или простой текст
    journal_conference = models.CharField(
        max_length=255,
        verbose_name=_('Journal/Conference'),
        blank=True
    )
    publication_date = models.DateField(verbose_name=_('Publication Date'), blank=True)
    doi = models.CharField(max_length=100, blank=True, verbose_name=_('DOI'))
    url = models.URLField(blank=True, verbose_name=_('URL'))
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='publications',
        verbose_name=_('Added by')
    )
    class Meta:
        verbose_name = _('Publication')
        verbose_name_plural = _('Publications')
        ordering = ['-publication_date']
        indexes = [
            models.Index(fields=['publication_date']),
            models.Index(fields=['doi']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.publication_date.year})"

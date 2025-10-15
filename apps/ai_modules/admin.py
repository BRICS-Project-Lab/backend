from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from .models import AIModule, AIModuleDetail, AIModuleLike

@admin.register(AIModule)
class AIModuleAdmin(ImportExportModelAdmin):
    list_display = ['name', 'company', 'country', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'country', 'created_at']
    search_fields = ['name', 'company', 'task_short_description']
    readonly_fields = ['created_at', 'updated_at', 'slug']
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'company', 'country', 'params_count')
        }),
        (_('Description'), {
            'fields': ('task_short_description', 'meta_description')
        }),
        (_('Status'), {
            'fields': ('status', 'created_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

class AIModuleDetailInline(admin.StackedInline):
    model = AIModuleDetail
    extra = 0

# Обновление админки с инлайнами
AIModuleAdmin.inlines = [AIModuleDetailInline]

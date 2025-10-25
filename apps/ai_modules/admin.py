from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import path
from django.http import HttpResponseRedirect
from .models import AIModule, AIModuleDetail, AIModuleLike, AIModuleFile
from apps.publications.models import Publication
from import_export.admin import ImportExportModelAdmin
from apps.publications.models import Publication
from apps.tags.models import AIModuleTag
import os


class AIModuleDetailInline(admin.StackedInline):
    model = AIModuleDetail
    extra = 0

class AIModuleFileInline(admin.TabularInline):
    model = AIModuleFile
    extra = 0
    fields = ('name', 'file', 'file_type', 'size', 'uploaded_by', 'uploaded_at')
    readonly_fields = ('size', 'uploaded_at')

class PublicationInline(admin.TabularInline):
    model = Publication
    extra = 0
    fields = ('title', 'journal_conference', 'publication_date', 'doi',)
    show_change_link = True

class AIModuleTagInline(admin.TabularInline):
    model = AIModuleTag
    extra = 0
    autocomplete_fields = ('tag',)


@admin.register(AIModule)
class AIModuleAdmin(admin.ModelAdmin):  # Убрали ImportExportModelAdmin
    list_display = ('name', 'company', 'country', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'country', 'created_at')
    search_fields = ('name', 'company', 'task_short_description', 'slug')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('created_by',)
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'company', 'country', 'params_count')
        }),
        (_('Description'), {
            'fields': ('task_short_description',)
        }),
        (_('Status'), {
            'fields': ('status', 'created_by')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    inlines = [AIModuleDetailInline, AIModuleFileInline, PublicationInline, AIModuleTagInline]

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj:  # change view
            ro.append('slug')
        return ro

    def get_prepopulated_fields(self, request, obj=None):
        if obj:
            return {}
        return super().get_prepopulated_fields(request, obj)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv_view), name='ai_modules_aimodule_import_csv'),
        ]
        return custom_urls + urls

    def import_csv_view(self, request):
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            if csv_file:
                # Сохраняем файл временно
                import tempfile
                with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.csv') as tmp_file:
                    for chunk in csv_file.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name
                
                try:
                    # Запускаем импорт через нашу команду
                    from django.core.management import call_command
                    call_command('import_ai_modules', tmp_file_path)
                    messages.success(request, 'Импорт успешно завершен!')
                except Exception as e:
                    messages.error(request, f'Ошибка импорта: {str(e)}')
                finally:
                    # Удаляем временный файл
                    os.unlink(tmp_file_path)
                
                return redirect('..')
        
        context = {
            'title': 'Импорт ИИ модулей из CSV',
            'has_permission': True,
        }
        return render(request, 'admin/ai_modules/import_csv.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = 'import-csv/'
        return super().changelist_view(request, extra_context=extra_context)


@admin.register(AIModuleLike)
class AIModuleLikeAdmin(admin.ModelAdmin):
    list_display = ('ai_module', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('ai_module__name', 'user__username')
    autocomplete_fields = ('ai_module', 'user')

@admin.register(AIModuleFile)
class AIModuleFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'ai_module', 'file_type', 'size', 'uploaded_by', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('name', 'ai_module__name', 'uploaded_by__username')
    autocomplete_fields = ('ai_module', 'uploaded_by')
    readonly_fields = ('size', 'uploaded_at')
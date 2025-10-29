from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Publication

from django.contrib import admin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from import_export.admin import ImportExportModelAdmin
from .models import Publication


@admin.register(Publication)
class PublicationAdmin(admin.ModelAdmin):
    list_display = ('title', 'ai_module', 'publication_date', 'journal_conference')
    list_filter = ('publication_date', 'journal_conference', 'ai_module')
    search_fields = ('title', 'authors', 'journal_conference', 'doi')
    autocomplete_fields = ('ai_module',)
    date_hierarchy = 'publication_date'
    readonly_fields = ('created_at', 'updated_at', 'added_by')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-publications/', self.import_publications_view, name='publications_publication_import'),
        ]
        return custom_urls + urls
    
    def import_publications_view(self, request):
        if request.method == 'POST':
            uploaded_file = request.FILES.get('csv_file')
            
            if not uploaded_file:
                messages.error(request, 'Пожалуйста, загрузите CSV файл')
                return redirect('admin:publications_publication_changelist')
            
            # Сохранить файл временно
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                # Выполнить импорт
                from django.core.management import call_command
                call_command('import_publications', tmp_file_path)
                messages.success(request, 'Публикации успешно импортированы')
            except Exception as e:
                messages.error(request, f'Ошибка импорта: {str(e)}')
            finally:
                # Удалить временный файл
                if os.path.exists(tmp_file_path):
                    os.remove(tmp_file_path)
            
            return redirect('admin:publications_publication_changelist')
        
        # GET запрос - показать форму
        from django.template.response import TemplateResponse
        context = {
            'title': 'Импорт публикаций',
            'opts': self.model._meta,
        }
        
        return TemplateResponse(request, 'admin/publications/import_publications.html', context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_import_button'] = True
        return super().changelist_view(request, extra_context)
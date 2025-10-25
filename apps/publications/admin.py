from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Publication

@admin.register(Publication)
class PublicationAdmin(ImportExportModelAdmin):
    list_display = ('title', 'ai_module', 'publication_date', 'journal_conference',)
    list_filter = ('publication_date', 'journal_conference')
    search_fields = ('title', 'authors', 'journal_conference', 'doi', 'ai_module__name')
    autocomplete_fields = ('ai_module',)
    date_hierarchy = 'publication_date'
    readonly_fields = ('created_at', 'updated_at')
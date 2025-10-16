from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from import_export.admin import ImportExportModelAdmin
from .models import AIModule, AIModuleDetail, AIModuleLike, AIModuleFile
from apps.publications.models import Publication
from apps.tags.models import AIModuleTag

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
    fields = ('title', 'journal_conference', 'publication_date', 'doi', 'citation_count')
    show_change_link = True

class AIModuleTagInline(admin.TabularInline):
    model = AIModuleTag
    extra = 0
    autocomplete_fields = ('tag',)


@admin.register(AIModule)
class AIModuleAdmin(ImportExportModelAdmin):
    list_display = ('name', 'company', 'country', 'status', 'created_by', 'created_at')
    list_filter = ('status', 'country', 'created_at')
    search_fields = ('name', 'company', 'task_short_description', 'meta_description', 'slug')
    # ВАЖНО: не включаем 'slug' в readonly_fields здесь, иначе его не будет в форме
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ('created_by',)
    date_hierarchy = 'created_at'

    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'slug', 'company', 'country', 'params_count')
        }),
        (_('Description'), {
            'fields': ('task_short_description', 'meta_description', 'search_vector')
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

    # Делаем slug только для чтения ТОЛЬКО на форме редактирования
    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj:  # change view
            ro.append('slug')
        return ro

    def get_prepopulated_fields(self, request, obj=None):
        # Отключаем автозаполнение на форме редактирования (когда slug readonly)
        if obj:
            return {}
        return super().get_prepopulated_fields(request, obj)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')


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
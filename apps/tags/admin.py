from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import TagCategory, Tag, AIModuleTag

class TagInline(admin.TabularInline):
    model = Tag
    extra = 0
    fields = ('name', 'slug', 'description', 'color', 'is_active')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(TagCategory)
class TagCategoryAdmin(ImportExportModelAdmin):
    list_display = ('name', 'slug', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'slug')
    inlines = [TagInline]
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Tag)
class TagAdmin(ImportExportModelAdmin):
    list_display = ('name', 'category', 'slug', 'is_active', 'created_by', 'approved_by', 'created_at')
    list_filter = ('is_active', 'category', 'created_at')
    search_fields = ('name', 'slug', 'description', 'category__name')
    autocomplete_fields = ('category', 'created_by', 'approved_by')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(AIModuleTag)
class AIModuleTagAdmin(admin.ModelAdmin):
    list_display = ('ai_module', 'tag', 'assigned_by', 'assigned_at')
    list_filter = ('assigned_at', 'tag__category')
    search_fields = ('ai_module__name', 'tag__name', 'assigned_by__username')
    autocomplete_fields = ('ai_module', 'tag', 'assigned_by')
    readonly_fields = ('assigned_at',)